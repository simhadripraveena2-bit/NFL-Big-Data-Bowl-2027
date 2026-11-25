"""Phase 16 (measurement only): frozen WR route-launch acceleration and the identical tracked-40 reference.

Definition (configs/phase16_protocol.json): Phase 15 kinematics (SG order 2, window 7, position-derived speed,
a_t = gradient of speed); onset = first frame with speed > 1 yd/s; window = onset .. onset + 10 frames (1.0 s);
primary = 95th percentile of a_t over the window; diagnostics = mean a_t and net speed gain. Attempts that are
already moving at frame 0, never exceed 1 yd/s, or do not cover the full window are rejected (no extrapolation).
"""
from __future__ import annotations

import numpy as np

from nfl_bdb.features.skill_drills import kinematics

FS = 10.0
V_ON = 1.0
WIN_FRAMES = 10


def launch(x, y, window: int = 7, fs: float = FS, v_on: float = V_ON, win_frames: int = WIN_FRAMES) -> dict:
    x = np.asarray(x, float); y = np.asarray(y, float); n = len(x)
    if n < window + 2:
        return dict(valid=False, reason="too_short")
    sp = kinematics(x, y, window, fs)["speed"]
    if sp[0] > v_on:
        return dict(valid=False, reason="moving_at_first_frame", start_speed=float(sp[0]))
    idx = np.flatnonzero(sp > v_on)
    if len(idx) == 0:
        return dict(valid=False, reason="no_onset")
    k0 = int(idx[0])
    if k0 + win_frames > n - 1:
        return dict(valid=False, reason="window_incomplete", onset=k0)
    at = np.gradient(sp, 1.0 / fs)
    w = slice(k0, k0 + win_frames + 1)
    frac = (v_on - sp[k0 - 1]) / (sp[k0] - sp[k0 - 1]) if k0 >= 1 and sp[k0] > sp[k0 - 1] else 0.0
    return dict(valid=True, reason="", onset=k0, onset_time=k0 / fs, onset_time_interp=(k0 - 1 + frac) / fs if k0 >= 1 else 0.0,
                p95=float(np.percentile(at[w], 95)), mean_at=float(at[w].mean()), net_gain=float(sp[k0 + win_frames] - sp[k0]),
                start_speed=float(sp[0]))


def gstudy_cov(df, y: str, covs: list[str], athlete: str = "nfl_id", route: str = "route", cell: str = "cell"):
    """Phase 15 G-study model with athlete-level fixed covariates added (REML, statsmodels MixedLM)."""
    import pandas as pd
    import statsmodels.formula.api as smf
    cols = [athlete, route, cell, y] + covs
    d = df[cols].dropna().copy()
    d = pd.DataFrame({"a": d[athlete].astype(str).values, "r": d[route].astype(str).values, "c": d[cell].astype(str).values,
                      "y": d[y].astype(float).values, **{c: d[c].astype(float).values for c in covs}})
    rhs = " + ".join(["C(c)"] + covs)
    fit = smf.mixedlm(f"y ~ {rhs}", d, groups=d["a"], re_formula="1", vc_formula={"pr": "0 + C(r)"}).fit(reml=True, method="lbfgs")
    return dict(s2_athlete=float(fit.cov_re.iloc[0, 0]), s2_athlete_route=float(fit.vcomp[0]), s2_residual=float(fit.scale),
                n_obs=len(d), n_athletes=d["a"].nunique(), converged=bool(fit.converged),
                coefs={c: float(fit.fe_params[c]) for c in covs})
