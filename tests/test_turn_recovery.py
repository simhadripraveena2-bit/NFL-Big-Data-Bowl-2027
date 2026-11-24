"""Unit tests for Phase 11 turn detection / recovery features and repeatability helpers (synthetic data only)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nfl_bdb.evaluation.repeatability import (boot_two_attempt, centre_by_group, icc1_unbalanced,
                                              two_attempt_stats)  # noqa: E402
from nfl_bdb.features.turn_recovery import TurnParams, detect_turns, label_three_cone, with_  # noqa: E402

FS = 10.0


def path_from_speed_heading(speed, heading_deg, x0=0.0, y0=0.0):
    """Integrate a speed / heading profile at 10 Hz into x, y (heading in math convention, degrees)."""
    h = np.radians(heading_deg)
    vx, vy = speed * np.cos(h), speed * np.sin(h)
    x = x0 + np.r_[0, np.cumsum(vx[:-1]) / FS]
    y = y0 + np.r_[0, np.cumsum(vy[:-1]) / FS]
    return x, y


def reversal_profile(v_in=4.0, v_turn=0.2, v_out=4.0, n_in=20, n_dec=8, n_acc=8, n_out=20):
    """Straight run, decelerate to ~stop, reverse direction (180 deg), accelerate, straight run."""
    sp = np.r_[np.full(n_in, v_in), np.linspace(v_in, v_turn, n_dec), np.linspace(v_turn, v_out, n_acc), np.full(n_out, v_out)]
    hd = np.r_[np.zeros(n_in + n_dec), np.full(n_acc + n_out, 180.0)]
    return sp, hd


def loop_profile(v_in=4.0, v_min=1.0, v_out=4.0, n_in=20, n_turn=12, n_out=25, total_deg=170.0):
    """Curved turn: speed dips to v_min mid-turn while heading sweeps ``total_deg`` degrees."""
    half = n_turn // 2
    sp = np.r_[np.full(n_in, v_in), np.linspace(v_in, v_min, half), np.linspace(v_min, v_out, n_turn - half), np.full(n_out, v_out)]
    hd = np.r_[np.zeros(n_in), np.linspace(0, total_deg, n_turn), np.full(n_out, total_deg)]
    return sp, hd


def test_single_reversal_detected_with_near_zero_retention():
    sp, hd = reversal_profile()
    x, y = path_from_speed_heading(sp, hd)
    r = detect_turns(x, y, sp, TurnParams())
    assert r["ok"]
    assert len(r["turns"]) == 1
    t = r["turns"][0]
    assert t["chord_deg"] > 150
    assert t["near_stop"]
    assert t["retention"] < 0.25
    assert abs(t["v_entry"] - 4.0) < 0.2


def test_loop_turn_features():
    sp, hd = loop_profile(v_in=4.0, v_min=1.0, v_out=4.0)
    x, y = path_from_speed_heading(sp, hd)
    r = detect_turns(x, y, sp, TurnParams())
    assert len(r["turns"]) == 1
    t = r["turns"][0]
    assert 140 < t["chord_deg"] <= 180
    assert 0.15 < t["retention"] < 0.45                      # ~1/4 after smoothing
    assert not t["recovery_censored"]
    # 6 frames from 1.0 to 4.0 yd/s: 0.9*4 = 3.6 is reached ~0.45-0.6 s after the minimum
    assert 0.3 < t["recovery_time"] < 0.8
    assert 3.0 < t["reacc"] < 7.0                            # 3 yd/s over 0.6 s -> 5 yd/s^2


def test_recovery_censored_when_next_turn_comes_first():
    sp1, hd1 = reversal_profile(n_out=3, v_out=2.0, n_acc=4)
    sp2, hd2 = reversal_profile(v_in=2.0, n_in=1)
    sp = np.r_[sp1, sp2]; hd = np.r_[hd1, hd2 + 180.0]
    x, y = path_from_speed_heading(sp, hd)
    r = detect_turns(x, y, sp, TurnParams())
    assert len(r["turns"]) == 2
    assert r["turns"][0]["recovery_censored"]
    assert np.isnan(r["turns"][0]["recovery_time"])
    assert not r["turns"][1]["recovery_censored"]


def test_no_speed_loss_gives_zero_recovery_not_censored():
    sp = np.full(60, 4.0)
    hd = np.r_[np.zeros(20), np.linspace(0, 70, 10), np.full(30, 70.0)]
    x, y = path_from_speed_heading(sp, hd)
    r = detect_turns(x, y, sp, TurnParams())
    assert len(r["turns"]) == 1
    t = r["turns"][0]
    assert 45 <= t["chord_deg"] < 90
    assert t["recovery_time"] == 0.0 and not t["recovery_censored"]
    assert t["retention"] > 0.95


def test_straight_line_has_no_turns_and_noise_does_not_create_turns():
    rng = np.random.default_rng(0)
    sp = np.r_[np.linspace(0.5, 7.0, 30), np.full(30, 7.0)]
    x, y = path_from_speed_heading(sp, np.zeros(60))
    x = x + rng.normal(0, 0.01, len(x)); y = y + rng.normal(0, 0.01, len(y))
    r = detect_turns(x, y, sp, TurnParams())
    assert r["ok"] and r["turns"] == []


def test_start_at_rest_is_flagged_truncated_and_not_a_turn():
    sp = np.r_[np.zeros(5), np.linspace(0, 5, 15), np.full(30, 5.0)]
    x, y = path_from_speed_heading(sp, np.zeros(len(sp)))
    r = detect_turns(x, y, sp, TurnParams())
    assert r["flags"]["truncated_start"]
    assert r["turns"] == []


def test_end_in_turn_is_truncated():
    sp, hd = reversal_profile(n_acc=2, n_out=0, v_out=0.5)
    x, y = path_from_speed_heading(sp, hd)
    r = detect_turns(x, y, sp, TurnParams())
    assert r["flags"]["truncated_end"]
    assert r["turns"] == []


def test_too_short_and_no_movement():
    assert detect_turns(np.zeros(10), np.zeros(10), np.zeros(10))["reason"] == "too_short"
    z = np.zeros(40)
    assert detect_turns(z, z, z)["reason"] == "no_movement"


def test_speed_source_options_and_invalid():
    sp, hd = loop_profile()
    x, y = path_from_speed_heading(sp, hd)
    for src in ("pos", "provided", "provided_sg"):
        assert len(detect_turns(x, y, sp, with_(TurnParams(), speed_source=src))["turns"]) == 1
    with pytest.raises(ValueError):
        detect_turns(x, y, sp, with_(TurnParams(), speed_source="bogus"))


def synthetic_three_cone():
    """R1 (reversal), R2 (reversal), B1 (curve, no loss), C (loop with dip), B2 (curve, no loss)."""
    segs = []
    s, h = reversal_profile(v_in=3.0, n_in=15, n_out=8, v_out=3.0); segs.append((s, h))
    s, h = reversal_profile(v_in=3.0, n_in=0, n_out=10, v_out=4.0); segs.append((s, h + 180))
    s = np.full(25, 4.0); h = np.r_[np.full(8, 360.0), np.linspace(360, 430, 8), np.full(9, 430.0)]; segs.append((s, h))
    s, h = loop_profile(v_in=4.0, v_min=1.0, v_out=4.0, n_in=8, n_out=10); segs.append((s, h + 430))
    s = np.full(30, 4.5); h = np.r_[np.full(8, 600.0), np.linspace(600, 670, 8), np.full(14, 670.0)]; segs.append((s, h))
    sp = np.concatenate([a for a, _ in segs]); hd = np.concatenate([b for _, b in segs])
    return sp, hd


def test_three_cone_template_labelling():
    sp, hd = synthetic_three_cone()
    x, y = path_from_speed_heading(sp, hd)
    r = detect_turns(x, y, sp, TurnParams())
    assert r["template_ok"], [(round(t["chord_deg"]), t["near_stop"]) for t in r["turns"]]
    assert [t["label"] for t in r["turns"]] == ["R1", "R2", "B1", "C", "B2"]
    c = next(t for t in r["turns"] if t["label"] == "C")
    assert c["retention"] < 0.5 and not c["recovery_censored"]


def test_label_rules():
    mk = lambda h, ns: dict(chord_deg=h, near_stop=ns)
    assert label_three_cone([mk(170, True), mk(160, True), mk(165, False)]) == (["R1", "R2", "C"], True)
    assert label_three_cone([mk(170, True), mk(160, True), mk(60, False), mk(165, False), mk(60, False)])[0] == ["R1", "R2", "B1", "C", "B2"]
    # first turn not a stop reversal -> non-template
    assert label_three_cone([mk(170, False), mk(160, True), mk(165, False)]) == ([None] * 3, False)
    # missing C
    assert label_three_cone([mk(170, True), mk(160, True), mk(60, False)])[1] is False
    # extra turn after B2
    assert label_three_cone([mk(170, True), mk(160, True), mk(165, False), mk(60, False), mk(150, True)])[1] is False


# ---------------- repeatability helpers ----------------

def test_two_attempt_stats_perfect_and_noise():
    rng = np.random.default_rng(1)
    t = rng.normal(0, 1, 200)
    st = two_attempt_stats(t, t + 0.0)
    assert st["icc31"] == pytest.approx(1.0) and st["te"] == pytest.approx(0.0)
    a = t + rng.normal(0, 1, 200); b = t + rng.normal(0, 1, 200)
    st = two_attempt_stats(a, b)
    assert 0.35 < st["icc31"] < 0.65                     # true ICC 0.5
    assert st["te"] == pytest.approx(1.0, abs=0.15)       # within-subject SD
    ci = boot_two_attempt(a, b, B=200, seed=3)
    assert ci["icc31"][0] < st["icc31"] < ci["icc31"][1]


def test_icc31_ignores_systematic_shift_but_icc21_does_not():
    rng = np.random.default_rng(2)
    t = rng.normal(0, 1, 300)
    a = t + rng.normal(0, 0.3, 300); b = t + 1.0 + rng.normal(0, 0.3, 300)
    st = two_attempt_stats(a, b)
    assert st["icc31"] > 0.8 and st["icc21"] < st["icc31"] - 0.1


def test_centre_by_group_removes_position_inflation():
    rng = np.random.default_rng(3)
    g = np.repeat(["A", "B"], 100)
    level = np.where(g == "A", 0.0, 5.0)
    a = level + rng.normal(0, 1, 200); b = level + rng.normal(0, 1, 200)   # no within-group signal
    assert two_attempt_stats(a, b)["icc31"] > 0.8
    ac, bc = centre_by_group(a, b, g)
    assert abs(two_attempt_stats(ac, bc)["icc31"]) < 0.25


def test_icc1_unbalanced():
    rng = np.random.default_rng(4)
    vals = []
    for _ in range(300):
        mu = rng.normal(0, 1); k = rng.choice([2, 3])
        vals.append(mu + rng.normal(0, 1, k))
    assert icc1_unbalanced(vals)["icc1"] == pytest.approx(0.5, abs=0.12)
    assert np.isnan(icc1_unbalanced([np.array([1.0, 2.0])])["icc1"])
