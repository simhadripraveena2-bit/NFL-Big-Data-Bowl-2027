"""Near-top-speed task demand D(p, c) (preregistration §3.3).

Registered primary definition (frozen):
    T_i      = mean of player i's 5 largest REG play maxima (`vmax_play`) over all his plays
    share_ic = fraction of player i's plays in context c with vmax_play >= 0.90 * T_i
    D(p, c)  = median of share_ic over eligible players of position p
    cross-fitting: random player halves (seed 3503); D from one half is paired with rho from the other.
Sensitivity (not primary): thresholds 0.85 / 0.95; absolute threshold vmax_play >= 7.5 yd/s;
out-of-sample T_i (estimated on the other game-parity half of the player's games).
"""
from __future__ import annotations

import numpy as np
import polars as pl

REGISTERED_THRESHOLD = 0.90
CROSSFIT_SEED = 3503


def player_top5(plays: pl.DataFrame, speed: str = "vmax_play") -> pl.DataFrame:
    return plays.group_by("nfl_id").agg(pl.col(speed).top_k(5).mean().alias("T"))


def player_shares(plays: pl.DataFrame, thresholds=(0.85, 0.90, 0.95), speed: str = "vmax_play",
                  top: pl.DataFrame | None = None, absolute: float | None = 7.5) -> pl.DataFrame:
    """plays: nfl_id, ctx, speed. top: optional externally supplied T per player (for out-of-sample T)."""
    top = top if top is not None else player_top5(plays, speed)
    d = plays.join(top, on="nfl_id")
    aggs = [pl.len().alias("n")] + [(pl.col(speed) >= th * pl.col("T")).mean().alias(f"share_{int(th * 100)}") for th in thresholds]
    if absolute is not None:
        aggs.append((pl.col(speed) >= absolute).mean().alias("share_abs"))
    return d.group_by("nfl_id", "ctx").agg(aggs)


def cell_demand(shares: pl.DataFrame, col: str = "share_90", min_plays: int = 1) -> pl.DataFrame:
    return shares.filter(pl.col("n") >= min_plays).group_by("ctx").agg(pl.col(col).median().alias("D"), pl.len().alias("players"))


def crossfit_halves(player_ids: np.ndarray, seed: int = CROSSFIT_SEED) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    ids = np.sort(np.unique(player_ids))
    perm = rng.permutation(ids)
    h = len(ids) // 2
    return np.sort(perm[:h]), np.sort(perm[h:])


def meta_regression_reml(rho, se, D, pos):
    """REML random-effects meta-regression rho_k = alpha_pos(k) + lambda D_k + eta_k,
    eta_k ~ N(0, se_k^2 + omega^2). Returns lambda, its SE, omega^2."""
    from scipy import optimize
    levels = sorted(set(pos))
    X = np.column_stack([[1.0 if p == lv else 0.0 for p in pos] for lv in levels] + [np.asarray(D, float)])
    y = np.asarray(rho, float); v = np.asarray(se, float) ** 2

    def neg_reml(lw):
        w = 1 / (v + np.exp(lw))
        XtW = X.T * w
        A = XtW @ X
        try:
            b = np.linalg.solve(A, XtW @ y)
        except np.linalg.LinAlgError:
            return 1e30
        r = y - X @ b
        return 0.5 * (np.sum(np.log(v + np.exp(lw))) + np.linalg.slogdet(A)[1] + np.sum(w * r ** 2))

    res = optimize.minimize_scalar(neg_reml, bounds=(-12, 2), method="bounded")
    om = float(np.exp(res.x)); w = 1 / (v + om)
    A = (X.T * w) @ X; b = np.linalg.solve(A, (X.T * w) @ y)
    cov = np.linalg.inv(A)
    return float(b[-1]), float(np.sqrt(cov[-1, -1])), om
