"""Simulation-based power analysis for the Phase 3.5 pre-registered tests.

The data-generating process mirrors the pre-registered estimands:

H1 / H5 (task-conditioned translation, one position, two task contexts h = high demand, l = low):
    z_i ~ N(0, 1)                                   true combine speed capacity (standardised)
    x_i = sqrt(R_x) z_i + sqrt(1 - R_x) e_i          observed tracked peak speed (R_x = 0.987)
    m_ic = sqrt(V_c) (rho_c z_i + sqrt(1 - rho_c^2) u_ic),  corr(u_ih, u_il) = r_u
                                                    true context-specific player mean (context-adjusted)
    mbar_ic = m_ic + mean of n_ic within-player residuals (SD sigma_c)
  Estimand: Delta = rho_h - rho_l, the difference between two *disattenuated* within-position
  correlations of capacity with the true player-context means. r_u is chosen so the true
  cross-context correlation equals its calibrated value.
  Estimator (moment form of the pre-registered mixed model):
    rho_hat_c = cov(x, mbar_c) / (sd(x) sqrt(V_hat_c)),  V_hat_c = var(mbar_c) - mean(sigma_c^2 / n_ic)
  Test: player-cluster percentile bootstrap CI for Delta_hat; reject if the CI excludes 0 with
  Delta_hat > 0. Independent players are the resampling unit: plays never add independent units.

H2 (incremental value of tracked peak speed over the official 40, WR deep routes):
    (F, P) true 40-speed and peak speed, corr r = r_obs / sqrt(R_F R_P)
    t_i = a F_i + b P_perp_i + sqrt(1 - a^2 - b^2) w_i,  P_perp = (P - r F) / sqrt(1 - r^2)
          a = rho_forty, b = partial * sqrt(1 - a^2)  (partial = true partial correlation of P with t | F)
    s_i = sqrt(V_deep) t_i + mean of n_i deep-route residuals (SD sigma_deep)
  Test: OLS s ~ F_obs + P_obs with HC3 SE; reject if the P_obs coefficient is > 0 and significant.
  Also: leave-one-player-out Delta R^2 (closed-form PRESS).
"""
from __future__ import annotations

import numpy as np
from scipy import stats


def holm_first_alpha(alpha: float, m: int) -> float:
    """Most stringent Holm step (the level a single surviving test must pass in the worst case)."""
    return alpha / m


def _draw_counts(counts: np.ndarray, n_players: int, play_scale: float, rng) -> np.ndarray:
    idx = rng.integers(0, len(counts), n_players)
    return np.maximum(1, np.round(counts[idx] * play_scale)).astype(int)


def _solve_ru(c_true: float, rh: float, rl: float) -> float:
    den = np.sqrt((1 - rh ** 2) * (1 - rl ** 2))
    return float(np.clip((c_true - rh * rl) / den, -0.99, 0.99)) if den > 0 else 0.0


def _batched_rho(x: np.ndarray, m: np.ndarray, sv: np.ndarray) -> np.ndarray:
    """Disattenuated correlation along the last axis. x, m: (..., n); sv: (..., n) sampling variance."""
    xc = x - x.mean(-1, keepdims=True); mc = m - m.mean(-1, keepdims=True)
    n = x.shape[-1]
    cov = (xc * mc).sum(-1) / (n - 1)
    vx = (xc ** 2).sum(-1) / (n - 1)
    vm = (mc ** 2).sum(-1) / (n - 1)
    vtrue = np.maximum(vm - sv.mean(-1), 0.05 * vm)
    return cov / np.sqrt(vx * vtrue), cov / np.sqrt(vx * vm)


