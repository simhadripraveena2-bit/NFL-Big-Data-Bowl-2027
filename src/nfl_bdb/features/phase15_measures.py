"""Phase 15 (measurement validation only): WR route-drill generalizability study and DL pass-rush arc bend.

No NFL outcome is read here.

1. ``sg_speed_gain``: exact attenuation of Savitzky-Golay (order p) speed on uniform circular motion.
   For x + iy = R exp(i w t), the SG derivative filter c_k (k = -h..h) returns
   v_hat = v * |sum_k c_k exp(i w k dt)| / w,
   and the estimated heading rate equals w exactly (the filter is linear and shift-invariant, so a
   circle maps to a concentric circle traversed in phase). The gain depends only on w, the window
   and the sampling interval; it is fixed by the filter, not fitted to data.
2. ``arc_segment`` / ``arc_measures``: geometric pass-rush arc (no reliability or outcome input).
3. ``gstudy``: unbalanced generalizability study via REML (statsmodels MixedLM): athlete random
   intercept, athlete x route variance component nested in athlete, route x year cells as fixed effects,
   residual = within athlete x route (repeat attempts).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import savgol_coeffs

from nfl_bdb.features.skill_drills import kinematics

FS = 10.0


def sg_speed_gain(omega_rad, window: int = 7, poly: int = 2, fs: float = FS):
    """Ratio estimated/true speed for uniform circular motion at heading rate ``omega_rad`` (rad/s)."""
    dt = 1.0 / fs
    c = savgol_coeffs(window, poly, deriv=1, delta=dt, use="dot")      # weights for samples t-h..t+h
    k = np.arange(window) - window // 2
    w = np.atleast_1d(np.abs(np.asarray(omega_rad, float)))
    g = np.ones_like(w)
    nz = w > 1e-9
    resp = np.exp(1j * np.outer(w[nz], k * dt)) @ c
    g[nz] = np.abs(resp) / w[nz]
    return g if np.ndim(omega_rad) else float(g[0])


@dataclass(frozen=True)
class ArcParams:
    window: int = 7
    omega_arc_deg: float = 25.0     # > 99th percentile (23 deg/s) of straight-sprint frames (Phase 15 geometry audit)
    v_min: float = 2.0              # yd/s: heading reliable and athlete running
    merge_gap: int = 2              # frames: brief straight segments inside the arc are bridged
    min_frames: int = 5
    min_heading_deg: float = 30.0
    fs: float = FS


def _runs(mask):
    idx = np.flatnonzero(mask)
    if len(idx) == 0:
        return []
    br = np.flatnonzero(np.diff(idx) > 1)
    return list(zip(np.r_[idx[0], idx[br + 1]].tolist(), np.r_[idx[br], idx[-1]].tolist()))


def arc_segment(x, y, p: ArcParams = ArcParams()) -> dict:
    """The pass-rush arc: the run (frames with speed >= v_min and |heading rate| >= omega_arc, gaps <= merge_gap
    bridged) with the largest absolute heading change; valid if >= min_frames and >= min_heading_deg."""
    k = kinematics(x, y, p.window, p.fs)
    sp, om = k["speed"], k["omega"]
    on = (sp >= p.v_min) & (np.abs(om) >= np.radians(p.omega_arc_deg))
    runs = []
    for a, b in _runs(on):
        if runs and a - runs[-1][1] - 1 <= p.merge_gap:
            runs[-1] = (runs[-1][0], b)
        else:
            runs.append((a, b))
    best, best_h = None, 0.0
    for a, b in runs:
        h = abs(np.degrees(om[a:b + 1].sum() / p.fs))
        if h > best_h:
            best, best_h = (a, b), h
    out = dict(kin=k, n=len(sp), found=best is not None)
    if best is None:
        return dict(out, valid=False, reason="no_arc")
    a, b = best
    frames = np.arange(a, b + 1)
    frames = frames[sp[frames] >= p.v_min]          # bridged frames below v_min are excluded from medians
    out.update(start=a, end=b, n_frames=int(len(frames)), heading_deg=float(best_h),
               side="left" if om[a:b + 1].sum() > 0 else "right", frames=frames,
               truncated=bool(a == 0 or b >= len(sp) - 1))
    if len(frames) < p.min_frames:
        return dict(out, valid=False, reason="too_few_frames")
    if best_h < p.min_heading_deg:
        return dict(out, valid=False, reason="small_heading_change")
    if out["truncated"]:
        return dict(out, valid=False, reason="truncated")
    return dict(out, valid=True, reason="")


def arc_measures(x, y, p: ArcParams = ArcParams(), band=None, correct: bool = False) -> dict:
    """Median speed, heading rate, curvature (|omega|/v), radius and centripetal acceleration over the arc,
    optionally with the analytic SG speed correction; curvature in a common speed band (frames inside only)."""
    seg = arc_segment(x, y, p)
    res = {k: seg.get(k) for k in ("found", "valid", "reason", "start", "end", "n_frames", "heading_deg", "side", "truncated")}
    if not seg.get("valid"):
        return res
    k = seg["kin"]; f = seg["frames"]
    v = k["speed"][f]; w = np.abs(k["omega"][f])
    if correct:
        v = v / sg_speed_gain(w, p.window, 2, p.fs)
    kappa = w / v
    res.update(speed=float(np.median(v)), omega_deg=float(np.degrees(np.median(w))), curvature=float(np.median(kappa)),
               radius=float(np.median(1 / kappa)), a_n=float(np.median(v * w)), v_min_arc=float(v.min()), v_max_arc=float(v.max()))
    if band is not None:
        m = (v >= band[0]) & (v <= band[1])
        res.update(band_frames=int(m.sum()), band_curvature=float(np.median(kappa[m])) if m.sum() >= 3 else np.nan)
    return res


def gstudy(df, y: str, athlete: str = "nfl_id", route: str = "route", cell: str = "cell"):
    """Unbalanced G-study by REML. Returns variance components (athlete, athlete x route, residual) and counts.
    Assumptions: random effects normal and independent; route x year cells fixed (scores are relative to the
    cell mean); athlete x route interaction and residual are homoscedastic across routes."""
    import pandas as pd
    import statsmodels.formula.api as smf
    d = df[[athlete, route, cell, y]].dropna()
    d = pd.DataFrame({"a": d[athlete].astype(str).values, "r": d[route].astype(str).values, "c": d[cell].astype(str).values,
                      "y": d[y].astype(float).values})
    m = smf.mixedlm("y ~ C(c)", d, groups=d["a"], re_formula="1", vc_formula={"pr": "0 + C(r)"})
    fit = m.fit(reml=True, method="lbfgs")
    s2p = float(fit.cov_re.iloc[0, 0]); s2pr = float(fit.vcomp[0]); s2e = float(fit.scale)
    reps = d.groupby(["a", "r"]).size()
    return dict(s2_athlete=s2p, s2_athlete_route=s2pr, s2_residual=s2e, n_obs=len(d), n_athletes=d["a"].nunique(),
                n_routes=d["r"].nunique(), n_cells=d["c"].nunique(), n_repeat_cells=int((reps >= 2).sum()),
                converged=bool(fit.converged))


def g_coef(s2p, s2pr, s2e, n_routes, n_attempts=1):
    """Generalizability (relative) of an athlete's cell-adjusted mean over n_routes routes."""
    err = s2pr / n_routes + s2e / (n_routes * n_attempts)
    return s2p / (s2p + err) if (s2p + err) > 0 else np.nan
