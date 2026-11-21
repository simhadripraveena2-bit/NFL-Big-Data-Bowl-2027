"""Registered H1 sensitivity analyses, negative control and interval diagnostics (post-primary; frozen code untouched).

Everything here re-uses the frozen estimator (`reml.fit_reml`, `confirmatory.h1_reml`, `confirmatory.design_h1`).
New pieces implement only what the protocol registers but the frozen modules did not yet contain:
  * POST-season play features with the exact Phase 3 definition (for the REG + POST robustness check);
  * natural cubic spline f_c(x), 3 df (spec §1.4) and its player-cluster bootstrap / player-grouped CV;
  * ceiling-robust outcome: bivariate player-level measurement-error model (spec §1.4);
  * context labels permuted within player (negative control, spec §4);
  * model-based Wald interval for Delta: numerical Hessian of the SAME REML criterion at the fitted parameters
    (re-implemented here and verified to reproduce `RemlFit.neg2ll`), delta method (spec §10 "as a check").
"""
from __future__ import annotations

import numpy as np
import polars as pl
from scipy import linalg, sparse

from nfl_bdb.data.io import load
from nfl_bdb.data.play_table import AMBIGUOUS_ROUTES, DEEP_ROUTES, SHORT_ROUTES
from nfl_bdb.models import confirmatory as cf
from nfl_bdb.models.reml import _cross, fit_reml


# ------------------------------------------------------------------------------------------------
# POST-season features (Phase 3 definition: k = frames since ball_snap; vmax_prepass = max s for k <= k_pf)
# ------------------------------------------------------------------------------------------------
def prepass_features(season_types=("POST",), seasons=(2023, 2024, 2025)) -> pl.DataFrame:
    from nfl_bdb.data.game_kinematics import load_game_sequences
    out = []
    for yr in seasons:
        df, _ = load_game_sequences(seasons=(yr,), season_types=season_types, cols=["game_id", "play_id", "nfl_id", "time", "s", "event"])
        if df.height == 0:
            continue
        snap = df.filter(pl.col("event") == "ball_snap").group_by("seq").agg(pl.col("time").min().alias("t_snap"))
        pf = df.filter(pl.col("event").is_in(["pass_forward", "pass_shovel"])).group_by("seq").agg(pl.col("time").min().alias("t_pf"))
        df = (df.join(snap, on="seq").join(pf, on="seq", how="left").with_columns(
            ((pl.col("time") - pl.col("t_snap")).dt.total_milliseconds() / 100).round().cast(pl.Int32).alias("k"),
            ((pl.col("t_pf") - pl.col("t_snap")).dt.total_milliseconds() / 100).round().cast(pl.Int32).alias("k_pf"))
            .filter(pl.col("k") >= 0))
        out.append(df.group_by("seq").agg(pl.col("game_id").first(), pl.col("play_id").first(), pl.col("nfl_id").first(),
                                          pl.col("k_pf").first(), pl.col("s").max().alias("vmax_play"),
                                          pl.col("s").filter(pl.col("k") <= pl.col("k_pf")).max().alias("vmax_prepass")).drop("seq"))
    return pl.concat(out) if out else pl.DataFrame()


def play_table(season_types=("POST",), features: pl.DataFrame | None = None) -> pl.DataFrame:
    """Same derived columns as play_table.reg_play_table, for other season types (verified equal on REG)."""
    games = load("games", lazy=False).select("game_id", "season", "season_type", "week")
    pos = load("combine_results", lazy=False).select("nfl_id", pl.col("combine_position").alias("pos"), "draft_year")
    pp = (load("player_play", lazy=False).join(games, on="game_id").filter(pl.col("season_type").is_in(list(season_types)))
          .join(pos, on="nfl_id", how="inner"))
    feat = features.select("game_id", "play_id", "nfl_id", "k_pf", "vmax_play", "vmax_prepass")
    d = pp.join(feat, on=["game_id", "play_id", "nfl_id"], how="left")
    d = d.with_columns(
        (pl.col("pass_result").fill_null("") != "").alias("is_pass"),
        (pl.col("k_pf") / 10).alias("time_to_throw"),
        (pl.col("season") - pl.col("draft_year") + 1).alias("nfl_year"),
        pl.when(pl.col("yards_to_go") <= 3).then(pl.lit("short")).when(pl.col("yards_to_go") <= 7)
        .then(pl.lit("med")).otherwise(pl.lit("long")).alias("ytg_bin"),
    ).with_columns(
        pl.when(pl.col("time_to_throw").is_null()).then(pl.lit("NA")).when(pl.col("time_to_throw") < 2.5)
        .then(pl.lit("<2.5")).when(pl.col("time_to_throw") < 3.5).then(pl.lit("2.5-3.5"))
        .otherwise(pl.lit(">=3.5")).alias("ttt_bin"),
        pl.when(pl.col("route_ran").is_in(DEEP_ROUTES)).then(pl.lit("deep"))
        .when(pl.col("route_ran").is_in(SHORT_ROUTES)).then(pl.lit("short"))
        .when(pl.col("route_ran").is_not_null()).then(pl.lit("ambiguous")).alias("route_depth"),
    )
    return d