def power_h1(vc: dict, rho_high: float, rho_low: float, n_sims: int, n_boot: int, rng, alphas=(0.05,),
             peak_rel: float = 0.987, n_players: int | None = None, play_scale: float = 1.0,
             play_level: bool = False, resid: dict | None = None, batch: int = 100) -> dict:
    ctxs = vc["contexts"]; counts = np.asarray(vc["counts"])
    V = np.asarray(vc["var_between"]); sw = np.asarray(vc["sd_within"])
    n = n_players or vc["n_players"]
    ru = _solve_ru(vc["corr_between_true"], rho_high, rho_low)
    rhos = np.array([rho_high, rho_low])
    est, est_raw, rej, rej_raw, cover = [], [], {a: 0 for a in alphas}, {a: 0 for a in alphas}, 0
    done = 0
    while done < n_sims:
        S = min(batch, n_sims - done)
        z = rng.standard_normal((S, n))
        x = np.sqrt(peak_rel) * z + np.sqrt(1 - peak_rel) * rng.standard_normal((S, n))
        u1 = rng.standard_normal((S, n)); u2 = ru * u1 + np.sqrt(1 - ru ** 2) * rng.standard_normal((S, n))
        U = np.stack([u1, u2], 1)                                     # (S, 2, n)
        m = np.sqrt(V)[None, :, None] * (rhos[None, :, None] * z[:, None, :] + np.sqrt(1 - rhos ** 2)[None, :, None] * U)
        N = np.stack([_draw_counts(counts[:, k], S * n, play_scale, rng).reshape(S, n) for k in range(2)], 1)
        sv = (sw[None, :, None] ** 2) / N
        if play_level:
            noise = np.empty_like(m)
            for k, c in enumerate(ctxs):
                tot = N[:, k, :].ravel()
                pool = resid[c] if resid is not None else None
                draws = (rng.choice(pool, tot.sum()) if pool is not None else rng.standard_normal(tot.sum()) * sw[k])
                starts = np.concatenate([[0], np.cumsum(tot)[:-1]])
                noise[:, k, :] = (np.add.reduceat(draws, starts) / tot).reshape(S, n)
            mbar = m + noise
        else:
            mbar = m + rng.standard_normal(m.shape) * np.sqrt(sv)
        r_h, rr_h = _batched_rho(x, mbar[:, 0], sv[:, 0]); r_l, rr_l = _batched_rho(x, mbar[:, 1], sv[:, 1])
        d_hat = r_h - r_l; d_raw = rr_h - rr_l
        # cluster bootstrap over players
        bi = rng.integers(0, n, (S, n_boot, n))
        take = lambda a: np.take_along_axis(a[:, None, :].repeat(n_boot, 1), bi, 2)  # noqa: E731
        xb = take(x)
        bh, bhr = _batched_rho(xb, take(mbar[:, 0]), take(sv[:, 0]))
        bl, blr = _batched_rho(xb, take(mbar[:, 1]), take(sv[:, 1]))
        bd = bh - bl; bdr = bhr - blr
        for a in alphas:
            lo = np.percentile(bd, 100 * a / 2, axis=1); lo_r = np.percentile(bdr, 100 * a / 2, axis=1)
            rej[a] += int(((lo > 0) & (d_hat > 0)).sum()); rej_raw[a] += int(((lo_r > 0) & (d_raw > 0)).sum())
        lo95 = np.percentile(bd, 2.5, axis=1); hi95 = np.percentile(bd, 97.5, axis=1)
        target = (rho_high - rho_low) * np.sqrt(peak_rel)
        cover += int(((lo95 <= target) & (hi95 >= target)).sum())
        est.append(d_hat); est_raw.append(d_raw); done += S
    est = np.concatenate(est); est_raw = np.concatenate(est_raw)
    out = dict(mean_delta_hat=float(np.nanmean(est)), sd_delta_hat=float(np.nanstd(est)),
               mean_delta_raw=float(np.nanmean(est_raw)), sd_delta_raw=float(np.nanstd(est_raw)),
               coverage95=cover / n_sims, r_u=ru)
    for a in alphas:
        out[f"power_a{a:.4f}"] = rej[a] / n_sims
        out[f"power_raw_a{a:.4f}"] = rej_raw[a] / n_sims
    return out


def _ols_hc3(X: np.ndarray, y: np.ndarray):
    XtXi = np.linalg.inv(X.T @ X)
    b = XtXi @ X.T @ y
    e = y - X @ b
    h = np.einsum("ij,jk,ik->i", X, XtXi, X)
    meat = (X * (e / (1 - h))[:, None] ** 2).T @ X
    cov = XtXi @ meat @ XtXi
    press = ((e / (1 - h)) ** 2).sum()
    return b, np.sqrt(np.diag(cov)), press


def power_h2(vc: dict, r_obs_peak_forty: float, forty_rel: float, peak_rel: float, rho_forty: float, partial: float,
             n_sims: int, rng, alphas=(0.05,), n_players: int | None = None) -> dict:
    counts = np.asarray(vc["counts"])[:, 0]
    V = vc["var_between"][0]; sw = vc["sd_within"][0]
    n = n_players or vc["n_players"]
    r = min(r_obs_peak_forty / np.sqrt(forty_rel * peak_rel), 0.99)
    a = rho_forty; b = partial * np.sqrt(1 - a ** 2)
    res_sd = np.sqrt(max(1 - a ** 2 - b ** 2, 0))
    rej = {al: 0 for al in alphas}; coefs, dr2 = [], []
    for _ in range(n_sims):
        F = rng.standard_normal(n); Pp = rng.standard_normal(n); P = r * F + np.sqrt(1 - r ** 2) * Pp
        t = a * F + b * Pp + res_sd * rng.standard_normal(n)
        k = _draw_counts(counts, n, 1.0, rng)
        s = np.sqrt(V) * t + rng.standard_normal(n) * sw / np.sqrt(k)
        Fo = np.sqrt(forty_rel) * F + np.sqrt(1 - forty_rel) * rng.standard_normal(n)
        Po = np.sqrt(peak_rel) * P + np.sqrt(1 - peak_rel) * rng.standard_normal(n)
        X = np.column_stack([np.ones(n), Fo, Po])
        bb, se, press_f = _ols_hc3(X, s)
        _, _, press_r = _ols_hc3(X[:, :2], s)
        tval = bb[2] / se[2]
        for al in alphas:
            rej[al] += int((tval > stats.t.ppf(1 - al / 2, n - 3)))
        coefs.append(bb[2] / np.sqrt(V)); dr2.append((press_r - press_f) / ((s - s.mean()) ** 2).sum())
    dr2 = np.asarray(dr2)
    out = dict(mean_std_coef=float(np.mean(coefs)), sd_std_coef=float(np.std(coefs)), mean_loo_dR2=float(dr2.mean()), p_loo_dR2_pos=float((dr2 > 0).mean()),
               r_true_peak_forty=r)
    for al in alphas:
        out[f"power_a{al:.4f}"] = rej[al] / n_sims
    return out


def mde(xs, powers, target=0.8):
    """Linear interpolation of the smallest effect reaching the target power (nan if never)."""
    xs = np.asarray(xs, float); ps = np.asarray(powers, float)
    o = np.argsort(xs); xs, ps = xs[o], ps[o]
    for i in range(len(xs)):
        if ps[i] >= target:
            if i == 0:
                return float(xs[0])
            return float(xs[i - 1] + (target - ps[i - 1]) * (xs[i] - xs[i - 1]) / (ps[i] - ps[i - 1]))
    return float("nan")
