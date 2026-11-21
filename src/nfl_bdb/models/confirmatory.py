"""Registered confirmatory procedures (Phase 4 implementation of preregistration v1.0).

Everything here operates on a play table that has, per play: player index, context index, team-season
index, covariates, and outcome; and on player-level predictor vectors (tracked peak speed x, official
40 speed F). In Phase 4 these are SYNTHETIC; the same functions will be called once on real data after
approval.

Registered elements implemented here
  H1   bivariate-context REML LMM per position -> rho_c, Delta (spec §1.1); moment estimator (§1.2);
       player-cluster percentile bootstrap (moment estimator inside the bootstrap, as allowed by §1.3);
       decision: REML Delta_hat > 0 and the (1 - alpha) bootstrap CI excludes 0 (protocol §9, §12).
  H2   REML LMM of deep-route separation on F and x (§2.1); two-stage WLS equivalent; player-cluster
       bootstrap; errors-in-variables refit (§2.3); player-grouped CV Delta R^2 with fold-internal
       residualisation (§2.2); season-forward check.
  Testing  fixed sequence H1-WR -> H2 at alpha = 0.05 (primary); Holm over {H1-WR, H1-DB, H2} (sensitivity).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import polars as pl

from nfl_bdb.models.reml import fit_reml


# ------------------------------------------------------------------------------------------------
# design matrices
# ------------------------------------------------------------------------------------------------
def one_hot(df: pl.DataFrame, covs: list[str]) -> np.ndarray:
    if not covs:
        return np.zeros((df.height, 0))
    d = df.select([pl.col(c).cast(pl.Utf8).fill_null("NA") for c in covs])
    return d.to_dummies(drop_first=True).to_numpy().astype(float)


def design_h1(df: pl.DataFrame, covs: list[str], d: int, numeric: tuple[str, ...] = ("nfl_year",)) -> np.ndarray:
    """Context-specific intercepts and context-specific covariate effects (formula 0 + ctx + ctx:(w + a))."""
    ctx = df["ctx_i"].to_numpy()
    blocks = []
    for c in range(d):
        m = (ctx == c).astype(float)
        sub = df.filter(pl.col("ctx_i") == c)
        W = one_hot(sub, [v for v in covs if v != "ctx"])
        full = np.zeros((df.height, W.shape[1]))
        full[ctx == c] = W
        num = np.column_stack([df[v].to_numpy().astype(float) * m for v in numeric]) if numeric else np.zeros((df.height, 0))
        blocks.append(np.column_stack([m, full, num]))
    X = np.column_stack(blocks)
    X = X[:, np.abs(X).sum(0) > 0]   # drop absent levels (all-zero columns)
    return full_rank(X)


def full_rank(X: np.ndarray, tol: float = 1e-8) -> np.ndarray:
    """Drop linearly dependent columns (QR with column pivoting), keeping the original column order."""
    from scipy.linalg import qr
    if X.shape[1] == 0:
        return X
    _, R, piv = qr(X, mode="economic", pivoting=True)
    dg = np.abs(np.diag(R))
    rank = int((dg > tol * dg.max()).sum())
    return X[:, np.sort(piv[:rank])]


def residualise_np(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    X1 = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    return y - X1 @ beta + y.mean()


# ------------------------------------------------------------------------------------------------
# H1
# ------------------------------------------------------------------------------------------------
@dataclass
class H1Result:
    rho: np.ndarray
    delta: float
    beta: np.ndarray
    sigma_b: np.ndarray
    s2_team: float
    converged: bool
    extra: dict = field(default_factory=dict)


def h1_reml(player, ctx, team, y, Xw, x_player, d=2, start=None) -> H1Result:
    """REML: y ~ 0 + ctx + ctx:w + ctx:x + (0 + ctx | player) + (1 | team_season), varIdent(ctx)."""
    xp = (x_player - x_player.mean()) / x_player.std(ddof=1)
    xs = xp[player]
    Xx = np.column_stack([xs * (ctx == c) for c in range(d)])
    X = np.column_stack([Xw, Xx])
    fit = fit_reml(y, X, player, ctx, team, d, start=None if start is None else dict(theta=start))
    bc = fit.beta[-d:]
    rho = bc / np.sqrt(bc ** 2 + np.diag(fit.sigma_b))   # var(x) = 1 after standardisation
    return H1Result(rho=rho, delta=float(rho[0] - rho[1]), beta=bc, sigma_b=fit.sigma_b, s2_team=fit.s2_team,
                    converged=fit.converged, extra=dict(theta=fit.theta, s2_resid=fit.s2_resid))


def h1_reml_bootstrap(player, ctx, team, y, Xw, x_player, B, rng, alpha=0.05, d=2, start=None):
    """Registered primary inference (spec §1.3): player-cluster bootstrap of the REML estimator.
    Resampled players are distinct units (new random-effect columns); team-season columns are shared.
    Warm-started from the full-data variance parameters."""
    P = len(x_player)
    order = np.argsort(player, kind="stable"); ps = player[order]
    bounds = np.searchsorted(ps, np.arange(P + 1))
    rows_of = [order[bounds[i]:bounds[i + 1]] for i in range(P)]
    deltas = np.empty(B)
    for b in range(B):
        pick = rng.integers(0, P, P)
        idx = np.concatenate([rows_of[i] for i in pick])
        newp = np.concatenate([np.full(len(rows_of[i]), k) for k, i in enumerate(pick)])
        tt = team[idx]; ut, tnew = np.unique(tt, return_inverse=True)
        Xb = Xw[idx]
        Xb = Xb[:, np.abs(Xb).sum(0) > 0]
        try:
            r = h1_reml(newp, ctx[idx], tnew, y[idx], Xb, x_player[pick], d, start=start)
            deltas[b] = r.delta
        except Exception:  # noqa: BLE001
            deltas[b] = np.nan
    deltas = deltas[np.isfinite(deltas)]
    lo, hi = np.percentile(deltas, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return dict(ci=(float(lo), float(hi)), p=boot_p(deltas), se=float(deltas.std()), boot=deltas, n_ok=len(deltas))


def player_context_stats(player, ctx, r, P, d=2):
    """Per player-context mean, count and pooled within-SD of a (residualised) outcome r."""
    idx = player * d + ctx
    n = np.bincount(idx, minlength=P * d).reshape(P, d).astype(float)
    s1 = np.bincount(idx, weights=r, minlength=P * d).reshape(P, d)
    s2 = np.bincount(idx, weights=r * r, minlength=P * d).reshape(P, d)
    m = s1 / np.maximum(n, 1)
    ss = s2 - n * m ** 2
    sw2 = ss.sum(0) / np.maximum((n - 1).sum(0), 1)
    return m, n, sw2


def moment_rho(x, m, n, sw2, floor=0.05):
    """Disattenuated correlation per context (spec §1.2), vectorised over a leading bootstrap axis.
    x: (..., P); m, n: (..., P, d); sw2: (d,)."""
    xc = x - x.mean(-1, keepdims=True)
    mc = m - m.mean(-2, keepdims=True)
    P = x.shape[-1]
    cov = (xc[..., None] * mc).sum(-2) / (P - 1)
    vx = (xc ** 2).sum(-1) / (P - 1)
    vm = (mc ** 2).sum(-2) / (P - 1)
    samp = (sw2 / n).mean(-2)
    vt = np.maximum(vm - samp, floor * vm)
    rho = cov / np.sqrt(vx[..., None] * vt)
    raw = cov / np.sqrt(vx[..., None] * vm)
    return rho, raw


def h1_moment_bootstrap(x, m, n, sw2, B, rng, alpha=0.05):
    P = len(x)
    rho, raw = moment_rho(x, m, n, sw2)
    bi = rng.integers(0, P, (B, P))
    rb, rawb = moment_rho(x[bi], m[bi], n[bi], sw2)
    db = rb[:, 0] - rb[:, 1]; drb = rawb[:, 0] - rawb[:, 1]
    lo, hi = np.percentile(db, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    p = boot_p(db)
    return dict(rho_m=rho, delta_m=float(rho[0] - rho[1]), delta_raw=float(raw[0] - raw[1]), ci=(float(lo), float(hi)),
                p=p, p_raw=boot_p(drb), se=float(db.std()), boot=db)


def boot_p(db):
    """Two-sided percentile-bootstrap p-value (CI inversion), floored at 1/B."""
    B = len(db)
    return float(min(1.0, max(2 * min((db <= 0).mean(), (db >= 0).mean()), 1 / B)))


def h1_procedure(player, ctx, team, y, Xw, Wres, x_player, B, rng, alpha=0.05, d=2):
    """Full registered H1 procedure. Xw: LMM fixed-effect design (context-specific); Wres: pooled
    covariates for the moment residualisation. Returns REML point estimate, moment bootstrap CI, decision."""
    P = len(x_player)
    reml = h1_reml(player, ctx, team, y, Xw, x_player, d)
    r = residualise_np(Wres, y)
    m, n, sw2 = player_context_stats(player, ctx, r, P, d)
    mb = h1_moment_bootstrap(x_player, m, n, sw2, B, rng, alpha)
    lo, hi = mb["ci"]
    supported = bool(reml.delta > 0 and lo > 0)
    return dict(delta_reml=reml.delta, rho_reml=reml.rho, beta=reml.beta, s2_team=reml.s2_team, converged=reml.converged,
                delta_moment=mb["delta_m"], delta_raw=mb["delta_raw"], ci_lo=lo, ci_hi=hi, p=mb["p"], p_raw=mb["p_raw"],
                se_boot=mb["se"], supported=supported,
                disagree=bool(abs(reml.delta - mb["delta_m"]) > 0.5 * mb["se"]))


# ------------------------------------------------------------------------------------------------
# H2
# ------------------------------------------------------------------------------------------------
def standardise(v):
    return (v - v.mean()) / v.std(ddof=1)


def h2_reml(player, team, y, Xw, F, x):
    Fs, xs = standardise(F), standardise(x)
    X = np.column_stack([np.ones(len(y)), Xw, Fs[player], xs[player]])
    fit = fit_reml(y, X, player, np.zeros(len(y), int), team, 1)
    bF, bP = fit.beta[-2], fit.beta[-1]
    s2b = float(fit.sigma_b[0, 0])
    r = np.corrcoef(Fs, xs)[0, 1]
    tot = bF ** 2 + bP ** 2 + 2 * bF * bP * r + s2b
    xperp_var = 1 - r ** 2
    partial = bP * np.sqrt(xperp_var) / np.sqrt(bP ** 2 * xperp_var + s2b)
    se = float(np.sqrt(fit.cov_beta[-1, -1]))
    return dict(beta_P=float(bP), beta_F=float(bF), beta_P_std=float(bP / np.sqrt(tot)), partial=float(partial),
                se_wald=se, s2b=s2b, s2_team=fit.s2_team, s2=float(fit.s2_resid[0]), converged=fit.converged)


def player_stats(player, r, P):
    n = np.bincount(player, minlength=P).astype(float)
    s1 = np.bincount(player, weights=r, minlength=P)
    s2 = np.bincount(player, weights=r * r, minlength=P)
    m = s1 / np.maximum(n, 1)
    sw2 = (s2 - n * m ** 2).sum() / max((n - 1).sum(), 1)
    return m, n, sw2


def wls_two_stage(m, n, sw2, F, x, s2b=None):
    """Two-stage equivalent: WLS of player means on (F, x) with weights 1/(s2b + sw2/n); HC3 SEs."""
    if s2b is None:
        s2b = max(np.var(m, ddof=1) - np.mean(sw2 / n), 0.05 * np.var(m, ddof=1))
    w = 1 / (s2b + sw2 / n)
    X = np.column_stack([np.ones(len(m)), standardise(F), standardise(x)])
    Wx = X * w[:, None]
    XtWX = X.T @ Wx
    XtWXi = np.linalg.inv(XtWX)
    b = XtWXi @ (Wx.T @ m)
    e = m - X @ b
    h = np.einsum("ij,jk,ik->i", Wx, XtWXi, X)
    meat = (X * (w * e / (1 - h))[:, None]).T @ (X * (w * e / (1 - h))[:, None])
    cov = XtWXi @ meat @ XtWXi
    return b, np.sqrt(np.diag(cov)), s2b


def eiv_two_stage(m, n, sw2, F, x, rel_F, rel_x):
    """Errors-in-variables (method-of-moments regression calibration) on the player level."""
    W = np.column_stack([standardise(F), standardise(x)])
    S = np.cov(W.T)
    S_true = S - np.diag([(1 - rel_F) * S[0, 0], (1 - rel_x) * S[1, 1]])
    c = np.array([np.cov(W[:, k], m)[0, 1] for k in range(2)])
    return np.linalg.solve(S_true, c)


def h2_bootstrap(m, n, sw2, F, x, B, rng, alpha=0.05):
    P = len(m)
    bi = rng.integers(0, P, (B, P))
    out = np.empty(B)
    for k in range(B):
        i = bi[k]
        try:
            out[k] = wls_two_stage(m[i], n[i], sw2, F[i], x[i])[0][2]
        except np.linalg.LinAlgError:
            out[k] = np.nan
    out = out[np.isfinite(out)]
    lo, hi = np.percentile(out, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return dict(ci=(float(lo), float(hi)), p=boot_p(out), se=float(out.std()), boot=out)


# ---- player-grouped CV with fold-internal residualisation (sufficient statistics) ---------------
@dataclass
class PlayerSuff:
    XtX: np.ndarray   # (P, p, p) including intercept
    Xty: np.ndarray   # (P, p)
    yty: np.ndarray   # (P,)
    xbar: np.ndarray  # (P, p)
    ybar: np.ndarray  # (P,)
    n: np.ndarray     # (P,)


def player_sufficient(player, W, y, P) -> PlayerSuff:
    X = np.column_stack([np.ones(len(y)), W])
    p = X.shape[1]
    XtX = np.zeros((P, p, p)); Xty = np.zeros((P, p)); yty = np.zeros(P)
    order = np.argsort(player, kind="stable"); ps = player[order]
    bounds = np.searchsorted(ps, np.arange(P + 1))
    Xo, yo = X[order], y[order]
    for i in range(P):
        a, b = bounds[i], bounds[i + 1]
        Xi, yi = Xo[a:b], yo[a:b]
        XtX[i] = Xi.T @ Xi; Xty[i] = Xi.T @ yi; yty[i] = yi @ yi
    n = np.diff(bounds).astype(float)
    xbar = np.array([Xty[i] * 0 for i in range(P)])
    for i in range(P):
        a, b = bounds[i], bounds[i + 1]
        xbar[i] = Xo[a:b].mean(0) if b > a else 0
    ybar = np.array([yo[bounds[i]:bounds[i + 1]].mean() if bounds[i + 1] > bounds[i] else 0 for i in range(P)])
    return PlayerSuff(XtX, Xty, yty, xbar, ybar, n)


def _resid_means(S: PlayerSuff, train, test):
    """Fit pooled OLS on training players' plays; return residual means and pooled within var for train/test."""
    A = S.XtX[train].sum(0); c = S.Xty[train].sum(0)
    beta = np.linalg.lstsq(A, c, rcond=None)[0]
    def means(idx):
        return S.ybar[idx] - S.xbar[idx] @ beta
    def within(idx):
        ss = S.yty[idx] - 2 * S.Xty[idx] @ beta + np.einsum("ij,ijk,ik->i", np.broadcast_to(beta, (len(idx), len(beta))), S.XtX[idx], np.broadcast_to(beta, (len(idx), len(beta))))
        m = means(idx)
        return (ss - S.n[idx] * m ** 2).sum() / (S.n[idx] - 1).sum()
    return means(train), means(test), within(train)


