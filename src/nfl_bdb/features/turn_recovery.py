"""Phase 11 (measurement feasibility only): turn detection and speed-retention / recovery features on the
10 Hz NFL Combine three-cone trajectories.

Nothing in this module touches game outcomes. It turns one tracked attempt (x, y, provided speed s) into a
list of detected turns with candidate features:

    entry speed      v_entry   max speed in the approach window before the turn's speed minimum
    minimum speed    v_min     speed at the turn's minimum
    retention        v_min / v_entry
    recovery time    time from the minimum until speed first regains ``recovery_frac`` * v_entry
                     (censored if the athlete does not regain it before the next turn starts)
    re-acceleration  slope of a linear fit of speed on time over ``reacc_window`` s after the minimum
    duration         time spent in the turn segment (frames flagged as turning)
    heading change   angle between the entry and exit directions (0-180 deg, chord definition)
                     plus the cumulative absolute heading change along the segment (can exceed 180)

Turn segmentation (per attempt; frames are never treated as independent observations):
  1. Smooth positions with a Savitzky-Golay filter (``window``, ``poly``); velocity from the SG derivative.
  2. A frame is *turning* if |heading rate| >= ``omega_min_deg`` deg/s, or if position-derived speed is
     below ``v_stop`` (heading is undefined near a stop, e.g. a touch-and-return reversal).
  3. Contiguous turning frames form a candidate segment; segments separated by <= ``merge_gap`` frames
     are merged. Segments that touch the first frame (recording starts at rest or mid-turn) are dropped
     and the attempt is flagged ``truncated_start``.
  4. A candidate is a turn only if the entry/exit chord heading change >= ``min_turn_deg``.
  5. Turns are labelled against the three-cone template R1, R2 (touch reversals), B1 (around cone B),
     C (around cone C), B2 (around cone B again); see ``label_three_cone``. Attempts that do not match
     are kept, unlabelled.

Speed source: "pos" (SG derivative of x, y; reference), "provided" (vendor ``s``), "provided_sg"
(SG-smoothed vendor ``s``). Heading is always taken from the smoothed positions.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace

import numpy as np
from scipy.signal import savgol_filter

TEMPLATE = ("R1", "R2", "B1", "C", "B2")


@dataclass(frozen=True)
class TurnParams:
    window: int = 7              # SG window (frames)
    poly: int = 2
    speed_source: str = "pos"    # "pos" | "provided" | "provided_sg"
    omega_min_deg: float = 60.0  # heading rate (deg/s) above which a frame counts as turning
    v_stop: float = 1.0          # yd/s; below this the heading is undefined and the frame counts as turning
    merge_gap: int = 2           # frames
    min_turn_deg: float = 45.0   # minimum chord heading change for a turn
    dir_frames: int = 3          # frames used to define entry / exit directions
    entry_window: float = 2.0    # s before the minimum searched for the entry speed (also bounded by the previous turn's minimum)
    recovery_frac: float = 0.9
    reacc_window: float = 0.5    # s after the minimum for the re-acceleration slope
    fs: float = 10.0

    def label(self) -> str:
        return (f"w{self.window}_{self.speed_source}_om{self.omega_min_deg:g}_vs{self.v_stop:g}"
                f"_ew{self.entry_window:g}_rf{self.recovery_frac:g}_ra{self.reacc_window:g}")


def kinematics(x, y, s, p: TurnParams) -> dict:
    """Smoothed kinematics for one attempt. Returns dict of arrays (speed, speed_pos, vx, vy, omega_deg)."""
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
    theta = np.unwrap(np.arctan2(vy, vx))
    omega = np.degrees(np.gradient(theta, dt))
    return dict(speed=speed, speed_pos=speed_pos, vx=vx, vy=vy, theta=theta, omega_deg=omega)


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    idx = np.flatnonzero(mask)
    if len(idx) == 0:
        return []
    br = np.flatnonzero(np.diff(idx) > 1)
    starts = np.r_[idx[0], idx[br + 1]]; ends = np.r_[idx[br], idx[-1]]
    return list(zip(starts.tolist(), ends.tolist()))


def _merge(runs, gap):
    out = []
    for a, b in runs:
        if out and a - out[-1][1] - 1 <= gap:
            out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    return out


def _unit_dir(vx, vy, sp, idx, v_min):
    idx = [i for i in idx if 0 <= i < len(vx) and sp[i] >= v_min]
    if not idx:
        return None
    v = np.array([vx[idx].sum(), vy[idx].sum()])
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else None


def detect_turns(x, y, s, p: TurnParams = TurnParams()) -> dict:
    """Detect turns in one attempt. Returns dict(ok, reason, flags, turns=[...], labels, template_ok, kin)."""
    n = len(x)
    if n < max(p.window + 2, 20):
        return dict(ok=False, reason="too_short", turns=[], flags={}, template_ok=False)
    k = kinematics(x, y, s, p)
    sp, spp = k["speed"], k["speed_pos"]
    if np.nanmax(spp) < 2.0:
        return dict(ok=False, reason="no_movement", turns=[], flags={}, template_ok=False)
    turning = (np.abs(k["omega_deg"]) >= p.omega_min_deg) | (spp < p.v_stop)
    runs = _merge(_runs(turning), p.merge_gap)
    flags = dict(truncated_start=False, truncated_end=False)
    turns = []
    for a, b in runs:
        if a == 0:
            flags["truncated_start"] = True
            continue
        if b >= n - 1:
            flags["truncated_end"] = True
            continue
        d_in = _unit_dir(k["vx"], k["vy"], spp, range(a - p.dir_frames, a), p.v_stop)
        d_out = _unit_dir(k["vx"], k["vy"], spp, range(b + 1, b + 1 + p.dir_frames), p.v_stop)
        if d_in is None or d_out is None:
            continue
        chord = float(np.degrees(np.arccos(np.clip(d_in @ d_out, -1.0, 1.0))))
        if chord < p.min_turn_deg:
            continue
        seg = np.arange(max(a - 1, 0), min(b + 2, n))
        good = seg[spp[seg] >= p.v_stop]
        cum = float(np.degrees(np.abs(np.diff(k["theta"][good])).sum())) if len(good) > 1 else np.nan
        i_min = int(seg[np.argmin(sp[seg])])
        turns.append(dict(start=a, end=b, i_min=i_min, chord_deg=chord, cum_heading_deg=cum,
                          duration=(b - a + 1) / p.fs))
    # features need neighbours (previous minimum, next turn start)
    for j, t in enumerate(turns):
        prev_min = turns[j - 1]["i_min"] if j > 0 else 0
        nxt = turns[j + 1]["start"] if j + 1 < len(turns) else n
        lo = max(prev_min + 1, t["i_min"] - int(round(p.entry_window * p.fs)))
        win = np.arange(lo, t["i_min"] + 1)
        i_e = int(win[np.argmax(sp[win])])
        v_e, v_m = float(sp[i_e]), float(sp[t["i_min"]])
        t.update(i_entry=i_e, v_entry=v_e, v_min=v_m, retention=v_m / v_e if v_e > 0 else np.nan,
                 entry_at_window_edge=bool(i_e == lo and lo > prev_min + 1))
        # recovery: first crossing of recovery_frac * v_entry after the minimum, before the next turn starts
        target = p.recovery_frac * v_e
        rec = np.nan; censored = True
        if v_m >= target:                       # speed never dropped below the target: no loss to recover
            rec, censored = 0.0, False
        for i in ([] if not censored else range(t["i_min"] + 1, nxt)):
            if sp[i] >= target:
                frac = (target - sp[i - 1]) / (sp[i] - sp[i - 1]) if sp[i] > sp[i - 1] else 1.0
                rec = (i - 1 + frac - t["i_min"]) / p.fs; censored = False
                break
        t.update(recovery_time=rec, recovery_censored=censored)
        m = int(round(p.reacc_window * p.fs))
        hi = min(t["i_min"] + m, nxt - 1, n - 1)
        if hi - t["i_min"] >= 2:
            ii = np.arange(t["i_min"], hi + 1)
            t.update(reacc=float(np.polyfit(ii / p.fs, sp[ii], 1)[0]), reacc_frames=int(len(ii)))
        else:
            t.update(reacc=np.nan, reacc_frames=int(max(hi - t["i_min"] + 1, 0)))
        t["near_stop"] = bool(v_m < p.v_stop)
    labels, template_ok = label_three_cone(turns)
    for t, lab in zip(turns, labels):
        t["label"] = lab
    return dict(ok=True, reason="", turns=turns, flags=flags, template_ok=template_ok, kin=k)


def label_three_cone(turns: list[dict]) -> tuple[list[str | None], bool]:
    """Label turns against the three-cone template.

    Core (required, in order): R1 and R2 = the first two turns, both touch reversals (chord >= 135 deg and
    minimum speed below v_stop, i.e. ``near_stop``); C = the next turn with chord >= 90 deg after R2.
    Optional: a 45-90 deg curve between R2 and C is B1; one after C is B2 (the curves around cone B often
    show no speed loss and may not be detected). Any other turn makes the attempt non-template.
    Returns (labels, template_ok); labels are all None when the core is not matched."""
    none = [None] * len(turns)
    if len(turns) < 3:
        return none, False
    h = [t["chord_deg"] for t in turns]
    rev = [h[i] >= 135 and t.get("near_stop", False) for i, t in enumerate(turns)]
    if not (rev[0] and rev[1]):
        return none, False
    labels = ["R1", "R2"]
    i = 2
    if i < len(turns) and 45 <= h[i] < 90:
        labels.append("B1"); i += 1
    if i >= len(turns) or h[i] < 90:
        return none, False
    labels.append("C"); i += 1
    if i < len(turns) and 45 <= h[i] < 90:
        labels.append("B2"); i += 1
    if i != len(turns):
        return none, False
    return labels, True


def params_dict(p: TurnParams) -> dict:
    return asdict(p)


def with_(p: TurnParams, **kw) -> TurnParams:
    return replace(p, **kw)
