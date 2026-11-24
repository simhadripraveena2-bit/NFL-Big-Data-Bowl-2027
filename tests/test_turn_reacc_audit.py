"""Tests for the Phase 11.1 C re-acceleration window audit (synthetic data only)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nfl_bdb.features.turn_reacc_audit import (audit_turn, overlap_with_segment, post_exit_frames,  # noqa: E402
                                               reacc_window_frames, slope, turning_in_window)
from nfl_bdb.features.turn_recovery import TurnParams, detect_turns, with_  # noqa: E402

P = TurnParams()


def test_window_frames_match_stage1_definition():
    assert reacc_window_frames(10, 100, 200, P).tolist() == list(range(10, 16))     # 0.5 s -> 6 frames
    assert reacc_window_frames(10, 14, 200, P).tolist() == [10, 11, 12, 13]          # truncated by next turn
    assert len(reacc_window_frames(10, 12, 200, P)) == 0                              # < 3 frames
    assert reacc_window_frames(10, 100, 13, P).tolist() == [10, 11, 12]              # recording end


def test_overlap_categories():
    f = np.arange(10, 16)
    assert overlap_with_segment(f, 5, 20)["category"] == "inside"
    o = overlap_with_segment(f, 5, 12)
    assert o["category"] == "partial" and o["n_inside"] == 3 and o["frac_inside"] == pytest.approx(0.5)
    assert overlap_with_segment(f, 0, 9)["category"] == "after"
    assert overlap_with_segment(f, 0, 9)["frac_inside"] == 0.0
    assert overlap_with_segment(np.array([], int), 0, 9)["category"] == "no_window"


def test_post_exit_frames_rules():
    f, why = post_exit_frames(20, 100, 200, P)
    assert why == "" and f.tolist() == list(range(21, 27))
    assert post_exit_frames(20, 26, 200, P)[1] == "next_turn"       # window would touch the next turn's start
    assert post_exit_frames(20, 27, 200, P)[1] == ""
    assert post_exit_frames(20, 100, 26, P)[1] == "recording_ends"
    assert post_exit_frames(20, 100, 27, P)[1] == ""


def test_slope_recovers_linear_speed():
    sp = 1.0 + 3.0 * np.arange(40) / 10.0
    assert slope(sp, np.arange(5, 11), 10.0) == pytest.approx(3.0)
    assert np.isnan(slope(sp, np.arange(5, 7), 10.0))


def test_turning_diagnostics_straight_vs_circle():
    n = 30
    sp = 2.0 + 0.3 * np.arange(n)                               # straight-line acceleration
    om = np.zeros(n)
    d = turning_in_window(sp, om, np.arange(5, 11), P)
    assert d["normal_share"] == pytest.approx(0.0) and d["heading_change"] == 0.0 and d["share_turning"] == 0.0
    sp = np.full(n, 4.0)                                         # constant-speed circle at 90 deg/s
    om = np.full(n, 90.0)
    d = turning_in_window(sp, om, np.arange(5, 11), P)
    assert d["normal_share"] == pytest.approx(1.0)
    assert d["heading_change"] == pytest.approx(90.0 * 6 / 10.0)
    assert d["share_turning"] == 1.0 and d["mean_abs_omega"] == pytest.approx(90.0)
    assert np.isnan(turning_in_window(sp, om, np.array([], int), P)["normal_share"])


def _loop(v_in=4.0, v_min=1.0, v_out=5.0, n_in=20, n_turn=12, n_out=25, total=170.0):
    half = n_turn // 2
    sp = np.r_[np.full(n_in, v_in), np.linspace(v_in, v_min, half), np.linspace(v_min, v_out, n_turn - half), np.linspace(v_out, v_out + 2, n_out)]
    hd = np.r_[np.zeros(n_in), np.linspace(0, total, n_turn), np.full(n_out, total)]
    h = np.radians(hd)
    x = np.r_[0, np.cumsum(sp[:-1] * np.cos(h[:-1])) / 10]; y = np.r_[0, np.cumsum(sp[:-1] * np.sin(h[:-1])) / 10]
    return x, y, sp


@pytest.mark.parametrize("src", ["pos", "provided", "provided_sg"])
def test_candidate_a_equals_stage1_reacc_and_b_is_after_exit(src):
    p = with_(P, speed_source=src)
    x, y, s = _loop()
    r = detect_turns(x, y, s, p)
    assert len(r["turns"]) == 1
    t = r["turns"][0]
    au = audit_turn(r["kin"]["speed"], t, len(x), len(x), p, omega_deg=r["kin"]["omega_deg"])
    assert au["cand_a"] == pytest.approx(t["reacc"], abs=1e-12)
    assert au["b_lo"] == t["end"] + 1 and au["b_reason"] == ""
    assert au["a_category"] in ("inside", "partial")
    # after the exit the synthetic path is straight; only the Savitzky-Golay tail of the heading change
    # remains (window 7: about 8 deg, mean |omega| about 13 deg/s), far less than inside the A window
    assert abs(au["b_heading_change"]) < 10 and au["b_mean_abs_omega"] < 20
    assert au["b_heading_change"] < au["a_heading_change"] / 3
    assert au["cand_b"] > 0
