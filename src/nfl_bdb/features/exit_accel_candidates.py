"""Phase 13 candidate estimators of post-turn (straight-exit) acceleration after the first short-shuttle
reversal. Development code: the estimator selected on synthetic ground truth is copied, with its parameters
fixed, into ``exit_accel_frozen.py``; real data are analysed only with the frozen module.

E1  frame-based (Phase 12, unchanged): ``shuttle_accel.analyse_attempt`` with its defaults; OLS slope of
    the SG speed over the 6 frames starting at the first straight frame k0. 95% interval: OLS t-interval
    (df = 4), which ignores window-placement error.
E2  sub-frame exit time: same detection; the exit time is moved between frames k0-1 and k0 to where the
    criteria (speed >= 1 yd/s, deviation <= 15 deg) are first met, by linear interpolation of each failing
    criterion's margin; acceleration = [v(t_exit + 0.5) - v(t_exit)] / 0.5 with v linearly interpolated
    between SG frame speeds. 95% interval: E1's OLS standard error with df = 4 (ignores exit-time error).
E3  continuous-time fit: cubic smoothing splines x(t), y(t) (scipy make_smoothing_spline, penalty
    lam * integral f''^2) fitted on a fixed span of frames [i_min - 0.5 s, i_min + 1.5 s] around the
    Phase 12 speed-minimum frame; exit time = first time after the fitted speed minimum with fitted speed
    >= 1 yd/s and fitted heading within 15 deg of the outgoing drill axis (1 ms grid); estimate = mean of
    a_t(t) = v(t).a(t)/|v(t)| over [t_exit + 0.2, t_exit + 0.7]. 95% interval: parametric bootstrap
    (Gaussian residuals with the fitted residual SD, refit, re-detect exit), percentile.
"""
from __future__ import annotations

import numpy as np
from scipy.interpolate import make_smoothing_spline
from scipy.stats import t as tdist

from nfl_bdb.features.shuttle_accel import ShuttleParams, analyse_attempt, drill_axis


def params_for_fs(fs: float) -> ShuttleParams:
    """Phase 12 parameters (exactly the defaults at 10 Hz); frame counts scaled by time at other fs."""
    if fs == 10.0:
        return ShuttleParams()
    w = int(round(0.7 * fs)); w += (w % 2 == 0)
    return ShuttleParams(window=w, approach_frames=int(round(0.5 * fs)), min_leg_frames=int(round(0.3 * fs)), fs=fs)


def _first_valid_r1(r):
    if not r["ok"] or not r["reversals"]:
        return None
    return r["reversals"][0]


def e1_e2(x, y, s, fs: float = 10.0) -> dict:
    p = params_for_fs(fs)
    r = analyse_attempt(x, y, s, p)
    r1 = _first_valid_r1(r)
    out = dict(e1=np.nan, e1_lo=np.nan, e1_hi=np.nan, e1_exit=np.nan, e2=np.nan, e2_lo=np.nan, e2_hi=np.nan,
               e2_exit=np.nan, valid=False, reason="no_reversal" if r1 is None else r1["reason"], i_min=np.nan,
               sign_out=0, approach_ok=False)
    if r1 is None:
        return out
    out.update(i_min=r1["i_min"], sign_out=r1["sign_out"], approach_ok=r1["approach_frames"] >= p.approach_frames)
    if not r1["valid"]:
        return out
    k = r["kin"]; sp = k["speed"]; k0 = r1["k0"]; m = int(round(p.reg_window * fs))
    W = np.arange(k0, k0 + m + 1); tt = W / fs
    b, a = np.polyfit(tt, sp[W], 1)
    res = sp[W] - (a + b * tt); se = np.sqrt(res @ res / (len(W) - 2) / ((tt - tt.mean()) @ (tt - tt.mean())))
    q = tdist.ppf(0.975, len(W) - 2)
    out.update(valid=True, e1=float(b), e1_lo=float(b - q * se), e1_hi=float(b + q * se), e1_exit=k0 / fs)
    # E2: sub-frame exit between k0-1 and k0
    u = k["u"]; d = r1["sign_out"]
    dev = np.degrees(np.arccos(np.clip(d * u / np.maximum(k["speed_pos"], 1e-12), -1, 1)))
    crossings = [k0 - 1.0]
    for marg in (k["speed_pos"] - p.v_head, p.straight_deg - dev):
        m0, m1 = marg[k0 - 1], marg[k0]
        if m0 < 0 <= m1 and m1 > m0:
            crossings.append(k0 - 1 + (-m0) / (m1 - m0))
    t_ex = max(crossings) / fs
    fr = np.arange(len(sp)) / fs
    if t_ex + p.reg_window > fr[-1]:
        return out
    v0, v1 = np.interp(t_ex, fr, sp), np.interp(t_ex + p.reg_window, fr, sp)
    e2 = float((v1 - v0) / p.reg_window)
    out.update(e2=e2, e2_lo=e2 - q * se, e2_hi=e2 + q * se, e2_exit=t_ex)
    return out