# ------------------------------------------------------------------------------------------------
# indexing helpers (identical to the confirmatory runner)
# ------------------------------------------------------------------------------------------------
def index_frame(df: pl.DataFrame, high: str = "deep"):
    df = df.with_columns(pl.when(pl.col("ctx") == high).then(0).otherwise(1).alias("ctx_i"),
                         (pl.col("team_abbr") + "_" + pl.col("season").cast(pl.Utf8)).alias("team_season"))
    ids = sorted(df["nfl_id"].unique().to_list()); pm = {k: i for i, k in enumerate(ids)}
    ts = sorted(df["team_season"].unique().to_list()); tm = {k: i for i, k in enumerate(ts)}
    df = df.with_columns(pl.col("nfl_id").replace_strict(pm).alias("pid"), pl.col("team_season").replace_strict(tm).alias("team_i"))
    return df.sort("pid", "ctx_i", "game_id", "play_id"), ids


def min_ctx_filter(df: pl.DataFrame, k: int = 20) -> pl.DataFrame:
    c = df.group_by("nfl_id", "ctx").len().pivot(index="nfl_id", on="ctx", values="len").fill_null(0)
    for col in ("deep", "short"):
        if col not in c.columns:
            c = c.with_columns(pl.lit(0).alias(col))
    keep = c.filter((pl.col("deep") >= k) & (pl.col("short") >= k))["nfl_id"].implode()
    return df.filter(pl.col("nfl_id").is_in(keep))


# ------------------------------------------------------------------------------------------------
# natural cubic spline, 3 df (ESL 5.2.1 basis: N1 = x, N_{k+2} = d_k - d_{K-1}), knots K = 4
# ------------------------------------------------------------------------------------------------
def ns_basis(x: np.ndarray, knots: np.ndarray, deriv: bool = False) -> np.ndarray:
    K = len(knots); xi = knots

    def d(k):
        a = np.maximum(x - xi[k], 0); b = np.maximum(x - xi[K - 1], 0)
        if deriv:
            return (3 * a ** 2 - 3 * b ** 2) / (xi[K - 1] - xi[k])
        return (a ** 3 - b ** 3) / (xi[K - 1] - xi[k])
    cols = [np.ones_like(x) if deriv else x.copy()] + [d(k) - d(K - 2) for k in range(K - 2)]
    return np.column_stack(cols)


def spline_design(Xw, player, ctx, xs, knots, d=2):
    B = ns_basis(xs, knots)[player]
    return np.column_stack([Xw] + [B * (ctx == c)[:, None] for c in range(d)])


def spline_fit(player, ctx, team, y, Xw, x_player, knots_raw, d=2, start=None):
    """Returns average derivative per context (yd/s per within-sample SD of x) and the fit."""
    mu, sd = x_player.mean(), x_player.std(ddof=1)
    xs = (x_player - mu) / sd; kn = (np.asarray(knots_raw) - mu) / sd
    kn = np.concatenate([[min(kn[0], xs.min())], kn[1:-1], [max(kn[-1], xs.max())]])
    X = spline_design(Xw, player, ctx, xs, kn, d)
    fit = fit_reml(y, X, player, ctx, team, d, start=None if start is None else dict(theta=start))
    nb = 3
    coef = fit.beta[-d * nb:].reshape(d, nb)
    Dv = ns_basis(xs, kn, deriv=True)
    avg_deriv = (Dv @ coef.T).mean(0)
    return dict(avg_deriv=avg_deriv, diff=float(avg_deriv[0] - avg_deriv[1]), coef=coef, knots_std=kn, fit=fit, xs=xs)