def player_folds(P: int, folds: int, rng) -> np.ndarray:
    """Fold id per PLAYER (all plays of a player share a fold: held-out players, never held-out plays)."""
    perm = rng.permutation(P); fid = np.empty(P, int); fid[perm] = np.arange(P) % folds
    return fid


def h2_cv(S: PlayerSuff, F, x, rng, folds=10, repeats=20):
    """Player-grouped K-fold CV of M1 (F) vs M2 (F + x) predicting held-out players' shrunken levels.
    Returns Delta R^2_CV (pooled over repeats) and component R^2."""
    P = len(F)
    res = []
    for _ in range(repeats):
        fid = player_folds(P, folds, rng)
        pred1 = np.empty(P); pred2 = np.empty(P); target = np.empty(P); mu_tr = np.empty(P)
        for f in range(folds):
            te = np.where(fid == f)[0]; tr = np.where(fid != f)[0]
            m_tr, m_te, sw2 = _resid_means(S, tr, te)
            s2b = max(np.var(m_tr, ddof=1) - np.mean(sw2 / S.n[tr]), 1e-6)
            k_tr = s2b / (s2b + sw2 / S.n[tr]); k_te = s2b / (s2b + sw2 / S.n[te])
            mu = np.average(m_tr, weights=k_tr)
            t_tr = mu + k_tr * (m_tr - mu); t_te = mu + k_te * (m_te - mu)
            Fm, Fs = F[tr].mean(), F[tr].std(ddof=1); xm, xsd = x[tr].mean(), x[tr].std(ddof=1)
            X1 = np.column_stack([np.ones(len(tr)), (F[tr] - Fm) / Fs]); X1t = np.column_stack([np.ones(len(te)), (F[te] - Fm) / Fs])
            X2 = np.column_stack([X1, (x[tr] - xm) / xsd]); X2t = np.column_stack([X1t, (x[te] - xm) / xsd])
            pred1[te] = X1t @ np.linalg.lstsq(X1, t_tr, rcond=None)[0]
            pred2[te] = X2t @ np.linalg.lstsq(X2, t_tr, rcond=None)[0]
            target[te] = t_te; mu_tr[te] = mu
        sst = ((target - mu_tr) ** 2).sum()
        r1 = 1 - ((target - pred1) ** 2).sum() / sst; r2 = 1 - ((target - pred2) ** 2).sum() / sst
        res.append((r1, r2))
    res = np.array(res)
    return dict(r2_m1=float(res[:, 0].mean()), r2_m2=float(res[:, 1].mean()), dr2=float((res[:, 1] - res[:, 0]).mean()))


