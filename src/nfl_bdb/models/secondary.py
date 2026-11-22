"""Registered secondary analyses: H1-DB, H1-DL(a), H1-DL(b), H5(a/b/c), H1-global inputs (frozen code untouched).

Re-used unchanged: confirmatory.h1_reml / h1_registered_test / design_h1 / boot_p; reml.fit_reml;
h1_extensions.reml_criterion / num_hessian / cluster_resample; demand.meta_regression_reml (validated against below).
Added:
  * index_frame for any ordered context list (2 or 3 contexts);
  * rho_wald: per-context rho and their delta-method covariance from the same REML fit (numerical Hessian of the
    identical REML criterion, as validated for the H1-WR Wald check);
  * H1-DL(b) paired player-cluster bootstrap (registered scheme): base model vs model + player alignment x context +
    standardised combine weight x context; pooled rho = mean of the two context rhos (operational definition declared
    in scripts/run_secondary.py before the run);
  * REML random-effects meta-regression returning all coefficients (identical criterion to demand.meta_regression_reml)
    and a cell-cluster bootstrap within position.
"""
from __future__ import annotations

import numpy as np
import polars as pl
from scipy import optimize

from nfl_bdb.models import confirmatory as cf
from nfl_bdb.models.h1_extensions import cluster_resample, num_hessian, reml_criterion
from nfl_bdb.models.reml import fit_reml


def index_frame(df: pl.DataFrame, contexts: list[str]):
    cmap = {c: i for i, c in enumerate(contexts)}
    df = df.filter(pl.col("ctx").is_in(contexts)).with_columns(
        pl.col("ctx").replace_strict(cmap).cast(pl.Int64).alias("ctx_i"),
        (pl.col("team_abbr") + "_" + pl.col("season").cast(pl.Utf8)).alias("team_season"))
    ids = sorted(df["nfl_id"].unique().to_list()); pm = {k: i for i, k in enumerate(ids)}
    ts = sorted(df["team_season"].unique().to_list()); tm = {k: i for i, k in enumerate(ts)}
    df = df.with_columns(pl.col("nfl_id").replace_strict(pm).alias("pid"), pl.col("team_season").replace_strict(tm).alias("team_i"))
    return df.sort("pid", "ctx_i", "game_id", "play_id"), ids


def arrays(dfi, xcol="x_peak"):
    xp = dfi.group_by("pid").agg(pl.col(xcol).first()).sort("pid")[xcol].to_numpy().astype(float)
    return dfi["pid"].to_numpy(), dfi["ctx_i"].to_numpy(), dfi["team_i"].to_numpy(), dfi["y"].to_numpy().astype(float), xp


def player_ctx_columns(values: np.ndarray, player: np.ndarray, ctx: np.ndarray, d: int) -> np.ndarray:
    """Player-level covariate(s) entered with context-specific coefficients (values: P x k)."""
    v = np.atleast_2d(values.T).T if values.ndim == 1 else values
    return np.column_stack([v[player][:, j] * (ctx == c) for c in range(d) for j in range(v.shape[1])])


def _rho_from(beta_x, th, d):
    tril = np.tril_indices(d)
    L = np.zeros((d, d)); L[tril] = th[: len(tril[0])]; L[np.diag_indices(d)] = np.exp(L[np.diag_indices(d)])
    Sb = L @ L.T + 1e-10 * np.eye(d)
    return beta_x / np.sqrt(beta_x ** 2 + np.diag(Sb))


def rho_wald(player, ctx, team, y, Xw, x_player, d, h=1e-3):
    """REML fit (same estimand as confirmatory.h1_reml) + delta-method covariance of the rho vector."""
    xp = (x_player - x_player.mean()) / x_player.std(ddof=1)
    X = np.column_stack([Xw] + [xp[player] * (ctx == c) for c in range(d)])
    fit = fit_reml(y, X, player, ctx, team, d)
    th = fit.theta; bx = fit.beta[-d:]
    f = reml_criterion(y, X, player, ctx, team, d)
    H = num_hessian(f, th, h)
    cov_th = 2 * np.linalg.inv(H); cov_bx = fit.cov_beta[-d:, -d:]
    eps = 1e-5
    Jb = np.column_stack([(_rho_from(bx + e, th, d) - _rho_from(bx - e, th, d)) / (2 * eps) for e in np.eye(d) * eps])
    Jt = np.column_stack([(_rho_from(bx, th + e, d) - _rho_from(bx, th - e, d)) / (2 * eps) for e in np.eye(len(th)) * eps])
    cov = Jb @ cov_bx @ Jb.T + Jt @ cov_th @ Jt.T
    rho = _rho_from(bx, th, d)
    return dict(rho=rho, cov=cov, se=np.sqrt(np.diag(cov)), converged=fit.converged, sigma_b=fit.sigma_b,
                s2_team=fit.s2_team, s2_resid=fit.s2_resid, beta_x=bx, hessian_min_eig=float(np.linalg.eigvalsh(H).min()),
                criterion_check=float(abs(f(th) - fit.neg2ll)))