def cluster_resample(player, team, P, rng):
    """Registered resampling scheme (h1_reml_bootstrap): players drawn with replacement, duplicates are distinct
    units, team-season columns shared."""
    order = np.argsort(player, kind="stable"); bnd = np.searchsorted(player[order], np.arange(P + 1))
    rows = [order[bnd[i]:bnd[i + 1]] for i in range(P)]
    pick = rng.integers(0, P, P)
    idx = np.concatenate([rows[i] for i in pick])
    newp = np.concatenate([np.full(len(rows[i]), k) for k, i in enumerate(pick)])
    _, tnew = np.unique(team[idx], return_inverse=True)
    return pick, idx, newp, tnew


def spline_bootstrap(player, ctx, team, y, Xw, x_player, knots_raw, B, seed, start=None):
    rng = np.random.default_rng(seed); P = len(x_player); out = np.full((B, 3), np.nan)
    for b in range(B):
        pick, idx, newp, tnew = cluster_resample(player, team, P, rng)
        Xb = Xw[idx]; Xb = Xb[:, np.abs(Xb).sum(0) > 0]
        try:
            r = spline_fit(newp, ctx[idx], tnew, y[idx], Xb, x_player[pick], knots_raw, start=start)
            out[b] = [r["avg_deriv"][0], r["avg_deriv"][1], r["diff"]]
        except Exception:  # noqa: BLE001
            pass
    return out


def grouped_cv_linear_vs_spline(df_idx, covs, x_player, knots_raw, draft_class, seed, folds=10, repeats=20):
    """Player-grouped 10-fold x 20 CV stratified by draft class; marginal (fixed-effect) prediction of held-out
    players' plays. Returns RMSE per repeat for the linear and spline models."""
    rng = np.random.default_rng(seed)
    player = df_idx["pid"].to_numpy(); ctx = df_idx["ctx_i"].to_numpy(); y = df_idx["y"].to_numpy().astype(float)
    P = len(x_player); res = []
    for _ in range(repeats):
        fid = np.empty(P, int)
        for cls in np.unique(draft_class):
            m = np.where(draft_class == cls)[0]; perm = rng.permutation(m)
            fid[perm] = (np.arange(len(m)) + rng.integers(0, folds)) % folds
        se = {"linear": 0.0, "spline": 0.0}; n = 0
        for f in range(folds):
            te_p = np.where(fid == f)[0]
            if len(te_p) == 0:
                continue
            tr = ~np.isin(player, te_p); te = ~tr
            Xall = cf.design_h1(df_idx, covs, 2)   # common columns for train / test
            tr_ids = np.unique(player[tr]); pm = -np.ones(P, int); pm[tr_ids] = np.arange(len(tr_ids))
            _, ttr = np.unique(df_idx["team_i"].to_numpy()[tr], return_inverse=True)
            keep = np.abs(Xall[tr]).sum(0) > 0
            Xtr, Xte = Xall[tr][:, keep], Xall[te][:, keep]
            mu, sd = x_player[tr_ids].mean(), x_player[tr_ids].std(ddof=1)
            xs_all = (x_player - mu) / sd
            # linear
            XL_tr = np.column_stack([Xtr] + [xs_all[player[tr]] * (ctx[tr] == c) for c in (0, 1)])
            XL_te = np.column_stack([Xte] + [xs_all[player[te]] * (ctx[te] == c) for c in (0, 1)])
            fl = fit_reml(y[tr], XL_tr, pm[player[tr]], ctx[tr], ttr, 2)
            # spline (knots fixed from all WR combine participants, boundary from training range)
            kn = (np.asarray(knots_raw) - mu) / sd
            kn = np.concatenate([[min(kn[0], xs_all[tr_ids].min())], kn[1:-1], [max(kn[-1], xs_all[tr_ids].max())]])
            XS_tr = spline_design(Xtr, player[tr], ctx[tr], xs_all, kn); XS_te = spline_design(Xte, player[te], ctx[te], xs_all, kn)
            fs = fit_reml(y[tr], XS_tr, pm[player[tr]], ctx[tr], ttr, 2)
            se["linear"] += float(np.sum((y[te] - XL_te @ fl.beta) ** 2)); se["spline"] += float(np.sum((y[te] - XS_te @ fs.beta) ** 2))
            n += int(te.sum())
        res.append(dict(rmse_linear=np.sqrt(se["linear"] / n), rmse_spline=np.sqrt(se["spline"] / n)))
    return pl.DataFrame(res)


