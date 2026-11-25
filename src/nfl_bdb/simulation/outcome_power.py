"""Phase 17: power simulation for a possible WR route-launch x context-adjusted separation study.

Simulation only: every nuisance value is a previously documented aggregate (Phases 3, 3.5, 4, 16) or an exposure /
team-season COUNT of the eligible population; no outcome value is read.

Latent model (full pre-selection population of N players):
  (T, F10, F40) ~ N(0, Sigma)                       T = true route-launch score; F = true official sprint times
  b = g F40 + rho sqrt(1-g^2) T_perp + sqrt((1-g^2)(1-rho^2)) e     rho = true partial corr(T, b | F10, F40)
Selection: E = lam b + sqrt(1-lam^2) eta; the top n_elig of N on E are eligible (exposure linked to ability);
eligible players receive the observed exposure counts n_i (routes) and team-season counts k_i, larger counts going to
larger E when lam > 0.
Observed: y_i = b_i + team noise (variance tau*s2b/k_i) + sampling noise (sigma_w^2/n_i), with s2b solved so the
mean reliability of y over eligible players equals R_y; X_i = sqrt(R_x,i) T_i + sqrt(1 - R_x,i) e (R_x,i constant or
G(n_routes,i)); F observed with reliability R_F.
Analysis: OLS of y on standardised X, F10_obs, F40_obs with HC3 SE; two-sided t test (df n-4); partial r_hat =
t / sqrt(t^2 + df); disattenuated r_hat / sqrt(R_x R_y); Fisher-z 95% CI (SE 1/sqrt(n-5)).
"""
from __future__ import annotations

import numpy as np
from scipy import stats


def _solve_s2b(R_y, n_i, k_i, tau, s2w):
    """Player true variance giving mean reliability R_y; returns nan if unattainable."""
    def mean_rel(s2b):
        return np.mean(s2b / (s2b + tau * s2b / k_i + s2w / n_i))
    lo, hi = 1e-8, 10.0
    if mean_rel(hi) < R_y:
        return np.nan
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        if mean_rel(mid) < R_y:
            lo = mid
        else:
            hi = mid
    return hi


def _batched_ols_hc3(X, y):
    """X: (R, n, p), y: (R, n). Returns beta (R, p) and HC3 SE (R, p)."""
    XtX = np.einsum("rni,rnj->rij", X, X)
    XtXi = np.linalg.inv(XtX)
    b = np.einsum("rij,rnj,rn->ri", XtXi, X, y)
    e = y - np.einsum("rni,ri->rn", X, b)
    h = np.einsum("rni,rij,rnj->rn", X, XtXi, X)
    w = (e / (1 - h)) ** 2
    meat = np.einsum("rni,rn,rnj->rij", X, w, X)
    cov = np.einsum("rij,rjk,rkl->ril", XtXi, meat, XtXi)
    return b, np.sqrt(np.einsum("rii->ri", cov))


