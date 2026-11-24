"""Phase 11.1 (measurement audit only): where does the C re-acceleration window sit relative to the
detected C turning segment, and a diagnostic post-exit slope.

This module does NOT change the Stage 1 feature (``turn_recovery.detect_turns`` -> ``reacc``, here called
candidate A). It re-derives the exact frames that candidate A regresses on, measures their overlap with the
detected turning segment, and computes an independent diagnostic, candidate B:

  candidate A  post-minimum speed slope   OLS slope of speed on time over frames
               [i_min, min(i_min + m, next_start - 1, n - 1)], m = round(reacc_window * fs), >= 3 frames
               (identical to Stage 1).
  candidate B  post-turn-exit speed slope OLS slope over frames [end + 1, end + 1 + m]; usable only if all
               m + 1 frames exist (end + 1 + m <= n - 1) and none reaches the next detected turn
               (end + 1 + m < next_start). Same speed source and same number of frames as a full A window.

Nothing here touches NFL game data.
"""
from __future__ import annotations

import numpy as np

from nfl_bdb.features.turn_recovery import TurnParams


def reacc_window_frames(i_min: int, next_start: int, n: int, p: TurnParams) -> np.ndarray:
    """Frames used by the Stage 1 re-acceleration regression (candidate A). Empty if < 3 frames."""
    m = int(round(p.reacc_window * p.fs))
    hi = min(i_min + m, next_start - 1, n - 1)
    if hi - i_min < 2:
        return np.array([], dtype=int)
    return np.arange(i_min, hi + 1)


def overlap_with_segment(frames: np.ndarray, start: int, end: int) -> dict:
    """Share of regression frames inside the detected turning segment [start, end] (inclusive)."""
    if len(frames) == 0:
        return dict(n_frames=0, n_inside=0, frac_inside=np.nan, category="no_window")
    inside = int(((frames >= start) & (frames <= end)).sum())
    frac = inside / len(frames)
    if inside == len(frames):
        cat = "inside"
    elif inside == 0:
        cat = "after" if frames[0] > end else "before"
    else:
        cat = "partial"
    return dict(n_frames=int(len(frames)), n_inside=inside, frac_inside=float(frac), category=cat)


def post_exit_frames(end: int, next_start: int, n: int, p: TurnParams) -> tuple[np.ndarray, str]:
    """Frames for candidate B and a reason code ('' if usable)."""
    m = int(round(p.reacc_window * p.fs))
    lo, hi = end + 1, end + 1 + m
    if hi > n - 1:
        return np.array([], dtype=int), "recording_ends"
    if hi >= next_start:
        return np.array([], dtype=int), "next_turn"
    return np.arange(lo, hi + 1), ""


def slope(speed: np.ndarray, frames: np.ndarray, fs: float) -> float:
    if len(frames) < 3:
        return np.nan
    return float(np.polyfit(frames / fs, speed[frames], 1)[0])


def turning_in_window(speed: np.ndarray, omega_deg: np.ndarray, frames: np.ndarray, p: TurnParams) -> dict:
    """How much the athlete is still turning inside a regression window.

    mean_abs_omega   mean |heading rate| (deg/s) over the window frames
    share_turning    share of frames with |heading rate| >= p.omega_min_deg (the Stage 1 turning rule)
    heading_change   |sum of heading rate| * dt over the window (deg)
    normal_share     sum (v*omega)^2 / sum[(v*omega)^2 + (dv/dt)^2]: share of squared acceleration that is
                     centripetal (direction change) rather than tangential (speed change), dv/dt by central
                     differences of the same speed series."""
    if len(frames) == 0:
        return dict(mean_abs_omega=np.nan, share_turning=np.nan, heading_change=np.nan, normal_share=np.nan)
    om = np.asarray(omega_deg, float)[frames]
    at = np.gradient(np.asarray(speed, float), 1.0 / p.fs)[frames]
    an = np.asarray(speed, float)[frames] * np.radians(om)
    den = float((an ** 2 + at ** 2).sum())
    return dict(mean_abs_omega=float(np.abs(om).mean()), share_turning=float((np.abs(om) >= p.omega_min_deg).mean()),
                heading_change=float(abs(om.sum()) / p.fs), normal_share=float((an ** 2).sum() / den) if den > 0 else np.nan)


def audit_turn(speed: np.ndarray, turn: dict, next_start: int, n: int, p: TurnParams, omega_deg=None) -> dict:
    """Window audit + both candidates for one detected turn (dict from ``detect_turns``).
    If ``omega_deg`` (heading rate, deg/s) is given, turning diagnostics for both windows are added."""
    fa = reacc_window_frames(turn["i_min"], next_start, n, p)
    ov = overlap_with_segment(fa, turn["start"], turn["end"])
    fb, reason = post_exit_frames(turn["end"], next_start, n, p)
    extra = {}
    if omega_deg is not None:
        extra.update({f"a_{k}": v for k, v in turning_in_window(speed, omega_deg, fa, p).items()})
        extra.update({f"b_{k}": v for k, v in turning_in_window(speed, omega_deg, fb, p).items()})
    return dict(**extra,
        start=turn["start"], end=turn["end"], i_min=turn["i_min"],
        a_lo=int(fa[0]) if len(fa) else -1, a_hi=int(fa[-1]) if len(fa) else -1,
        a_n_frames=ov["n_frames"], a_n_inside=ov["n_inside"], a_frac_inside=ov["frac_inside"], a_category=ov["category"],
        cand_a=slope(speed, fa, p.fs),
        frames_min_to_exit=int(turn["end"] - turn["i_min"]),
        b_lo=int(fb[0]) if len(fb) else -1, b_hi=int(fb[-1]) if len(fb) else -1, b_reason=reason,
        cand_b=slope(speed, fb, p.fs) if len(fb) else np.nan,
        v_exit=float(speed[turn["end"] + 1]) if turn["end"] + 1 < n else np.nan,
    )