# ------------------------------------------------------------------------------------------------
# ceiling-robust outcome: bivariate player-level measurement-error model (spec §1.4)
# ------------------------------------------------------------------------------------------------
def upper_expression(y: np.ndarray, top: float = 0.10) -> float:
    k = max(1, int(np.ceil(top * len(y))))
    return float(np.sort(y)[-k:].mean())


def ceiling_table(df_idx, seed, B_in=200):
    rng = np.random.default_rng(seed); rows = []
    for (pid, c), g in df_idx.group_by(["pid", "ctx_i"], maintain_order=True):
        yy = g["y"].to_numpy().astype(float)
        bs = [upper_expression(rng.choice(yy, len(yy))) for _ in range(B_in)]
        rows.append(dict(pid=pid, ctx_i=c, u=upper_expression(yy), var_e=float(np.var(bs, ddof=1)), n=len(yy)))
    return pl.DataFrame(rows).sort("pid", "ctx_i")


def ceiling_rho(U: np.ndarray, VE: np.ndarray, x: np.ndarray):
    """U, VE: P x 2 (upper expression, its sampling variance); x per player. Moment estimator of the bivariate
    ME model u_ic = mu_c + beta_c x_i + b_ic + e_ic:  beta_c by OLS on standardised x; Sigma_b = residual
    covariance minus mean ME variance; rho_c = beta_c / sqrt(beta_c^2 + Sigma_b,cc)."""
    xs = (x - x.mean()) / x.std(ddof=1)
    X = np.column_stack([np.ones(len(xs)), xs])
    coef, *_ = np.linalg.lstsq(X, U, rcond=None)
    R = U - X @ coef
    S = np.cov(R.T, ddof=2) - np.diag(VE.mean(0))
    beta = coef[1]
    sb = np.maximum(np.diag(S), 1e-6)
    rho = beta / np.sqrt(beta ** 2 + sb)
    return rho, beta, S


# ------------------------------------------------------------------------------------------------
# negative control: context labels permuted within player
# ------------------------------------------------------------------------------------------------
def permute_within_player(df_idx: pl.DataFrame, rng) -> pl.DataFrame:
    pid = df_idx["pid"].to_numpy(); ctx = df_idx["ctx_i"].to_numpy().copy()
    order = np.argsort(pid, kind="stable"); bnd = np.searchsorted(pid[order], np.arange(pid.max() + 2))
    for i in range(pid.max() + 1):
        ix = order[bnd[i]:bnd[i + 1]]
        ctx[ix] = rng.permutation(ctx[ix])
    return df_idx.with_columns(pl.Series("ctx_i", ctx)).sort("pid", "ctx_i", "game_id", "play_id")


