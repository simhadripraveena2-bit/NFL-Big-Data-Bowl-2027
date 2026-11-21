"""Semi-synthetic data generator for Phase 4 pipeline validation.

The *design* of every synthetic dataset is real: the actual eligible players, their plays per context,
team-season membership, routes, coverages, downs, seasons and NFL experience (a "skeleton" built from
REG-season player_play + tracking features, outcome-free). Only the outcome and the combine predictors
are synthetic. Nuisance parameters (fixed covariate effects, player covariance, team-season variance,
residual variances) come from outcome-only REML fits on real data (no combine data involved).

H1 data-generating process for one position (contexts h = 0, l = 1):
    z_i ~ capacity, z = r_dep * dep_i + sqrt(1 - r_dep^2) e_i        (dep_i = standardised real deployment share)
    true player-context level  l_ic = sqrt(Sb_cc) * (rho_c z_i + sqrt(1 - rho_c^2) u_ic),  corr(u_ih, u_il) = r_u
    y_ij = mu_hat_ij (real fixed effects) + l_i c(ij) + tau_t(ij) + eps_ij,  eps ~ N(0, s2_c) or real residual pool
    x_i = sqrt(R_x) z_i + sqrt(1 - R_x) e'_i                            (tracked peak, measurement error)
Truth: Delta = (rho_h - rho_l) * sqrt(R_x) is the target of the registered estimator (correlation with the
OBSERVED x); rho_c itself is reported as the estimand after the 1/sqrt(R_x) correction.
Options: deployment-only confounding through route mix (`route_confound`), selection on the outcome
(`sel_outcome`), thinning the low-demand context (`thin_low`) for differential measurement error.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl


@dataclass
class H1Truth:
    rho_h: float
    rho_l: float
    rel_x: float

    @property
    def delta_obs_scale(self):
        return (self.rho_h - self.rho_l) * np.sqrt(self.rel_x)


def _ru(c_true, rh, rl):
    den = np.sqrt((1 - rh ** 2) * (1 - rl ** 2))
    return float(np.clip((c_true - rh * rl) / den, -0.99, 0.99)) if den > 0 else 0.0


def simulate_h1(skel: pl.DataFrame, par: dict, rho_h: float, rho_l: float, rng, rel_x=0.987, r_dep=0.3,
                route_confound=0.0, sel_outcome=0.0, sel_capacity=0.0, thin_low=1.0, resid_pool=None, players_subset=None):
    """Return (play arrays dict, x_obs per player, truth). skel columns: pid (0..P-1), ctx_i, team_i, mu_hat,
    dep_std (player deployment share, standardised), go_share_std, route_ran, lr_std (log routes, std),
    eligible (bool)."""
    P = int(skel["pid"].max()) + 1
    pp = skel.group_by("pid").agg(pl.col("dep_std").first(), pl.col("go_share_std").first(), pl.col("lr_std").first(),
                                  pl.col("eligible").first()).sort("pid")
    dep = pp["dep_std"].to_numpy(); go = pp["go_share_std"].to_numpy(); lr = pp["lr_std"].to_numpy()
    z = r_dep * dep + np.sqrt(1 - r_dep ** 2) * rng.standard_normal(P)
    if sel_capacity:     # playing time (log routes) correlated with capacity itself
        z = (z + sel_capacity * lr) / np.sqrt(1 + sel_capacity ** 2)
    if route_confound:   # capacity also drives WHICH deep routes a player runs (GO share)
        z = (z + route_confound * go) / np.sqrt(1 + route_confound ** 2)
    Sb = np.asarray(par["sigma_b"]); c_true = Sb[0, 1] / np.sqrt(Sb[0, 0] * Sb[1, 1])
    ru = _ru(c_true, rho_h, rho_l)
    u1 = rng.standard_normal(P); u2 = ru * u1 + np.sqrt(1 - ru ** 2) * rng.standard_normal(P)
    if sel_outcome:      # playing time (log routes) correlated with the high-demand residual level u1
        u1 = (u1 + sel_outcome * lr) / np.sqrt(1 + sel_outcome ** 2)
        u2 = ru * u1 + np.sqrt(1 - ru ** 2) * rng.standard_normal(P)
    lev = np.column_stack([np.sqrt(Sb[0, 0]) * (rho_h * z + np.sqrt(1 - rho_h ** 2) * u1),
                           np.sqrt(Sb[1, 1]) * (rho_l * z + np.sqrt(1 - rho_l ** 2) * u2)])
    T = int(skel["team_i"].max()) + 1
    tau = rng.normal(0, np.sqrt(par["s2_team"]), T)
    pid = skel["pid"].to_numpy(); ctx = skel["ctx_i"].to_numpy(); team = skel["team_i"].to_numpy()
    s2 = np.asarray(par["s2_resid"])
    if resid_pool is not None:
        eps = np.empty(len(pid))
        for c in range(2):
            k = ctx == c
            eps[k] = rng.choice(resid_pool[c], k.sum())
    else:
        eps = rng.standard_normal(len(pid)) * np.sqrt(s2[ctx])
    y = skel["mu_hat"].to_numpy() + lev[pid, ctx] + tau[team] + eps
    keep = np.ones(len(pid), bool)
    if thin_low < 1.0:
        keep &= ~((ctx == 1) & (rng.random(len(pid)) > thin_low))
    x = np.sqrt(rel_x) * z + np.sqrt(1 - rel_x) * rng.standard_normal(P)
    return dict(y=y, keep=keep), x, H1Truth(rho_h, rho_l, rel_x), z


def simulate_h2(skel: pl.DataFrame, par: dict, partial: float, rng, rho_forty=0.3, r_obs=0.814, rel_F=0.95,
                rel_x=0.987, resid_pool=None):
    """Deep-route separation. True 40 speed F and peak P (corr r = r_obs / sqrt(rel_F rel_x));
    true player level t = sqrt(s2b) [a F + b P_perp + sqrt(1 - a^2 - b^2) w], b = partial sqrt(1 - a^2)."""
    P = int(skel["pid"].max()) + 1
    r = min(r_obs / np.sqrt(rel_F * rel_x), 0.99)
    F = rng.standard_normal(P); Pp = rng.standard_normal(P); Pk = r * F + np.sqrt(1 - r ** 2) * Pp
    a = rho_forty; b = partial * np.sqrt(1 - a ** 2)
    t = np.sqrt(par["s2b"]) * (a * F + b * Pp + np.sqrt(max(1 - a ** 2 - b ** 2, 0)) * rng.standard_normal(P))
    T = int(skel["team_i"].max()) + 1
    tau = rng.normal(0, np.sqrt(par["s2_team"]), T)
    pid = skel["pid"].to_numpy(); team = skel["team_i"].to_numpy()
    eps = rng.choice(resid_pool, len(pid)) if resid_pool is not None else rng.standard_normal(len(pid)) * np.sqrt(par["s2"])
    y = skel["mu_hat"].to_numpy() + t[pid] + tau[team] + eps
    Fo = np.sqrt(rel_F) * F + np.sqrt(1 - rel_F) * rng.standard_normal(P)
    xo = np.sqrt(rel_x) * Pk + np.sqrt(1 - rel_x) * rng.standard_normal(P)
    return y, Fo, xo, dict(partial=partial, rho_forty=rho_forty, rel_F=rel_F, rel_x=rel_x)
