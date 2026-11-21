"""Combine-only test-retest reliability of the 40-yard dash (approved deviation D3).

Uses ONLY combine tracking and combine results. No NFL game data of any kind is read.

Per tracked 40 attempt (10 Hz; the provider's track starts at movement onset):
    run axis  = unit vector from the first to the last tracked position
    u(t)      = displacement along the run axis from the first frame (yd)
    t10, t40  = time (s) at which u first reaches 10 / 40 yd (linear interpolation between frames).
                If the track ends short of 40 yd by <= 1.5 yd, t40 is extrapolated at the last speed;
                otherwise t40 is missing.
    fly_10_35 = time from u = 10 to u = 35 yd (onset-free split)
    vpeak     = max provided speed s (the registered predictor x_i uses valid attempts only:
                mono-exponential R^2 > 0.95 and vpeak <= 12.5 yd/s)
Reliability: first two usable attempts per player (attempt order kept), within position.
    ICC(3,1) consistency and ICC(2,1) absolute agreement (Shrout & Fleiss two-way models),
    Pearson r, mean attempt-2 minus attempt-1 difference, SEM = SD_between-attempt-diff / sqrt(2).
    Player-bootstrap 95% CIs (seeded).
"""
from __future__ import annotations

import numpy as np
import polars as pl

SPEED_SPIKE = 12.5
EXTRAP_MAX = 1.5


def attempt_times(x: np.ndarray, y: np.ndarray, s: np.ndarray, hz: float = 10.0) -> dict:
    t = np.arange(len(x)) / hz
    ax = np.array([x[-1] - x[0], y[-1] - y[0]]); ax = ax / np.linalg.norm(ax)
    u = (x - x[0]) * ax[0] + (y - y[0]) * ax[1]
    u = np.maximum.accumulate(u)          # monotone progress (removes sub-frame jitter backwards)

    def cross(level):
        k = np.flatnonzero(u >= level)
        if len(k) == 0:
            gap = level - u[-1]
            if gap <= EXTRAP_MAX and s[-1] > 1:
                return float(t[-1] + gap / s[-1])
            return np.nan
        i = int(k[0])
        if i == 0:
            return 0.0
        return float(t[i - 1] + (level - u[i - 1]) / (u[i] - u[i - 1]) * (t[i] - t[i - 1]))

    t10, t35, t40 = cross(10.0), cross(35.0), cross(40.0)
    return dict(t10=t10, t40=t40, fly_10_35=t35 - t10, u_end=float(u[-1]), vpeak=float(s.max()), n_frames=len(x))


def forty_attempt_table(ct: pl.DataFrame) -> pl.DataFrame:
    """ct: combine_tracking rows (PLAYER, FORTY_YARD_DASH), any order."""
    ct = ct.sort("event_id", "nfl_id", "attempt", "time")
    rows = []
    for (eid, nid, att), g in ct.group_by(["event_id", "nfl_id", "attempt"], maintain_order=True):
        r = attempt_times(g["x"].to_numpy(), g["y"].to_numpy(), g["s"].to_numpy())
        rows.append(dict(event_id=eid, nfl_id=int(nid), attempt=int(att), **r))
    return pl.DataFrame(rows, infer_schema_length=None)


def icc(a: np.ndarray, b: np.ndarray) -> dict:
    """Two-way ICCs for k = 2 measurements per subject (Shrout & Fleiss 1979)."""
    Y = np.column_stack([a, b]); n, k = Y.shape
    gm = Y.mean(); rm = Y.mean(1); cm = Y.mean(0)
    msr = k * np.sum((rm - gm) ** 2) / (n - 1)
    msc = n * np.sum((cm - gm) ** 2) / (k - 1)
    sse = np.sum((Y - rm[:, None] - cm[None, :] + gm) ** 2)
    mse = sse / ((n - 1) * (k - 1))
    icc31 = (msr - mse) / (msr + (k - 1) * mse)
    icc21 = (msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n)
    d = b - a
    return dict(n=n, icc31=float(icc31), icc21=float(icc21), r=float(np.corrcoef(a, b)[0, 1]),
                mean_diff=float(d.mean()), sem=float(d.std(ddof=1) / np.sqrt(2)), sd_between=float(np.sqrt(max(msr - mse, 0) / k)))


def boot_ci(a, b, stat, B=2000, seed=4040):
    rng = np.random.default_rng(seed); n = len(a); v = np.empty(B)
    for i in range(B):
        j = rng.integers(0, n, n)
        v[i] = icc(a[j], b[j])[stat]
    return tuple(float(q) for q in np.nanpercentile(v, [2.5, 97.5]))


def spearman_brown(r, k=2):
    return k * r / (1 + (k - 1) * r)