# ------------------------------------------------------------------------------------------------
# Wald interval: the REML criterion of reml.fit_reml, re-implemented for curvature only
# ------------------------------------------------------------------------------------------------
def reml_criterion(y, X, player, ctx, team, d):
    """Returns f(theta) = -2 l_R exactly as in reml.fit_reml (same parametrisation, same algebra)."""
    y = np.asarray(y, float); X = np.asarray(X, float)
    P = int(player.max()) + 1; T = int(team.max()) + 1 if team is not None else 0
    q = P * d + T; n = len(y); rows = np.arange(n)
    Zp = sparse.csr_matrix((np.ones(n), (rows, player * d + ctx)), shape=(n, q))
    if T:
        Zp = Zp + sparse.csr_matrix((np.ones(n), (rows, P * d + team)), shape=(n, q))
    cr = [_cross(X[ix], Zp[ix], y[ix]) for ix in [np.where(ctx == g)[0] for g in range(d)]]
    tril = np.tril_indices(d)

    def f(th):
        L = np.zeros((d, d)); L[tril] = th[: len(tril[0])]
        L[np.diag_indices(d)] = np.exp(L[np.diag_indices(d)])
        k = len(tril[0]); s2t = np.exp(2 * th[k]) if T else 0.0
        off = k + (1 if T else 0); s2g = np.exp(2 * th[off: off + d])
        Sb = L @ L.T + 1e-10 * np.eye(d); w = 1 / s2g
        A = sum(w[g] * cr[g]["ZZ"] for g in range(d)); Bm = sum(w[g] * cr[g]["XZ"] for g in range(d))
        Pm = sum(w[g] * cr[g]["XX"] for g in range(d)); u = sum(w[g] * cr[g]["Zy"] for g in range(d))
        v = sum(w[g] * cr[g]["Xy"] for g in range(d)); s = sum(w[g] * cr[g]["yy"] for g in range(d))
        C = A.copy(); Sbi = np.linalg.inv(Sb)
        for i in range(P):
            C[i * d:(i + 1) * d, i * d:(i + 1) * d] += Sbi
        if T:
            C[P * d:, P * d:] += np.eye(T) / max(s2t, 1e-12)
        cfac = linalg.cho_factor(C, lower=True, check_finite=False)
        XVX = Pm - Bm @ linalg.cho_solve(cfac, Bm.T, check_finite=False)
        XVy = v - Bm @ linalg.cho_solve(cfac, u, check_finite=False)
        yVy = s - u @ linalg.cho_solve(cfac, u, check_finite=False)
        cx = linalg.cho_factor(XVX, lower=True, check_finite=False)
        beta = linalg.cho_solve(cx, XVy, check_finite=False)
        return float(sum(cr[g]["n"] * np.log(s2g[g]) for g in range(d)) + P * np.linalg.slogdet(Sb)[1]
                     + (T * np.log(max(s2t, 1e-12)) if T else 0.0) + 2 * np.sum(np.log(np.diag(cfac[0])))
                     + 2 * np.sum(np.log(np.diag(cx[0]))) + yVy - beta @ XVy)
    return f


def num_hessian(f, th, h=1e-3):
    k = len(th); H = np.zeros((k, k))
    for i in range(k):
        for j in range(i, k):
            e_i = np.zeros(k); e_j = np.zeros(k); e_i[i] = h; e_j[j] = h
            H[i, j] = H[j, i] = (f(th + e_i + e_j) - f(th + e_i - e_j) - f(th - e_i + e_j) + f(th - e_i - e_j)) / (4 * h * h)
    return H


def delta_of(beta_x, th, d=2):
    tril = np.tril_indices(d)
    L = np.zeros((d, d)); L[tril] = th[: len(tril[0])]; L[np.diag_indices(d)] = np.exp(L[np.diag_indices(d)])
    Sb = L @ L.T + 1e-10 * np.eye(d)
    rho = beta_x / np.sqrt(beta_x ** 2 + np.diag(Sb))
    return float(rho[0] - rho[1])


def wald_delta(player, ctx, team, y, Xw, x_player, d=2, h=1e-3):
    """Model-based Wald SE of Delta at the registered REML fit. Cov(theta) = 2 H^-1 (H = Hessian of -2 l_R);
    Cov(beta) = RemlFit.cov_beta; beta and theta asymptotically independent under REML."""
    xp = (x_player - x_player.mean()) / x_player.std(ddof=1)
    X = np.column_stack([Xw] + [xp[player] * (ctx == c) for c in range(d)])
    fit = fit_reml(y, X, player, ctx, team, d)
    f = reml_criterion(y, X, player, ctx, team, d)
    th = fit.theta
    check = abs(f(th) - fit.neg2ll)
    H = num_hessian(f, th, h)
    cov_th = 2 * np.linalg.inv(H)
    bx = fit.beta[-d:]; cov_bx = fit.cov_beta[-d:, -d:]
    eps = 1e-5
    g_b = np.array([(delta_of(bx + e, th, d) - delta_of(bx - e, th, d)) / (2 * eps) for e in np.eye(d) * eps])
    g_t = np.array([(delta_of(bx, th + e, d) - delta_of(bx, th - e, d)) / (2 * eps) for e in np.eye(len(th)) * eps])
    var = float(g_b @ cov_bx @ g_b + g_t @ cov_th @ g_t)
    eig = np.linalg.eigvalsh(H)
    return dict(delta=delta_of(bx, th, d), se=np.sqrt(var), var_from_beta=float(g_b @ cov_bx @ g_b), var_from_theta=float(g_t @ cov_th @ g_t),
                criterion_reproduced_abs_diff=float(check), hessian_min_eig=float(eig.min()), hessian_max_eig=float(eig.max()),
                converged=fit.converged, theta=th.tolist())
