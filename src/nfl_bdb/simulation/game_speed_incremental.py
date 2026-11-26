"""Phase 19: synthetic power study -- does tracked Combine peak speed add information beyond the official 40
for WR game speed (H1 outcome, deep + short composite)? Simulation only; no outcome value is used.

Latent model (standardised true scores):
  S_F  true official-40 speed (sign: higher = faster), S_P true tracked peak speed,
  S_P = rho* S_F + sqrt(1 - rho*^2) S_perp,   rho* = r_obs / sqrt(R_F * mean R_P)
  L   = a S_F + pi sqrt(1 - a^2) S_perp + sqrt((1 - a^2)(1 - pi^2)) u      -> pi = true partial corr(L, S_P | S_F)
  composite true game-speed level  bbar = sd_bar * L ;  context effects b_deep / b_short reproduce the outcome-only
  Phase 4 Sigma_b exactly (bbar = mean of the two; difference d regressed on bbar).
Observed: F_o = sqrt(R_F) S_F + e, P_o = sqrt(R_P,i) S_P + e (R_P,i 0.94 best-of-2, 0.89 single attempt);
  m_ic = b_ic + sum_t w_ict tau_t + N(0, s2_c / n_ic)  with the real per-player x context x team-season play counts.
Analyses (player level only):
  E1 observed-scale incremental coefficient of P given F: WLS two-stage + HC3 (identical to the frozen
     confirmatory.wls_two_stage with n_eff = 1 / v_i, sw2 = 1);
  E2 player-grouped K-fold CV of M1 (F), M2 (P), M3 (F + P) on held-out players' shrunken levels (as frozen h2_cv);
  E4 EIV regression calibration (as frozen confirmatory.eiv_two_stage) under an assumed R_F.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

SIGMA_B = np.array([[0.0616, 0.0557], [0.0557, 0.0849]])
S2_TEAM = 0.0104
S2_RESID = np.array([0.761, 1.455])


@dataclass
class Design:
    n: np.ndarray        # (P, 2) plays per player x context
    W: np.ndarray        # (2, P, T) team-season weights n_ict / n_ic
    R_P: np.ndarray      # (P,) reliability of the observed peak (by number of valid attempts)

    @property
    def P(self):
        return self.n.shape[0]

    def resample(self, n_players, rng):
        i = rng.integers(0, self.P, n_players)
        return Design(self.n[i], self.W[:, i, :], self.R_P[i])


def composite_parts(design: Design):
    """Sampling variance of the composite mean (used by the analyst) and its team-season loading."""
    v = (S2_RESID[0] / design.n[:, 0] + S2_RESID[1] / design.n[:, 1]) / 4
    wbar = (design.W[0] + design.W[1]) / 2
    return v, wbar


def composite_reliability(design: Design):
    v, wbar = composite_parts(design)
    s2bar = SIGMA_B.sum() / 4
    team = S2_TEAM * (wbar ** 2).sum(1)
    return float(np.mean(s2bar / (s2bar + v + team))), float(np.mean(s2bar / (s2bar + v)))


def population_targets(a, pi, R_F, R_P_mean, r_obs):
    """Population regression of the true composite on standardised observed (F, P), and on true scores
    expressed in observed-SD units (the EIV target), in yd/s per SD."""
    rho = r_obs / np.sqrt(R_F * R_P_mean)
    c = pi * np.sqrt(1 - a ** 2)
    sd = np.sqrt(SIGMA_B.sum() / 4)
    cv = sd * np.array([a * np.sqrt(R_F), np.sqrt(R_P_mean) * (a * rho + c * np.sqrt(1 - rho ** 2))])
    S_o = np.array([[1, r_obs], [r_obs, 1]])
    S_t = np.array([[R_F, r_obs], [r_obs, R_P_mean]])
    return np.linalg.solve(S_o, cv), np.linalg.solve(S_t, cv), rho


def _std(A):
    return (A - A.mean(1, keepdims=True)) / A.std(1, ddof=1, keepdims=True)


def _wls_hc3(X, y, w):
    """Batched weighted LS with HC3 SEs, identical to confirmatory.wls_two_stage. X (R, n, p), y (R, n), w (R, n)."""
    Wx = X * w[..., None]
    XtWXi = np.linalg.inv(np.einsum("rni,rnj->rij", X, Wx))
    b = np.einsum("rij,rnj,rn->ri", XtWXi, Wx, y)
    e = y - np.einsum("rni,ri->rn", X, b)
    h = np.einsum("rni,rij,rnj->rn", Wx, XtWXi, X)
    u = X * (w * e / (1 - h))[..., None]
    cov = np.einsum("rij,rnj,rnk,rkl->ril", XtWXi, u, u, XtWXi)
    return b, np.sqrt(np.einsum("rii->ri", cov))


def _ols_pred(Xtr, ytr, Xte):
    beta = np.linalg.solve(np.einsum("rni,rnj->rij", Xtr, Xtr), np.einsum("rni,rn->ri", Xtr, ytr)[..., None])[..., 0]
    return np.einsum("rni,ri->rn", Xte, beta)


def cv_delta_r2(m, v, F, Pk, rng, folds=10, repeats=5):
    """Player-grouped CV (frozen h2_cv logic, player level): returns (R, 3) mean R^2 of M1, M2, M3."""
    R, n = m.shape
    out = np.zeros((R, 3))
    for _ in range(repeats):
        fid = np.empty(n, int); fid[rng.permutation(n)] = np.arange(n) % folds
        pred = np.zeros((3, R, n)); target = np.zeros((R, n)); mu_te = np.zeros((R, n))
        for f in range(folds):
            te = np.where(fid == f)[0]; tr = np.where(fid != f)[0]
            mtr, vtr, mte, vte = m[:, tr], v[:, tr], m[:, te], v[:, te]
            s2b = np.maximum(mtr.var(1, ddof=1) - vtr.mean(1), 1e-6)[:, None]
            ktr = s2b / (s2b + vtr); kte = s2b / (s2b + vte)
            mu = (mtr * ktr).sum(1, keepdims=True) / ktr.sum(1, keepdims=True)
            ttr = mu + ktr * (mtr - mu); target[:, te] = mu + kte * (mte - mu); mu_te[:, te] = mu
            z = []
            for A in (F, Pk):
                mA, sA = A[:, tr].mean(1, keepdims=True), A[:, tr].std(1, ddof=1, keepdims=True)
                z.append(((A[:, tr] - mA) / sA, (A[:, te] - mA) / sA))
            one_tr, one_te = np.ones((R, len(tr))), np.ones((R, len(te)))
            for k, cols in enumerate(((0,), (1,), (0, 1))):
                Xtr = np.stack([one_tr] + [z[j][0] for j in cols], -1); Xte = np.stack([one_te] + [z[j][1] for j in cols], -1)
                pred[k][:, te] = _ols_pred(Xtr, ttr, Xte)
        sst = ((target - mu_te) ** 2).sum(1)
        for k in range(3):
            out[:, k] += 1 - ((target - pred[k]) ** 2).sum(1) / sst
    return out / repeats


def simulate_cell(design: Design, *, a, pi, R_F, r_obs=0.851, reps=2000, rng=None, R_F_assumed=(0.95,),
                  folds=10, cv_repeats=5, do_cv=True):
    rng = rng or np.random.default_rng(0)
    P = design.P
    R_P_mean = float(design.R_P.mean())
    rho = min(r_obs / np.sqrt(R_F * R_P_mean), 0.9995)
    SF = rng.standard_normal((reps, P)); Sp = rng.standard_normal((reps, P))
    SP = rho * SF + np.sqrt(1 - rho ** 2) * Sp
    c = pi * np.sqrt(1 - a ** 2)
    L = a * SF + c * Sp + np.sqrt((1 - a ** 2) * (1 - pi ** 2)) * rng.standard_normal((reps, P))
    s2bar = SIGMA_B.sum() / 4
    cov_bd = (SIGMA_B[0, 0] - SIGMA_B[1, 1]) / 2; var_d = SIGMA_B[0, 0] + SIGMA_B[1, 1] - 2 * SIGMA_B[0, 1]
    bbar = np.sqrt(s2bar) * L
    d = (cov_bd / s2bar) * bbar + np.sqrt(var_d - cov_bd ** 2 / s2bar) * rng.standard_normal((reps, P))
    b = np.stack([bbar + d / 2, bbar - d / 2], 0)                                   # (2, R, P)
    T = design.W.shape[2]
    tau = np.sqrt(S2_TEAM) * rng.standard_normal((reps, T))
    m_c = b + np.einsum("cpt,rt->crp", design.W, tau) + np.sqrt(S2_RESID[:, None, None] / design.n.T[:, None, :]) * rng.standard_normal((2, reps, P))
    m = m_c.mean(0)
    v_i, _ = composite_parts(design); v = np.broadcast_to(v_i, (reps, P))
    Fo = np.sqrt(R_F) * SF + np.sqrt(1 - R_F) * rng.standard_normal((reps, P))
    Po = np.sqrt(design.R_P) * SP + np.sqrt(1 - design.R_P) * rng.standard_normal((reps, P))
    # E1: WLS two-stage (frozen weights rule) + HC3
    s2b_hat = np.maximum(m.var(1, ddof=1) - v.mean(1), 0.05 * m.var(1, ddof=1))
    w = 1 / (s2b_hat[:, None] + v)
    X = np.stack([np.ones((reps, P)), _std(Fo), _std(Po)], -1)
    beta, se = _wls_hc3(X, m, w)
    df = P - 3
    t = beta[:, 2] / se[:, 2]; crit = stats.t.ppf(0.975, df)
    b_obs, b_true, _ = population_targets(a, pi, R_F, R_P_mean, r_obs)
    lo, hi = beta[:, 2] - crit * se[:, 2], beta[:, 2] + crit * se[:, 2]
    r_partial = t / np.sqrt(t ** 2 + df)
    res = dict(a=a, pi=pi, R_F=R_F, rho_star=float(rho), n=P, beta_P_pop_obs=float(b_obs[1]), beta_P_pop_true=float(b_true[1]),
               power=float(np.mean(np.abs(t) > crit)), mean_beta_P=float(beta[:, 2].mean()),
               bias_beta_P=float(beta[:, 2].mean() - b_obs[1]), coverage_obs=float(np.mean((lo <= b_obs[1]) & (b_obs[1] <= hi))),
               ci_halfwidth=float(np.median(crit * se[:, 2])), mean_partial_r=float(r_partial.mean()), sd_partial_r=float(r_partial.std()),
               sd_level=float(np.sqrt(s2bar)))
    # E4: EIV under assumed R_F (frozen eiv_two_stage rule; covariance of the outcome with standardised W)
    Wz = np.stack([_std(Fo), _std(Po)], -1)
    Sw = np.einsum("rni,rnj->rij", Wz - Wz.mean(1, keepdims=True), Wz - Wz.mean(1, keepdims=True)) / (P - 1)
    cw = np.einsum("rni,rn->ri", Wz - Wz.mean(1, keepdims=True), m - m.mean(1, keepdims=True)) / (P - 1)
    for RFa in tuple(R_F_assumed) + (R_F,):
        St = Sw.copy(); St[:, 0, 0] -= (1 - RFa) * Sw[:, 0, 0]; St[:, 1, 1] -= (1 - R_P_mean) * Sw[:, 1, 1]
        e = np.linalg.solve(St, cw[..., None])[..., 0][:, 1]
        key = "true" if RFa == R_F else f"{RFa:.2f}"
        res[f"eiv_beta_P_mean_assumed_{key}"] = float(np.median(e))
    if do_cv:
        r2 = cv_delta_r2(m, v, Fo, Po, rng, folds, cv_repeats)
        d31 = r2[:, 2] - r2[:, 0]; d21 = r2[:, 1] - r2[:, 0]
        res.update(r2_m1=float(r2[:, 0].mean()), r2_m2=float(r2[:, 1].mean()), r2_m3=float(r2[:, 2].mean()),
                   dr2_m3_m1=float(d31.mean()), dr2_m3_m1_sd=float(d31.std()), p_dr2_pos=float(np.mean(d31 > 0)),
                   p_dr2_ge_002=float(np.mean(d31 >= 0.02)), dr2_m2_m1=float(d21.mean()))
    return res


def mde(effects, powers, target=0.8):
    e = np.asarray(effects, float); p = np.asarray(powers, float)
    for i in range(1, len(e)):
        if p[i - 1] < target <= p[i]:
            return float(e[i - 1] + (target - p[i - 1]) * (e[i] - e[i - 1]) / (p[i] - p[i - 1]))
    return float(e[0]) if p[0] >= target else float("nan")