def dlb_bootstrap(player, ctx, team, y, Xw_base, Xw_adj, x_player, B, seed, start_base=None, start_adj=None):
    """Paired registered-scheme bootstrap of (pooled rho base, pooled rho adjusted, per-context rhos)."""
    rng = np.random.default_rng(seed); P = len(x_player)
    out = np.full((B, 6), np.nan)   # rho_base(2), rho_adj(2), pooled_base, pooled_adj
    for b in range(B):
        pick, idx, newp, tnew = cluster_resample(player, team, P, rng)
        try:
            Xb = Xw_base[idx]; Xb = Xb[:, np.abs(Xb).sum(0) > 0]
            Xa = Xw_adj[idx]; Xa = cf.full_rank(Xa[:, np.abs(Xa).sum(0) > 0])
            rb = cf.h1_reml(newp, ctx[idx], tnew, y[idx], Xb, x_player[pick], start=start_base).rho
            ra = cf.h1_reml(newp, ctx[idx], tnew, y[idx], Xa, x_player[pick], start=start_adj).rho
            out[b] = [rb[0], rb[1], ra[0], ra[1], rb.mean(), ra.mean()]
        except Exception:  # noqa: BLE001
            pass
    return out


# ------------------------------------------------------------------------------------------------ meta-regression
def meta_reml_full(rho, se, D, pos):
    """REML random-effects meta-regression rho_k = alpha_pos(k) + lambda D_k + eta_k, eta_k ~ N(0, se_k^2 + omega^2).
    Same criterion as demand.meta_regression_reml; returns levels, coefficients, covariance, omega^2."""
    levels = sorted(set(pos))
    X = np.column_stack([[1.0 if p == lv else 0.0 for p in pos] for lv in levels] + [np.asarray(D, float)])
    y = np.asarray(rho, float); v = np.asarray(se, float) ** 2

    def neg_reml(lw):
        w = 1 / (v + np.exp(lw)); XtW = X.T * w; A = XtW @ X
        try:
            b = np.linalg.solve(A, XtW @ y)
        except np.linalg.LinAlgError:
            return 1e30
        r = y - X @ b
        return 0.5 * (np.sum(np.log(v + np.exp(lw))) + np.linalg.slogdet(A)[1] + np.sum(w * r ** 2))
    res = optimize.minimize_scalar(neg_reml, bounds=(-12, 2), method="bounded")
    om = float(np.exp(res.x)); w = 1 / (v + om)
    A = (X.T * w) @ X; b = np.linalg.solve(A, (X.T * w) @ y)
    return dict(levels=levels, coef=b, cov=np.linalg.inv(A), omega2=om, lam=float(b[-1]), lam_se=float(np.sqrt(np.linalg.inv(A)[-1, -1])))


def meta_cell_bootstrap(rho, se, D, pos, B, seed):
    """Cell-cluster bootstrap within position (registered): resample cells with replacement inside each position."""
    rng = np.random.default_rng(seed); pos = np.asarray(pos); out = []
    groups = {p: np.where(pos == p)[0] for p in sorted(set(pos))}
    for _ in range(B):
        idx = np.concatenate([rng.choice(g, len(g)) for g in groups.values()])
        Db = np.asarray(D)[idx]
        if np.ptp(Db) < 1e-9:
            continue
        try:
            out.append(meta_reml_full(np.asarray(rho)[idx], np.asarray(se)[idx], Db, pos[idx])["lam"])
        except np.linalg.LinAlgError:
            pass
    return np.array(out)


def holm_adjusted(p: list[float]) -> list[float]:
    """Holm step-down adjusted p-values (monotone)."""
    p = np.asarray(p, float); m = len(p); order = np.argsort(p); adj = np.empty(m); run = 0.0
    for k, i in enumerate(order):
        run = max(run, min(1.0, (m - k) * p[i])); adj[i] = run
    return adj.tolist()
