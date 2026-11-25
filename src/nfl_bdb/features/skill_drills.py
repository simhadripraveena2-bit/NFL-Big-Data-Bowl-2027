"""Phase 14 (data and measurement feasibility only): position-specific Combine skill drills.

Generic, physically defined movement descriptors for one tracked attempt, curve ("bend") metrics, and a
ball-phase parser for the 2025 WR/TE catching drills. Nothing here touches NFL game outcomes.

Kinematics: Savitzky-Golay smoothing of x, y (window w, order 2) at 10 Hz; velocity from the SG derivative;
heading = unwrap(atan2(vy, vx)); heading rate omega; tangential acceleration a_t = d|v|/dt; normal
(centripetal) acceleration a_n = |v| * |omega| (rad/s). Heading quantities are used only where speed >= v_head.
Combine tracking has no body orientation (`o`), so facing direction (backpedal vs forward run) is not observable.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import savgol_filter

FS = 10.0

# Candidate aliases (same drill under a different name in another year). Each is checked by geometry in the
# Phase 14 runner before pooling; names not listed are never merged.
ALIASES = {
    ("SKILL_DRILLS_DB", "LINE"): "LINE_DRILL",
    ("SKILL_DRILLS_OL", "PASS_PRO_MIRROR_DRILL"): "PASS_PRO-MIRROR_DRILL",
    ("SKILL_DRILLS_TE", "OVER_THE_SHOULDER_ADJUST"): "OVER_SHOULDER_ADJUST",
    ("SKILL_DRILLS_WR", "SPEED_OUT_LEFT"): "SPEED_OUT_ROUTE_LEFT",
}


def harmonise(drill_type: str, drill_name: str) -> str:
    return ALIASES.get((drill_type, drill_name), drill_name)


def kinematics(x, y, window: int = 7, fs: float = FS) -> dict:
    x = np.asarray(x, float); y = np.asarray(y, float)
    dt = 1.0 / fs
    vx = savgol_filter(x, window, 2, deriv=1, delta=dt); vy = savgol_filter(y, window, 2, deriv=1, delta=dt)
    sp = np.hypot(vx, vy)
    theta = np.unwrap(np.arctan2(vy, vx))
    omega = np.gradient(theta, dt)                      # rad/s
    a_t = np.gradient(sp, dt)
    a_n = sp * np.abs(omega)
    return dict(vx=vx, vy=vy, speed=sp, omega=omega, a_t=a_t, a_n=a_n)


def descriptors(x, y, window: int = 7, v_head: float = 1.0, v_curve: float = 2.0, fs: float = FS) -> dict:
    """Generic physical descriptors of one attempt (direction-invariant unless stated)."""
    x = np.asarray(x, float); y = np.asarray(y, float); n = len(x)
    out = dict(n_frames=n, duration=(n - 1) / fs)
    if n < window + 2:
        out["ok"] = False
        return out
    k = kinematics(x, y, window, fs)
    sp, om = k["speed"], k["omega"]
    step = np.hypot(np.diff(x), np.diff(y))
    P = np.c_[x, y] - np.c_[x, y].mean(0)
    _, sv, vt = np.linalg.svd(P, full_matrices=False)
    e1 = vt[0]; u = k["vx"] * e1[0] + k["vy"] * e1[1]
    sign = np.where(u >= 1.5, 1, np.where(u <= -1.5, -1, 0))
    s_nz = sign[sign != 0]
    head = sp >= v_head; curve = sp >= v_curve
    out.update(
        ok=True, path_length=float(step.sum()), net_displacement=float(np.hypot(x[-1] - x[0], y[-1] - y[0])),
        extent_major=float(np.ptp(P @ vt[0])), extent_minor=float(np.ptp(P @ vt[1])),
        peak_speed=float(sp.max()), mean_speed_moving=float(sp[head].mean()) if head.any() else np.nan,
        start_speed=float(sp[0]), end_speed=float(sp[-1]),
        n_axis_reversals=int((np.diff(s_nz) != 0).sum()) if len(s_nz) > 1 else 0,
        total_heading_change_deg=float(np.degrees(np.abs(om[head]).sum() / fs)) if head.any() else np.nan,
        signed_heading_change_deg=float(np.degrees(om[head].sum() / fs)) if head.any() else np.nan,
        a_n_p95=float(np.percentile(k["a_n"][curve], 95)) if curve.sum() >= 5 else np.nan,
        a_t_p95=float(np.percentile(k["a_t"], 95)), decel_p05=float(np.percentile(k["a_t"], 5)),
        frac_time_moving=float(head.mean()),
    )
    return out


def curve_metrics(x, y, window: int = 7, v_curve: float = 2.0, omega_min_deg: float = 60.0, min_frames: int = 5,
                  fs: float = FS) -> dict:
    """Bend on curved running: frames with speed >= v_curve and |heading rate| >= omega_min_deg.
    Reports, for all curve frames and separately for left (omega > 0) and right (omega < 0) turning:
    median speed, median centripetal acceleration a_n = v |omega|, median radius v / |omega|, frame count."""
    k = kinematics(x, y, window, fs)
    sp, om = k["speed"], k["omega"]
    on = (sp >= v_curve) & (np.abs(om) >= np.radians(omega_min_deg))
    out = {}
    for lab, m in (("all", on), ("left", on & (om > 0)), ("right", on & (om < 0))):
        nfr = int(m.sum())
        if nfr >= min_frames:
            out.update({f"{lab}_n": nfr, f"{lab}_speed": float(np.median(sp[m])), f"{lab}_a_n": float(np.median(k["a_n"][m])),
                        f"{lab}_radius": float(np.median(sp[m] / np.abs(om[m])))})
        else:
            out.update({f"{lab}_n": nfr, f"{lab}_speed": np.nan, f"{lab}_a_n": np.nan, f"{lab}_radius": np.nan})
    return out


def ball_phases(px, py, bx, by, fs: float = FS, contact_d: float = 1.0, hold_frames: int = 5,
                flight_speed: float = 8.0, jump_speed: float = 25.0) -> dict:
    """Parse ball relative to receiver (same timestamps). There are no event markers, so this is a heuristic:
      contact  = first frame with ball-receiver distance <= ``contact_d`` yd
      flight   = consecutive frames immediately before contact with ball step speed >= ``flight_speed`` yd/s
      throw    = first frame of that flight run
      held     = ball stays within ``contact_d`` for ``hold_frames`` frames starting at contact
      jump     = a ball step faster than ``jump_speed`` yd/s within 5 frames after contact (a tracking
                 discontinuity: the ball 'teleports', so the contact frame is ambiguous)
    A catch phase is 'identifiable' only if flight >= 3 frames, contact is found, the ball is held, and there
    is no jump around contact."""
    px, py, bx, by = (np.asarray(a, float) for a in (px, py, bx, by))
    n = len(px)
    d = np.hypot(bx - px, by - py)
    bs = np.r_[np.hypot(np.diff(bx), np.diff(by)) * fs, np.nan]   # bs[i] = speed from i to i+1
    idx = np.flatnonzero(d <= contact_d)
    contact = int(idx[0]) if len(idx) else -1
    throw, n_flight = -1, 0
    if contact > 0:
        j = contact - 1
        while j >= 0 and bs[j] >= flight_speed and bs[j] < jump_speed:
            n_flight += 1; j -= 1
        throw = j + 1 if n_flight else -1
    held = bool(contact >= 0 and contact + hold_frames <= n and (d[contact:contact + hold_frames] <= contact_d).all())
    jump = bool(contact >= 0 and np.nanmax(bs[max(contact - 1, 0):min(contact + 5, n - 1)] if contact < n - 1 else [0]) > jump_speed)
    return dict(n=n, d_start=float(d[0]), d_min=float(d.min()), contact=contact, throw=throw, n_flight=n_flight,
                flight_speed_med=float(np.median(bs[throw:contact])) if n_flight else np.nan,
                ball_static_before_throw=bool(throw > 3 and np.nanmedian(bs[:throw]) < 3.0),
                held=held, jump_near_contact=jump, n_ball_jumps=int(np.nansum(bs > jump_speed)),
                max_ball_step_speed=float(np.nanmax(bs)) if n > 1 else np.nan, frames_after_contact=(n - contact) if contact >= 0 else 0,
                identifiable=bool(contact >= 0 and n_flight >= 3 and held and not jump))