def simulate_cell(rho, *, N, n_elig, counts, team_counts, R_y, R_x, R_F=0.90, g=0.0, lam=0.0, tau=1.10,
                  s2w=1.85 ** 2, corr_T_F10=-0.2, corr_T_F40=-0.15, corr_F=0.85, reps=2000, rng=None, n_routes=None,
                  g_components=None, one_covariate=False):
    """Simulate `reps` datasets. R_x: float, or 'actual' with n_routes/g_components (s2p, s2pr, s2e)."""
    rng = rng or np.random.default_rng(0)
    counts = np.sort(np.asarray(counts, float)); team_counts = np.sort(np.asarray(team_counts, float))
    s2b = _solve_s2b(R_y, counts, team_counts, tau, s2w)
    if not np.isfinite(s2b):
        return dict(feasible=False)
    if one_covariate:
        S = np.array([[1, corr_T_F40], [corr_T_F40, 1]])
    else:
        S = np.array([[1, corr_T_F10, corr_T_F40], [corr_T_F10, 1, corr_F], [corr_T_F40, corr_F, 1]])
    Lc = np.linalg.cholesky(S)
    Z = rng.standard_normal((reps, N, S.shape[0])) @ Lc.T
    T = Z[..., 0]; Fs = Z[..., 1:]
    # T_perp: residual of T on F (population coefficients), standardised
    Sff = S[1:, 1:]; sTf = S[0, 1:]; coef = np.linalg.solve(Sff, sTf)
    Tp = T - Fs @ coef; Tp = Tp / np.sqrt(1 - sTf @ coef)
    F40 = Fs[..., -1]
    b = g * F40 + rho * np.sqrt(1 - g ** 2) * Tp + np.sqrt((1 - g ** 2) * (1 - rho ** 2)) * rng.standard_normal((reps, N))
    E = lam * b + np.sqrt(1 - lam ** 2) * rng.standard_normal((reps, N))
    order = np.argsort(-E, axis=1)[:, :n_elig]
    take = lambda A: np.take_along_axis(A, order, axis=1)  # noqa: E731
    b_e, T_e, F_e = take(b), take(T), np.stack([take(Fs[..., j]) for j in range(Fs.shape[-1])], -1)
    # exposure: if lam > 0 eligible players are already ordered by E (descending); give them descending counts
    n_i = np.tile(counts[::-1][:n_elig], (reps, 1)); k_i = np.tile(team_counts[::-1][:n_elig], (reps, 1))
    if lam == 0:
        perm = np.argsort(rng.random((reps, n_elig)), axis=1)
        n_i = np.take_along_axis(n_i, perm, axis=1); k_i = np.take_along_axis(k_i, perm, axis=1)
    noise_sd = np.sqrt(tau * s2b / k_i + s2w / n_i)
    y = np.sqrt(s2b) * b_e + noise_sd * rng.standard_normal((reps, n_elig))
    if isinstance(R_x, str):
        s2p, s2pr, s2e = g_components
        nr = rng.choice(n_routes, size=(reps, n_elig))
        rx = s2p / (s2p + (s2pr + s2e) / nr)
    else:
        rx = np.full((reps, n_elig), float(R_x))
    X = np.sqrt(rx) * T_e + np.sqrt(1 - rx) * rng.standard_normal((reps, n_elig))
    Fo = np.sqrt(R_F) * F_e + np.sqrt(1 - R_F) * rng.standard_normal(F_e.shape)
    std = lambda A: (A - A.mean(1, keepdims=True)) / A.std(1, keepdims=True)  # noqa: E731
    D = np.concatenate([np.ones((reps, n_elig, 1)), std(X)[..., None], np.stack([std(Fo[..., j]) for j in range(Fo.shape[-1])], -1)], -1)
    beta, se = _batched_ols_hc3(D, y)
    df = n_elig - D.shape[-1]
    t = beta[:, 1] / se[:, 1]
    crit = stats.t.ppf(0.975, df)
    r_hat = t / np.sqrt(t ** 2 + df)
    rx_mean = float(rx.mean())
    r_dis = r_hat / np.sqrt(rx_mean * R_y)
    z = np.arctanh(np.clip(r_hat, -0.999, 0.999)); sez = 1 / np.sqrt(n_elig - 3 - (D.shape[-1] - 2))
    lo, hi = np.tanh(z - 1.96 * sez), np.tanh(z + 1.96 * sez)
    lo_d, hi_d = lo / np.sqrt(rx_mean * R_y), hi / np.sqrt(rx_mean * R_y)
    return dict(feasible=True, s2b=float(s2b), power_two_sided=float(np.mean(np.abs(t) > crit)),
                power_directional=float(np.mean(t > crit)), mean_r_hat=float(r_hat.mean()), bias_r_hat=float(r_hat.mean() - rho),
                mean_r_disattenuated=float(np.mean(r_dis)), bias_r_disattenuated=float(np.mean(r_dis) - rho),
                coverage_naive=float(np.mean((lo <= rho) & (rho <= hi))), coverage_disattenuated=float(np.mean((lo_d <= rho) & (rho <= hi_d))),
                sd_r_hat=float(r_hat.std()), rx_mean=rx_mean)


def mde(effects, powers, target=0.8):
    e = np.asarray(effects, float); p = np.asarray(powers, float)
    for i in range(1, len(e)):
        if p[i - 1] < target <= p[i]:
            return float(e[i - 1] + (target - p[i - 1]) * (e[i] - e[i - 1]) / (p[i] - p[i - 1]))
    return float(e[0]) if p[0] >= target else np.nan