def _fit(tt, x, y, lam):
    return make_smoothing_spline(tt, x, lam=lam), make_smoothing_spline(tt, y, lam=lam)


def _e3_from_fit(sx, sy, t_lo, t_hi, t_min_frame, axis, sign_out, fs, straight_deg=15.0, v_head=1.0):
    g = np.arange(t_lo, t_hi, 0.001)
    vx, vy = sx.derivative(1)(g), sy.derivative(1)(g)
    ax, ay = sx.derivative(2)(g), sy.derivative(2)(g)
    sp = np.hypot(vx, vy)
    near = (g >= t_min_frame - 1.0 / fs) & (g <= t_min_frame + 1.0 / fs)
    if not near.any():
        return np.nan, np.nan, np.nan
    i_min = int(np.flatnonzero(near)[0] + np.argmin(sp[near]))
    cosd = sign_out * (vx * axis[0] + vy * axis[1]) / np.maximum(sp, 1e-12)
    ok = (sp >= v_head) & (cosd >= np.cos(np.radians(straight_deg)))
    ok[: i_min + 1] = False
    if not ok.any():
        return np.nan, np.nan, np.nan
    t_ex = g[int(np.flatnonzero(ok)[0])]
    sel = (g >= t_ex + 0.2) & (g <= t_ex + 0.7)
    if sel.sum() < 400 or g[-1] < t_ex + 0.7:
        return np.nan, t_ex, np.nan
    at = (vx[sel] * ax[sel] + vy[sel] * ay[sel]) / np.maximum(sp[sel], 1e-12)
    maxdev = float(np.degrees(np.arccos(np.clip(cosd[sel], -1, 1))).max())
    return float(at.mean()), float(t_ex), maxdev


def e3(x, y, s, fs: float = 10.0, lam=1e-4, B: int = 0, rng=None, pre: dict | None = None) -> dict:
    """Continuous-time estimate. ``lam`` = smoothing penalty at 10 Hz (scaled by fs/10), or None for GCV.
    ``pre`` = output of e1_e2 (reuses its reversal detection)."""
    pre = pre if pre is not None else e1_e2(x, y, s, fs)
    out = dict(e3=np.nan, e3_lo=np.nan, e3_hi=np.nan, e3_exit=np.nan, e3_maxdev=np.nan, e3_valid=False,
               e3_reason="")
    if np.isnan(pre["i_min"]) or not pre["approach_ok"]:
        out["e3_reason"] = "no_reversal_or_approach"; return out
    i_min = int(pre["i_min"]); lo = i_min - int(round(0.5 * fs)); hi = i_min + int(round(1.5 * fs))
    if lo < 0 or hi > len(x) - 1:
        out["e3_reason"] = "fit_span_outside_recording"; return out
    idx = np.arange(lo, hi + 1); tt = idx / fs
    x = np.asarray(x, float); y = np.asarray(y, float)
    lam_s = None if lam is None else lam * fs / 10.0
    axis = drill_axis(x, y)
    sx, sy = _fit(tt, x[idx], y[idx], lam_s)
    est, t_ex, maxdev = _e3_from_fit(sx, sy, tt[0], tt[-1], i_min / fs, axis, pre["sign_out"], fs)
    out.update(e3=est, e3_exit=t_ex, e3_maxdev=maxdev)
    if np.isnan(est):
        out["e3_reason"] = "no_exit_or_interval_outside_fit"; return out
    if maxdev > 15.0:
        out["e3_reason"] = "interval_not_straight"; return out
    if tt[-1] - (t_ex + 0.7) < 0.3:
        out["e3_reason"] = "interval_too_close_to_fit_boundary"; return out
    out["e3_valid"] = True
    if B > 0:
        rng = rng or np.random.default_rng(0)
        rx = x[idx] - sx(tt); ry = y[idx] - sy(tt)
        n = len(idx); sig = np.sqrt((rx @ rx + ry @ ry) / (2 * n))
        sig = max(sig, 1e-4)
        bs = []
        for _ in range(B):
            bx, by = _fit(tt, sx(tt) + rng.normal(0, sig, n), sy(tt) + rng.normal(0, sig, n), lam_s)
            b_est, _, _ = _e3_from_fit(bx, by, tt[0], tt[-1], i_min / fs, axis, pre["sign_out"], fs)
            if not np.isnan(b_est):
                bs.append(b_est)
        if len(bs) >= max(10, B // 2):
            out.update(e3_lo=float(np.percentile(bs, 2.5)), e3_hi=float(np.percentile(bs, 97.5)))
    return out
