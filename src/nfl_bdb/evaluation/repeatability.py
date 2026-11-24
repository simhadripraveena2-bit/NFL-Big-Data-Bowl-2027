"""Test-retest repeatability helpers (Phase 11, measurement feasibility).

Two-attempt statistics reuse the frozen two-way ICC helper (``forty_reliability.icc``; Shrout & Fleiss
ICC(3,1) consistency and ICC(2,1) absolute agreement). Added here:
  * Spearman rank agreement between attempts;
  * typical error (TE) = SD(attempt 2 - attempt 1) / sqrt(2) and TE as % of the grand mean;
  * a "within-position" variant: both attempts centred on the position mean of the players' two-attempt
    averages, so between-position differences cannot inflate the coefficient;
  * one-way ICC(1) for an unequal number of attempts per player (all valid attempts);
  * player-cluster bootstrap CIs (seeded).
"""
from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr

from nfl_bdb.features.forty_reliability import icc


def two_attempt_stats(a, b) -> dict:
    a = np.asarray(a, float); b = np.asarray(b, float)
    out = icc(a, b)
    out["spearman"] = float(spearmanr(a, b).statistic) if len(a) > 2 else np.nan
    gm = float(np.mean(np.r_[a, b]))
    out["te"] = out.pop("sem")
    out["te_pct"] = float(100 * out["te"] / abs(gm)) if gm != 0 else np.nan
    out["grand_mean"] = gm
    return out


def centre_by_group(a, b, groups):
    a = np.asarray(a, float).copy(); b = np.asarray(b, float).copy(); groups = np.asarray(groups)
    for g in np.unique(groups):
        m = groups == g
        mu = np.mean(np.r_[a[m], b[m]])
        a[m] -= mu; b[m] -= mu
    return a, b


def boot_two_attempt(a, b, groups=None, stats=("icc31", "icc21", "spearman"), B=2000, seed=1111):
    """Percentile CIs from resampling players. If ``groups`` is given, the position centring is redone
    inside each resample."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    rng = np.random.default_rng(seed); n = len(a)
    vals = {s: np.full(B, np.nan) for s in stats}
    for i in range(B):
        j = rng.integers(0, n, n)
        aa, bb = a[j], b[j]
        if groups is not None:
            aa, bb = centre_by_group(aa, bb, np.asarray(groups)[j])
        if np.std(np.r_[aa, bb]) == 0:
            continue
        r = two_attempt_stats(aa, bb)
        for s in stats:
            vals[s][i] = r[s]
    return {s: tuple(float(q) for q in np.nanpercentile(v, [2.5, 97.5])) for s, v in vals.items()}


def icc1_unbalanced(values_by_player: list[np.ndarray]) -> dict:
    """One-way random-effects ICC(1) with unequal k (ANOVA estimator with k0)."""
    groups = [np.asarray(v, float) for v in values_by_player if len(v) >= 2]
    if len(groups) < 3:
        return dict(n=len(groups), icc1=np.nan)
    N = sum(len(g) for g in groups); a = len(groups)
    gm = np.mean(np.concatenate(groups))
    ssb = sum(len(g) * (g.mean() - gm) ** 2 for g in groups)
    ssw = sum(((g - g.mean()) ** 2).sum() for g in groups)
    msb = ssb / (a - 1); msw = ssw / (N - a)
    k0 = (N - sum(len(g) ** 2 for g in groups) / N) / (a - 1)
    return dict(n=a, n_obs=N, k0=float(k0), icc1=float((msb - msw) / (msb + (k0 - 1) * msw)))