def h2_cv_bootstrap(S: PlayerSuff, F, x, rng, B=500, folds=10, repeats=2, level=0.90):
    """Player bootstrap of the whole CV procedure (duplicated players are distinct units)."""
    P = len(F); out = []
    for _ in range(B):
        i = rng.integers(0, P, P)
        Sb = PlayerSuff(S.XtX[i], S.Xty[i], S.yty[i], S.xbar[i], S.ybar[i], S.n[i])
        out.append(h2_cv(Sb, F[i], x[i], rng, folds, repeats)["dr2"])
    out = np.asarray(out)
    return float(np.percentile(out, 100 * (1 - level) / 2)), out


# ------------------------------------------------------------------------------------------------
# multiplicity
# ------------------------------------------------------------------------------------------------
def fixed_sequence(results: list[dict], alpha=0.05) -> list[bool]:
    """Hierarchical testing: test k is performed (at alpha) only if tests 1..k-1 were all supported.
    Each result needs 'p' and 'direction_ok' (estimate in the predicted direction)."""
    out, go = [], True
    for r in results:
        rej = go and r["p"] < alpha and r["direction_ok"]
        out.append(bool(rej)); go = go and rej
    return out


def holm(results: list[dict], alpha=0.05) -> list[bool]:
    m = len(results)
    order = np.argsort([r["p"] for r in results])
    rej = [False] * m
    for k, i in enumerate(order):
        if results[i]["p"] < alpha / (m - k) and results[i]["direction_ok"]:
            rej[i] = True
        else:
            break
    return rej
