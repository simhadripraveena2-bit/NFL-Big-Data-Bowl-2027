"""Phase 12 (measurement feasibility only): straight-exit acceleration after the touch reversals of the
NFL Combine short shuttle (5-10-5), from 10 Hz tracking.

This is a new, separately defined shuttle measurement. It is not the Phase 11 three-cone feature.
Nothing here touches NFL game data.

Geometry
--------
The shuttle is run along one line (the drill axis, estimated as the first principal direction of the
attempt's x, y positions). Velocity is projected on that axis: u = v . e.

* Legs are runs of frames with |u| >= ``leg_speed`` and a constant sign. A **reversal** sits between two
  consecutive legs of opposite sign. R1 = first reversal, R2 = second.
* Heading is defined only where speed >= ``v_head``. A frame is **straight for direction d** (d = +-1 along
  e) if speed >= v_head and the angle between its velocity and d*e is <= ``straight_deg``.
* Turn region of a reversal: from the frame after the last straight *incoming* frame (at or before the
  speed minimum) to the frame before the first straight *outgoing* frame k0 (after the minimum).
* Measurement window: frames k0 ... k0 + m (shifted by ``start_offset`` in sensitivity runs only), m = round(reg_window * fs) (6 frames = 0.5 s at 10 Hz).
  The slope of speed on time (OLS) is the **straight-exit acceleration**. The window starts at k0 by
  construction, so it never contains a turning frame as defined above; the window is VALID only if every
  window frame is itself straight for the outgoing direction, the window lies inside the recording, and it
  ends before the next reversal's turn region starts, and at least ``approach_frames`` straight incoming
  frames precede the turn (an observed approach).

Validity is never relaxed to gain observations; invalid windows are reported with their reason.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace

import numpy as np
from scipy.signal import savgol_filter


@dataclass(frozen=True)
class ShuttleParams:
    window: int = 7               # Savitzky-Golay window (frames)
    poly: int = 2
    speed_source: str = "pos"     # "pos" | "provided" | "provided_sg"
    v_head: float = 1.0           # yd/s; heading undefined below this
    straight_deg: float = 15.0    # max angle between velocity and the drill axis for a "straight" frame
    leg_speed: float = 1.5        # yd/s along the axis that defines a leg
    min_leg_frames: int = 3       # a leg needs at least this many frames
    approach_frames: int = 5      # straight incoming frames needed before the turn (observed approach)
    reg_window: float = 0.5       # s
    entry_window: float = 1.0     # s before the minimum searched for the entry speed
    start_offset: int = 0         # frames between k0 and the window start (sensitivity only; reference 0)
    fs: float = 10.0


def drill_axis(x, y) -> np.ndarray:
    """Unit vector of the first principal direction of the positions (sign: +x half-plane)."""
    P = np.column_stack([np.asarray(x, float), np.asarray(y, float)])
    P = P - P.mean(axis=0)
    _, _, vt = np.linalg.svd(P, full_matrices=False)
    e = vt[0]
    return e if e[0] >= 0 else -e


def kinematics(x, y, s, p: ShuttleParams) -> dict:
    x = np.asarray(x, float); y = np.asarray(y, float); s = np.asarray(s, float)
    dt = 1.0 / p.fs
    vx = savgol_filter(x, p.window, p.poly, deriv=1, delta=dt)
    vy = savgol_filter(y, p.window, p.poly, deriv=1, delta=dt)
    speed_pos = np.hypot(vx, vy)
    if p.speed_source == "pos":
        speed = speed_pos
    elif p.speed_source == "provided":
        speed = s.copy()
    elif p.speed_source == "provided_sg":
        speed = np.maximum(savgol_filter(s, p.window, p.poly), 0.0)
    else:
        raise ValueError(p.speed_source)
    e = drill_axis(x, y)
    u = vx * e[0] + vy * e[1]
    theta = np.unwrap(np.arctan2(vy, vx))
    omega = np.degrees(np.gradient(theta, dt))
    return dict(speed=speed, speed_pos=speed_pos, vx=vx, vy=vy, u=u, axis=e, omega_deg=omega)


def deviation_deg(vx, vy, u, d: int) -> np.ndarray:
    """Angle (deg) between each velocity and direction d*axis; u is the axis projection."""
    sp = np.hypot(vx, vy)
    with np.errstate(invalid="ignore", divide="ignore"):
        c = np.where(sp > 0, d * u / sp, -1.0)
    return np.degrees(np.arccos(np.clip(c, -1.0, 1.0)))


def legs(u: np.ndarray, p: ShuttleParams) -> list[tuple[int, int, int]]:
    """(start, end, sign) of runs with |u| >= leg_speed and constant sign, >= min_leg_frames long."""
    sign = np.where(u >= p.leg_speed, 1, np.where(u <= -p.leg_speed, -1, 0))
    out, i, n = [], 0, len(u)
    while i < n:
        if sign[i] == 0:
            i += 1; continue
        j = i
        while j + 1 < n and sign[j + 1] == sign[i]:
            j += 1
        if j - i + 1 >= p.min_leg_frames:
            out.append((i, j, int(sign[i])))
        i = j + 1
    # merge same-sign legs separated by a dip below leg_speed (no reversal in between)
    merged = []
    for lg in out:
        if merged and merged[-1][2] == lg[2]:
            merged[-1] = (merged[-1][0], lg[1], lg[2])
        else:
            merged.append(lg)
    return merged


def _straight(k, d, dev, sp, p):
    return sp[k] >= p.v_head and dev[d][k] <= p.straight_deg


def analyse_attempt(x, y, s, p: ShuttleParams = ShuttleParams()) -> dict:
    """Detect reversals and measure straight-exit acceleration after each. Returns
    dict(ok, reason, n_reversals, flags, reversals=[...], kin)."""
    n = len(x)
    if n < max(p.window + 2, 15):
        return dict(ok=False, reason="too_short", n_reversals=0, flags={}, reversals=[], kin=None)
    k = kinematics(x, y, s, p)
    sp, spp, u = k["speed"], k["speed_pos"], k["u"]
    lg = legs(u, p)
    flags = dict(start_moving=bool(spp[0] >= p.v_head), end_moving=bool(spp[-1] >= p.v_head), n_legs=len(lg))
    dev = {d: deviation_deg(k["vx"], k["vy"], u, d) for d in (1, -1)}
    m = int(round(p.reg_window * p.fs))
    revs = []
    for j in range(len(lg) - 1):
        (a0, a1, s_in), (b0, b1, s_out) = lg[j], lg[j + 1]
        if s_in == s_out:
            continue
        lo, hi = max(a1 - 1, 0), min(b0 + 1, n - 1)
        i_min = int(lo + np.argmin(sp[lo:hi + 1]))
        # last straight incoming frame at or before the minimum
        k_in = next((q for q in range(i_min, -1, -1) if _straight(q, s_in, dev, spp, p)), None)
        # first straight outgoing frame after the minimum (searched until the outgoing leg ends)
        k0 = next((q for q in range(i_min + 1, b1 + 1) if _straight(q, s_out, dev, spp, p)), None)
        r = dict(index=len(revs), i_min=i_min, v_min=float(sp[i_min]), leg_in=(a0, a1), leg_out=(b0, b1),
                 sign_in=s_in, sign_out=s_out)
        # approach: consecutive straight incoming frames ending at k_in
        n_app = 0
        if k_in is not None:
            q = k_in
            while q >= 0 and _straight(q, s_in, dev, spp, p):
                n_app += 1; q -= 1
        r["approach_frames"] = n_app
        r["approach_from_start"] = bool(k_in is not None and k_in - n_app + 1 == 0)
        e_lo = max(a0, i_min - int(round(p.entry_window * p.fs)))
        i_e = int(e_lo + np.argmax(sp[e_lo:i_min + 1]))
        r.update(i_entry=i_e, v_entry=float(sp[i_e]))
        turn_start = (k_in + 1) if k_in is not None else 0
        r["turn_start"] = turn_start
        if k0 is None:
            r.update(valid=False, reason="no_straight_exit", k0=-1)
            revs.append(r); continue
        r.update(k0=int(k0), turn_end=int(k0 - 1), turn_duration=(k0 - turn_start) / p.fs,
                 gap_min_to_window=(k0 - i_min) / p.fs, v_start=float(sp[k0]))
        d_in = np.array([k["vx"][turn_start - 1], k["vy"][turn_start - 1]]) if turn_start >= 1 else None
        d_out = np.array([k["vx"][k0], k["vy"][k0]])
        if d_in is not None and np.linalg.norm(d_in) > 0:
            c = d_in @ d_out / (np.linalg.norm(d_in) * np.linalg.norm(d_out))
            r["heading_change_deg"] = float(np.degrees(np.arccos(np.clip(c, -1, 1))))
        else:
            r["heading_change_deg"] = np.nan
        W = np.arange(k0 + p.start_offset, k0 + p.start_offset + m + 1)
        r["window"] = (int(W[0]), int(W[-1]))
        nxt_turn = None
        if j + 2 < len(lg) and lg[j + 2][2] != s_out:
            nxt_turn = b1 + 1        # the next reversal's region starts after this leg ends at the latest
        if n_app < p.approach_frames:
            r.update(valid=False, reason="approach_not_observed")
        elif W[-1] > n - 1:
            r.update(valid=False, reason="window_truncated_by_recording_end")
        elif nxt_turn is not None and W[-1] >= nxt_turn:
            r.update(valid=False, reason="window_reaches_next_reversal")
        else:
            straight = np.array([_straight(q, s_out, dev, spp, p) for q in W])
            r.update(valid=bool(straight.all()), reason="" if straight.all() else "window_not_straight")
        Wc = W[W <= n - 1]
        if len(Wc) < 2:
            r.update(window_frames=int(len(Wc)), accel=np.nan, leg_peak_in_window=False, window_overlaps_turn=False)
            revs.append(r); continue
        r.update(window_frames=int(len(Wc)), window_max_dev_deg=float(dev[s_out][Wc].max()),
                 window_max_abs_omega=float(np.abs(k["omega_deg"][Wc]).max()),
                 window_heading_change_deg=float(abs(k["omega_deg"][Wc].sum()) / p.fs),
                 window_straightness=_straightness(x, y, Wc),
                 window_lateral_range=_lateral_range(x, y, Wc, k["axis"]),
                 window_normal_share=_normal_share(sp, k["omega_deg"], Wc, p.fs),
                 accel=float(np.polyfit(Wc / p.fs, sp[Wc], 1)[0]) if len(Wc) >= 3 else np.nan)
        # is the outgoing leg's speed peak already reached inside the window?
        peak = int(b0 + np.argmax(sp[b0:b1 + 1]))
        r["leg_peak_in_window"] = bool(peak <= W[-1])
        r["window_overlaps_turn"] = bool(W[0] <= r["turn_end"])     # always False by construction
        revs.append(r)
    return dict(ok=True, reason="", n_reversals=len(revs), flags=flags, reversals=revs, kin=k)


def _normal_share(sp, omega_deg, W, fs) -> float:
    """Share of squared acceleration that is centripetal (v*omega) rather than tangential (dv/dt)."""
    at = np.gradient(np.asarray(sp, float), 1.0 / fs)[W]
    an = np.asarray(sp, float)[W] * np.radians(np.asarray(omega_deg, float)[W])
    den = float((an ** 2 + at ** 2).sum())
    return float((an ** 2).sum() / den) if den > 0 else np.nan


def _straightness(x, y, W) -> float:
    x = np.asarray(x, float)[W]; y = np.asarray(y, float)[W]
    path = np.hypot(np.diff(x), np.diff(y)).sum()
    return float(np.hypot(x[-1] - x[0], y[-1] - y[0]) / path) if path > 0 else np.nan


def _lateral_range(x, y, W, e) -> float:
    x = np.asarray(x, float)[W]; y = np.asarray(y, float)[W]
    perp = -x * e[1] + y * e[0]
    return float(perp.max() - perp.min())


def params_dict(p: ShuttleParams) -> dict:
    return asdict(p)


def with_(p: ShuttleParams, **kw) -> ShuttleParams:
    return replace(p, **kw)
