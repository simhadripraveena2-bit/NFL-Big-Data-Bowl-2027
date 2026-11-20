"""Estimators of individual acceleration–speed (A–S) capacity from tracking data.

Model of capacity (Hill–Keller / linear A–S line; Morin et al. 2021, DOI 10.1016/j.jbiomech.2021.110524):
    a_max(v) = A0 * (1 - v / S0)
A0 = theoretical maximal acceleration (yd/s^2), S0 = theoretical maximal speed (yd/s).

Inputs for every estimator: one athlete's frames (speed v, tangential acceleration a, play id),
already restricted to v >= v_min and a > 0, plus an athlete group label for pooling.

Baselines (our implementations; detailed published procedures were known to us from abstracts only):
  * ``fit_max_observed``   — naive: S0 = max speed, A0 = max acceleration.
  * ``fit_binned``         — Morin et al. (2021): max acceleration per 0.2 m/s speed bin from 3 m/s,
                             OLS through the bin maxima.
  * ``fit_binned_ci``      — binned + removal of points outside the 95% prediction band, refit
                             ("CI" rule described by Cormier et al. 2023, DOI 10.1016/j.jbiomech.2023.111724).
  * ``fit_binned_boxplot`` — Tukey upper-fence filtering of frames within each bin before taking the
                             max ("boxplot" rule of Cormier et al. 2023; our reading of the abstract).
  * ``fit_dbscan_binned``  — DBSCAN outlier removal before binning (inspired by Miguens et al. 2024,
                             DOI 10.1186/s40798-023-00672-7; not a replication).
  * ``fit_quantile``       — linear quantile regression at a high quantile (Koenker & Bassett 1978).

Proposed: ``HierarchicalFrontierEstimator`` (HEF) — an exposure-aware stochastic frontier fitted to the
bin maxima with partial pooling (empirical Bayes) and Laplace uncertainty. See ``fit`` docstring.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import log_ndtr

YD_PER_M = 1 / 0.9144
V_MIN = 3.0 * YD_PER_M          # 3 m/s in yd/s (Morin et al. 2021 lower speed bound)
BIN_W = 0.2 * YD_PER_M          # 0.2 m/s bins in yd/s


# ----------------------------------------------------------------------------- helpers
def bin_maxima(v, a, play, v_min=V_MIN, width=BIN_W, return_frames=False):
    """Per speed bin: speed at the max-acceleration frame, the max acceleration, and the number of
    distinct plays contributing frames to the bin (exposure). With ``return_frames`` also the number
    of frames in each bin."""
    m = (v >= v_min) & (a > 0) & np.isfinite(v) & np.isfinite(a)
    v, a, play = v[m], a[m], play[m]
    if len(v) == 0:
        return (np.empty(0),) * (4 if return_frames else 3)
    b = np.floor((v - v_min) / width).astype(int)
    order = np.lexsort((-a, b))
    b_s, v_s, a_s, p_s = b[order], v[order], a[order], play[order]
    first = np.r_[True, b_s[1:] != b_s[:-1]]
    vb, ab = v_s[first], a_s[first]
    ub = b_s[first]
    nb = np.array([len(np.unique(p_s[b_s == k])) for k in ub], dtype=float)
    if return_frames:
        nf = np.array([np.sum(b_s == k) for k in ub], dtype=float)
        return vb, ab, nb, nf
    return vb, ab, nb


def _line_to_params(intercept, slope):
    if not np.isfinite(slope) or slope >= 0 or intercept <= 0:
        return np.nan, np.nan
    return intercept, -intercept / slope


def _ols(x, y):
    if len(x) < 3:
        return np.nan, np.nan, None
    X = np.c_[np.ones_like(x), x]
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta[0], beta[1], X


# ----------------------------------------------------------------------------- baselines
def fit_max_observed(v, a, play):
    m = np.isfinite(v) & np.isfinite(a)
    return dict(A0=float(np.max(a[m])), S0=float(np.max(v[m])))


def fit_binned(v, a, play):
    vb, ab, _ = bin_maxima(v, a, play)
    i, s, _ = _ols(vb, ab)
    A0, S0 = _line_to_params(i, s)
    return dict(A0=A0, S0=S0, n_bins=len(vb))


def fit_binned_ci(v, a, play, level=0.95):
    from scipy.stats import t as tdist
    vb, ab, _ = bin_maxima(v, a, play)
    i, s, X = _ols(vb, ab)
    if X is None:
        return dict(A0=np.nan, S0=np.nan)
    res = ab - (i + s * vb)
    dof = max(len(vb) - 2, 1)
    s2 = np.sum(res ** 2) / dof
    XtXi = np.linalg.pinv(X.T @ X)
    se_pred = np.sqrt(s2 * (1 + np.einsum("ij,jk,ik->i", X, XtXi, X)))
    keep = np.abs(res) <= tdist.ppf(0.5 + level / 2, dof) * se_pred
    i2, s2_, _ = _ols(vb[keep], ab[keep])
    A0, S0 = _line_to_params(i2, s2_)
    return dict(A0=A0, S0=S0)


def fit_binned_boxplot(v, a, play, v_min=V_MIN, width=BIN_W):
    m = (v >= v_min) & (a > 0)
    v, a, play = v[m], a[m], play[m]
    b = np.floor((v - v_min) / width).astype(int)
    keep = np.ones(len(v), bool)
    for k in np.unique(b):
        idx = b == k
        if idx.sum() >= 4:
            q1, q3 = np.percentile(a[idx], [25, 75])
            keep[idx] = a[idx] <= q3 + 1.5 * (q3 - q1)
    return fit_binned(v[keep], a[keep], play[keep])


def fit_dbscan_binned(v, a, play, eps=0.12, min_samples=5):
    from sklearn.cluster import DBSCAN
    m = (v >= V_MIN) & (a > 0)
    v, a, play = v[m], a[m], play[m]
    if len(v) < 10:
        return dict(A0=np.nan, S0=np.nan)
    Z = np.c_[(v - v.mean()) / (v.std() + 1e-9), (a - a.mean()) / (a.std() + 1e-9)]
    lab = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(Z)
    keep = lab != -1
    return fit_binned(v[keep], a[keep], play[keep])


def fit_quantile(v, a, play, q=0.99):
    import statsmodels.api as sm
    m = (v >= V_MIN) & (a > 0)
    v, a = v[m], a[m]
    if len(v) < 20:
        return dict(A0=np.nan, S0=np.nan)
    res = sm.QuantReg(a, sm.add_constant(v)).fit(q=q, max_iter=2000)
    A0, S0 = _line_to_params(res.params[0], res.params[1])
    return dict(A0=A0, S0=S0)


def fit_simex(x, y, play, fs=10.0, noise_sd=0.01, base=None, lambdas=(0.5, 1.0, 1.5, 2.0), n_rep=4,
              window=5, poly=2, extrapolant="quadratic", rng=None):
    """SIMEX (simulation–extrapolation; Cook & Stefanski 1994) correction of a kinematic A–S
    estimator for position measurement noise of (estimated) SD ``noise_sd`` per axis.

    For each lambda, add independent N(0, lambda * noise_sd^2) noise to x and y, recompute
    kinematics, refit ``base`` (default: Morin binning), average over ``n_rep`` replicates, then
    extrapolate the (lambda, estimate) curve to lambda = -1 (zero measurement noise). Corrects the
    noise-driven inflation of bin maxima; does NOT correct deterministic smoothing bias.
    Requires the measurement-error variance to be known or estimated (an assumption)."""
    from nfl_bdb.simulation.movement import kinematics_fast
    base = base or fit_binned
    rng = rng or np.random.default_rng(0)

    def est(xx, yy):
        s, at, _ = kinematics_fast(xx, yy, play, fs, window, poly)
        r = base(s, at, play)
        return np.log(r["A0"]), np.log(r["S0"])

    lam = [0.0]; vals = [est(x, y)]
    for L in lambdas:
        reps = []
        for _ in range(n_rep):
            sd = np.sqrt(L) * noise_sd
            reps.append(est(x + rng.normal(0, sd, len(x)), y + rng.normal(0, sd, len(y))))
        lam.append(L); vals.append(tuple(np.nanmean(np.array(reps), axis=0)))
    lam = np.array(lam); vals = np.array(vals)
    out = {}
    for k, name in enumerate(("A0", "S0")):
        ok = np.isfinite(vals[:, k])
        if ok.sum() < 3:
            out[name] = np.nan; continue
        if extrapolant == "rational":
            from scipy.optimize import curve_fit
            g = lambda L, a, b, c: a + b / (c + L)
            try:
                p0 = [vals[ok, k][-1], 0.0, 2.0]
                pr, _ = curve_fit(g, lam[ok], vals[ok, k], p0=p0, bounds=([-10, -50, 1.05], [10, 50, 50]), maxfev=5000)
                out[name] = float(np.exp(g(-1.0, *pr)))
            except Exception:
                coef = np.polyfit(lam[ok], vals[ok, k], 2); out[name] = float(np.exp(np.polyval(coef, -1.0)))
        else:
            deg = 2 if extrapolant == "quadratic" else 1
            coef = np.polyfit(lam[ok], vals[ok, k], deg)
            out[name] = float(np.exp(np.polyval(coef, -1.0)))
    out["naive_A0"], out["naive_S0"] = float(np.exp(vals[0, 0])), float(np.exp(vals[0, 1]))
    return out


def jackknife_se(fn, n_groups=10, plays=None, rng=None):
    """Delete-a-group jackknife over plays. ``fn(keep_mask_over_plays)`` -> array of estimates."""
    rng = rng or np.random.default_rng(0)
    up = np.unique(plays)
    grp = rng.permutation(len(up)) % n_groups
    full = np.asarray(fn(np.ones(len(up), bool)), float)
    reps = np.array([fn(grp != g) for g in range(n_groups)], float)
    ok = np.all(np.isfinite(reps), axis=1)
    if ok.sum() < 3:
        return full, np.full_like(full, np.nan)
    G = ok.sum()
    se = np.sqrt((G - 1) / G * np.sum((reps[ok] - reps[ok].mean(0)) ** 2, axis=0))
    return full, se


def eb_shrink(est, se, groups):
    """Normal–normal empirical-Bayes shrinkage within groups (per column, on the given scale).

    est_j ~ N(theta_j, se_j^2), theta_j ~ N(mu_g, tau_g^2); (mu_g, tau_g) by maximum likelihood.
    Returns posterior means and SDs (hyper-parameter uncertainty ignored)."""
    est, se = np.atleast_2d(est.T).T, np.atleast_2d(se.T).T
    groups = np.asarray(groups)
    pm = np.full_like(est, np.nan); psd = np.full_like(est, np.nan)
    for g in np.unique(groups):
        idx = groups == g
        for k in range(est.shape[1]):
            e, s = est[idx, k], se[idx, k]
            ok = np.isfinite(e) & np.isfinite(s) & (s > 0)
            if ok.sum() < 3:
                pm[idx, k] = e; psd[idx, k] = s; continue

            def nll(par):
                mu, lt = par; t2 = np.exp(2 * lt)
                v = t2 + s[ok] ** 2
                return 0.5 * np.sum(np.log(v) + (e[ok] - mu) ** 2 / v)
            r = minimize(nll, [np.median(e[ok]), np.log(np.std(e[ok]) + 1e-3)], method="Nelder-Mead")
            mu, t2 = r.x[0], np.exp(2 * r.x[1])
            ee = np.where(ok, e, mu); ss = np.where(ok, s, np.inf)
            prec = 1 / t2 + 1 / ss ** 2
            pm[idx, k] = (ee / ss ** 2 + mu / t2) / prec
            psd[idx, k] = np.sqrt(1 / prec)
    return pm, psd


class PooledCapacityEstimator:
    """Proposed estimator (NCP-AS): noise-corrected, pooled in-situ A–S capacity.

    Per athlete j (frames with positions x, y and play ids):
      1. kinematics: Savitzky–Golay derivatives (window ``window``, quadratic) of positions;
      2. A–S line by Morin et al. (2021) binning (max acceleration per 0.2 m/s bin from 3 m/s, OLS);
      3. SIMEX correction (Cook & Stefanski 1994) for position noise of SD ``noise_sd``
         (quadratic extrapolant; lambdas 0.5–2; ``n_rep`` replicates per lambda);
      4. play-level delete-a-group jackknife SE of (log A0, log S0);
    Across athletes within a group g:
      5. normal–normal empirical-Bayes shrinkage of (log A0, log S0) with the jackknife SEs
         (athletes with little informative exposure are pulled toward the group mean, with wider
         intervals). Intervals: posterior mean ± z * posterior SD on the log scale.

    Ablations: ``simex=False`` (binning only), ``shrink=False`` (no pooling; jackknife intervals).
    Cost: O(J * G * (1 + L * R) * N_j) for J athletes, G jackknife groups, L lambdas, R replicates.
    """

    def __init__(self, noise_sd=0.01, window=7, simex=True, shrink=True, n_groups=10,
                 lambdas=(0.5, 1.0, 1.5, 2.0), n_rep=3, level=0.90, fs=10.0, seed=0):
        self.__dict__.update(dict(noise_sd=noise_sd, window=window, simex=simex, shrink=shrink, n_groups=n_groups,
                                  lambdas=lambdas, n_rep=n_rep, level=level, fs=fs, seed=seed))

    def _one(self, x, y, play, rng):
        from nfl_bdb.simulation.movement import kinematics_fast
        up = np.unique(play)

        def fn(keep):
            m = np.isin(play, up[keep])
            if self.simex:
                r = fit_simex(x[m], y[m], play[m], fs=self.fs, noise_sd=self.noise_sd, lambdas=self.lambdas,
                              n_rep=self.n_rep, window=self.window, rng=np.random.default_rng(rng.integers(1 << 31)))
            else:
                sp, at, _ = kinematics_fast(x[m], y[m], play[m], self.fs, self.window)
                r = fit_binned(sp, at, play[m])
            return [np.log(r["A0"]) if r["A0"] > 0 else np.nan, np.log(r["S0"]) if r["S0"] > 0 else np.nan]
        return jackknife_se(fn, self.n_groups, up, rng)

    def fit(self, tracks, groups):
        """tracks: list over athletes of (x, y, play) arrays ordered by (play, time)."""
        from scipy.stats import norm
        rng = np.random.default_rng(self.seed)
        est = np.full((len(tracks), 2), np.nan); se = est.copy()
        for j, (x, y, p) in enumerate(tracks):
            est[j], se[j] = self._one(x, y, p, rng)
        if self.shrink:
            pm, psd = eb_shrink(est, se, groups)
        else:
            pm, psd = est, se
        z = norm.ppf(0.5 + self.level / 2)
        return dict(A0=np.exp(pm[:, 0]), S0=np.exp(pm[:, 1]),
                    A0_lo=np.exp(pm[:, 0] - z * psd[:, 0]), A0_hi=np.exp(pm[:, 0] + z * psd[:, 0]),
                    S0_lo=np.exp(pm[:, 1] - z * psd[:, 1]), S0_hi=np.exp(pm[:, 1] + z * psd[:, 1]),
                    raw_logA0=est[:, 0], raw_logS0=est[:, 1], se_logA0=se[:, 0], se_logS0=se[:, 1])


BASELINES = {
    "max_observed": fit_max_observed,
    "binned": fit_binned,
    "binned_ci": fit_binned_ci,
    "binned_boxplot": fit_binned_boxplot,
    "dbscan_binned": fit_dbscan_binned,
    "quantile_0.99": fit_quantile,
    "quantile_0.95": lambda v, a, p: fit_quantile(v, a, p, q=0.95),
}


def bootstrap_interval(fn, v, a, play, n_boot=50, level=0.90, rng=None):
    """Play-level (block) bootstrap percentile interval for a baseline estimator."""
    rng = rng or np.random.default_rng(0)
    plays = np.unique(play)
    idx_by_play = {p: np.flatnonzero(play == p) for p in plays}
    est = []
    for _ in range(n_boot):
        pick = rng.choice(plays, len(plays), replace=True)
        idx = np.concatenate([idx_by_play[p] for p in pick])
        newplay = np.repeat(np.arange(len(pick)), [len(idx_by_play[p]) for p in pick])
        r = fn(v[idx], a[idx], newplay)
        est.append((r["A0"], r["S0"]))
    est = np.array(est, float)
    lo, hi = np.nanpercentile(est, [50 * (1 - level), 50 * (1 + level)], axis=0)
    return dict(A0_lo=lo[0], A0_hi=hi[0], S0_lo=lo[1], S0_hi=hi[1])


# ----------------------------------------------------------------------------- proposed estimator
def _nexp_logpdf(w, rate, sigma):
    """log density of w = eps - u, eps ~ N(0, sigma^2), u ~ Exp(rate)."""
    return np.log(rate) + rate * w + 0.5 * (rate * sigma) ** 2 + log_ndtr(-w / sigma - rate * sigma)


def _nexp_logcdf_terms(t, rate, sigma):
    """Return (log Phi(t/sigma), log of exp(rate t + rate^2 sigma^2/2) Phi(-t/sigma - rate sigma)).
    CDF of w = eps - u is exp(term1) + exp(term2)."""
    return log_ndtr(t / sigma), rate * t + 0.5 * (rate * sigma) ** 2 + log_ndtr(-t / sigma - rate * sigma)


@dataclass
class HEFConfig:
    mode: str = "evt"           # "evt": extreme-value bin-maximum frontier (proposed); "frame": frame-level frontier;
                                # "bin": bin maxima with single noise term (initial design). See class docstring.
    corr_frames: float = 2.5    # evt: effective number of independent looks per bin = frames / corr_frames
    evt_n: str = "frames"       # evt: exposure count per bin, "frames" (frames / corr_frames) or "plays"
    mixture: bool = True        # two-component exponential shortfall (near-maximal + sub-maximal efforts)
    truncation: bool = True     # correct the likelihood for selecting frames with a > 0
    pooled: bool = True         # hierarchical (empirical-Bayes) prior across athletes in a group
    robust: bool = True         # play-clustered sandwich information (frames within a play are not independent)
    gamma: float = 1.0          # bin mode only: shortfall rate = lambda * n_plays_in_bin ** gamma
    em_iters: int = 6
    sigma_init: float = 0.4
    max_frames: int = 6000      # random subsample of frames per athlete for speed (by play, preserving clusters)
    prior_sd_floor: tuple = (0.03, 0.02, 0.3, 0.3, 0.3)
    flat_prior_sd: tuple = (1.0, 1.0, 3.0, 3.0, 3.0)
    level: float = 0.90
    seed: int = 0


@dataclass
class HEFResult:
    A0: np.ndarray
    S0: np.ndarray
    A0_lo: np.ndarray
    A0_hi: np.ndarray
    S0_lo: np.ndarray
    S0_hi: np.ndarray
    theta: np.ndarray
    sigma: dict = field(default_factory=dict)
    mu: dict = field(default_factory=dict)
    Sigma: dict = field(default_factory=dict)


class HierarchicalFrontierEstimator:
    """Hierarchical stochastic-frontier estimator of the A–S line (HEF).

    Frame-level model (``mode="frame"``, proposed). For athlete j, frame i with speed v_i >= v_min:

        a_i = F_j(v_i) - u_i + eps_i,     F_j(v) = A0_j (1 - v / S0_j)
        eps_i ~ N(0, sigma_g^2)                        measurement + differentiation noise
        u_i  ~ pi_j Exp(r1_j) + (1 - pi_j) Exp(r2_j)   effort shortfall: near-maximal vs sub-maximal efforts

    Only frames with a_i > 0 are used (as in the in-situ literature), so each frame's density is divided
    by P(a > 0 | v_i) = 1 - CDF_w(-F_j(v_i)) (truncation correction). This is the stochastic-frontier
    decomposition of Aigner, Lovell & Schmidt (1977) applied to the A–S line, with a mixture shortfall.
    Unlike bin-maximum methods it never takes a maximum over noisy frames, so measurement noise is
    deconvolved (sigma is estimated) instead of inflating the frontier.

    Hierarchy and inference: theta_j = (log A0, log S0, logit pi, log r1, log r2) ~ N(mu_g, Sigma_g);
    empirical-Bayes / EM updates of (mu_g, Sigma_g, sigma_g); Laplace approximation at each MAP.
    With ``robust=True`` the data information is the inverse of the play-clustered sandwich
    H^-1 B H^-1 (B = sum over plays of outer products of per-play score vectors), because smoothed
    10 Hz frames within a play are strongly autocorrelated.

    Extreme-value mode (``mode="evt"``, proposed after the diagnostics in notebook 02). Bins as in
    Morin et al. (2021); the bin maximum y_b is modelled as the maximum of n_b independent looks
    a = F(v_b) - u + eps with u ~ Exp(lambda_j), eps ~ N(0, sigma_g^2):
        P(y_b <= y) = CDF_W(y - F(v_b)) ** n_b ,   W = eps - u (normal–exponential).
    This represents both effects that bias bin-maximum methods: noise inflation of a maximum
    (grows with n_b) and censoring (few looks => large expected gap below the frontier).
    n_b = frames in bin / corr_frames (smoothed frames are autocorrelated). Shortfall rate lambda_j is
    athlete-specific (pooled), sigma_g is shared within a group.

    Bin mode (``mode="bin"``) is the first design we tried: bin maxima with exposure-scaled exponential
    shortfall. Kept only as an ablation — the maximum of many noisy frames is biased upward, which the
    single-noise-term likelihood does not represent.

    Complexity per EM iteration: O(J * N_j * k) with N_j <= max_frames frames and k optimiser evaluations.
    """

    def __init__(self, config: HEFConfig | None = None):
        self.cfg = config or HEFConfig()

    # ---- per-frame log-likelihood vector
    def _loglik_vec(self, th, v, a, sigma):
        cfg = self.cfg
        A0, S0 = np.exp(th[0]), np.exp(th[1])
        F = A0 * (1 - v / S0)
        w = a - F
        if cfg.mixture:
            pi = 1 / (1 + np.exp(-th[2])); r1, r2 = np.exp(th[3]), np.exp(th[4])
            l1 = np.log(pi) + _nexp_logpdf(w, r1, sigma)
            l2 = np.log1p(-pi) + _nexp_logpdf(w, r2, sigma)
            ll = np.logaddexp(l1, l2)
            if cfg.truncation:
                c1a, c1b = _nexp_logcdf_terms(-F, r1, sigma)
                c2a, c2b = _nexp_logcdf_terms(-F, r2, sigma)
                logcdf = np.logaddexp(np.log(pi) + np.logaddexp(c1a, c1b), np.log1p(-pi) + np.logaddexp(c2a, c2b))
                ll = ll - np.log1p(-np.minimum(np.exp(logcdf), 1 - 1e-12))
        else:
            r = np.exp(th[3])
            ll = _nexp_logpdf(w, r, sigma)
            if cfg.truncation:
                ca, cb = _nexp_logcdf_terms(-F, r, sigma)
                ll = ll - np.log1p(-np.minimum(np.exp(np.logaddexp(ca, cb)), 1 - 1e-12))
        return ll

    def _evt_loglik_vec(self, th, vb, yb, n, sigma):
        """Bin maximum of n independent looks a = F - u + eps, u ~ Exp(lam), eps ~ N(0, sigma^2):
        log density = log n + (n - 1) log CDF_W(w) + log pdf_W(w),  w = y - F(v)."""
        A0, S0, lam = np.exp(th[0]), np.exp(th[1]), np.exp(th[3])
        w = yb - A0 * (1 - vb / S0)
        ca, cb = _nexp_logcdf_terms(w, lam, sigma)
        logcdf = np.minimum(np.logaddexp(ca, cb), 0.0)
        return np.log(n) + (n - 1) * logcdf + _nexp_logpdf(w, lam, sigma)

    def _bin_loglik_vec(self, th, vb, yb, nb, sigma):
        A0, S0, lam = np.exp(th[0]), np.exp(th[1]), np.exp(th[3])
        return _nexp_logpdf(yb - A0 * (1 - vb / S0), lam * nb ** self.cfg.gamma, sigma)

    @staticmethod
    def _hess(f, x, h=1e-3):
        n = len(x); H = np.zeros((n, n)); f0 = f(x)
        for i in range(n):
            ei = np.zeros(n); ei[i] = h
            H[i, i] = (f(x + ei) - 2 * f0 + f(x - ei)) / h ** 2
            for j in range(i + 1, n):
                ej = np.zeros(n); ej[j] = h
                H[i, j] = H[j, i] = (f(x + ei + ej) - f(x + ei - ej) - f(x - ei + ej) + f(x - ei - ej)) / (4 * h * h)
        return H

    def _prep(self, data, rng):
        cfg = self.cfg
        out = []
        for v, a, play in data:
            m = (v >= V_MIN) & (a > 0) & np.isfinite(v) & np.isfinite(a)
            v, a, play = v[m], a[m], play[m]
            if cfg.mode == "bin":
                out.append(bin_maxima(v, a, play) + (None,)); continue
            if cfg.mode == "evt":
                vb, ab, nb, nf = bin_maxima(v, a, play, return_frames=True)
                n = np.maximum(nf / cfg.corr_frames, 1.0) if cfg.evt_n == "frames" else np.maximum(nb, 1.0)
                out.append((vb, ab, n, None)); continue
            if len(v) > cfg.max_frames:
                plays = np.unique(play); rng.shuffle(plays)
                cnt = np.cumsum([np.sum(play == p) for p in plays])
                keep = np.isin(play, plays[: max(1, np.searchsorted(cnt, cfg.max_frames))])
                v, a, play = v[keep], a[keep], play[keep]
            _, inv = np.unique(play, return_inverse=True)
            out.append((v, a, inv, None))
        return out

    def fit(self, data: list[tuple], groups) -> HEFResult:
        """data: list over athletes of (v, a, play) arrays (any frames; filtering is done here).
        groups: group label per athlete (pooling unit, e.g. position)."""
        cfg = self.cfg
        rng = np.random.default_rng(cfg.seed)
        groups = np.asarray(groups)
        J = len(data)
        prep = self._prep(data, rng)
        npar = 5
        theta = np.zeros((J, npar)); covs = np.zeros((J, npar, npar))
        for j, d in enumerate(prep):
            if cfg.mode in ("bin", "evt"):
                vb, yb = d[0], d[1]
            else:
                vb, yb, _ = bin_maxima(d[0], d[1], d[2])
            A0, S0 = _line_to_params(*_ols(vb, yb)[:2]) if len(vb) >= 3 else (np.nan, np.nan)
            if not np.isfinite(A0) or not (4.0 < S0 < 20):
                A0 = np.max(yb) * 1.2 if len(yb) else 7.0
                S0 = np.max(vb) * 1.05 if len(vb) else 10.0
            theta[j] = [np.log(A0), np.log(min(max(S0, 4.5), 19)), 0.0, np.log(5.0), np.log(0.5)]
        mu, Sigma, sigma = {}, {}, {}
        for g in np.unique(groups):
            idx = groups == g
            mu[g] = np.median(theta[idx], axis=0)
            Sigma[g] = (np.diag(np.array([0.15, 0.10, 2.0, 1.5, 1.5]) ** 2) if cfg.pooled
                        else np.diag(np.array(cfg.flat_prior_sd) ** 2))
            sigma[g] = cfg.sigma_init
        bounds = [(np.log(2), np.log(25)), (np.log(4.5), np.log(20)), (-8, 8), (-4, 6), (-6, 4)]
        n_iter = cfg.em_iters if cfg.pooled else 2

        def data_ll(j, th, sg):
            d = prep[j]
            if cfg.mode == "evt":
                return np.sum(self._evt_loglik_vec(th, d[0], d[1], d[2], sg))
            if cfg.mode == "bin":
                return np.sum(self._bin_loglik_vec(th, d[0], d[1], d[2], sg))
            return np.sum(self._loglik_vec(th, d[0], d[1], sg))

        for it in range(n_iter):
            for j in range(J):
                g = groups[j]; Sinv = np.linalg.inv(Sigma[g])
                if len(prep[j][0]) < 3:
                    theta[j] = mu[g]; covs[j] = Sigma[g]; continue
                f = lambda th: -data_ll(j, th, sigma[g]) + 0.5 * (th - mu[g]) @ Sinv @ (th - mu[g])
                r = minimize(f, theta[j], method="L-BFGS-B", bounds=bounds)
                theta[j] = r.x
                last = it == n_iter - 1
                Hd = self._hess(lambda th: -data_ll(j, th, sigma[g]), r.x)
                info = Hd
                if cfg.robust and cfg.mode == "frame" and last:
                    info = self._robust_info(j, prep[j], r.x, sigma[g], Hd)
                prec = info + Sinv
                try:
                    C = np.linalg.inv(prec)
                    if not np.all(np.isfinite(C)) or np.any(np.diag(C) <= 0):
                        raise np.linalg.LinAlgError
                except np.linalg.LinAlgError:
                    C = Sigma[g]
                covs[j] = C
            for g in np.unique(groups):
                idx = np.where(groups == g)[0]
                if cfg.pooled:
                    mu[g] = theta[idx].mean(axis=0)
                    dlt = theta[idx] - mu[g]
                    S = (dlt.T @ dlt) / len(idx) + covs[idx].mean(axis=0)
                    S = 0.5 * (S + S.T)
                    S[np.diag_indices(npar)] = np.maximum(np.diag(S), np.array(cfg.prior_sd_floor) ** 2)
                    Sigma[g] = S
                neg = lambda ls: -sum(data_ll(j, theta[j], np.exp(ls)) for j in idx if len(prep[j][0]) >= 3)
                sigma[g] = float(np.exp(minimize_scalar(neg, bounds=(np.log(0.02), np.log(3.0)), method="bounded").x))
        from scipy.stats import norm
        z = norm.ppf(0.5 + cfg.level / 2)
        se = np.sqrt(np.maximum(covs[:, [0, 1], [0, 1]], 0))
        return HEFResult(A0=np.exp(theta[:, 0]), S0=np.exp(theta[:, 1]),
                         A0_lo=np.exp(theta[:, 0] - z * se[:, 0]), A0_hi=np.exp(theta[:, 0] + z * se[:, 0]),
                         S0_lo=np.exp(theta[:, 1] - z * se[:, 1]), S0_hi=np.exp(theta[:, 1] + z * se[:, 1]),
                         theta=theta, sigma=sigma, mu=mu, Sigma=Sigma)

    def _robust_info(self, j, d, th, sg, Hd, h=1e-4):
        """Inverse play-clustered sandwich: Hd B^-1 Hd, with B from per-play score sums."""
        v, a, cl = d[0], d[1], d[2]
        k = len(th); G = np.zeros((cl.max() + 1, k))
        for i in range(k):
            e = np.zeros(k); e[i] = h
            gi = (self._loglik_vec(th + e, v, a, sg) - self._loglik_vec(th - e, v, a, sg)) / (2 * h)
            G[:, i] = np.bincount(cl, weights=gi, minlength=cl.max() + 1)
        B = G.T @ G
        try:
            return Hd @ np.linalg.pinv(B) @ Hd
        except np.linalg.LinAlgError:
            return Hd
