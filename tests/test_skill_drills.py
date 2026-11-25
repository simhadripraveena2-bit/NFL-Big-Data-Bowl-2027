"""Tests for Phase 14 skill-drill descriptors, curve metrics and the ball-phase parser (synthetic data)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nfl_bdb.features.skill_drills import ball_phases, curve_metrics, descriptors, harmonise, kinematics  # noqa: E402

FS = 10.0


def circle(v=4.0, R=2.0, secs=4.0, ccw=True):
    t = np.arange(0, secs, 1 / FS); w = v / R * (1 if ccw else -1)
    return 30 + R * np.cos(w * t), 20 + R * np.sin(w * t)


def test_centripetal_acceleration_on_circle():
    x, y = circle(4.0, 2.0)
    mid = slice(5, -5)
    # SG(order 2) smoothing attenuates speed on tight curves: ~5% at w=7 for R = 2 yd, v = 4 yd/s
    s5, s7, s9 = (np.median(kinematics(x, y, w)["speed"][mid]) for w in (5, 7, 9))
    assert s9 < s7 < s5 < 4.0 and s7 == pytest.approx(4.0, rel=0.06)
    k = kinematics(x, y, 7)
    assert np.median(k["a_n"][mid]) == pytest.approx(4.0 ** 2 / 2.0, rel=0.07)
    cm = curve_metrics(x, y, 7)
    assert cm["all_radius"] == pytest.approx(2.0, rel=0.07) and cm["all_a_n"] == pytest.approx(8.0, rel=0.07)
    assert cm["left_n"] > 20 and cm["right_n"] == 0
    cw = curve_metrics(*circle(4.0, 2.0, ccw=False), 7)
    assert cw["right_n"] > 20 and cw["left_n"] == 0


def test_descriptors_straight_run_and_shuttle():
    t = np.arange(0, 3, 0.1); v = np.minimum(2.5 * t, 6.0)
    x = 10 + np.cumsum(v) / FS; y = np.full_like(x, 5.0)
    d = descriptors(x, y, 7)
    assert d["ok"] and d["n_axis_reversals"] == 0
    assert d["peak_speed"] == pytest.approx(6.0, rel=0.05)
    assert d["total_heading_change_deg"] < 5 and d["extent_minor"] < 1e-6
    # out-and-back: one reversal along the axis
    u = np.r_[np.linspace(0, 4, 10), np.linspace(4, 0, 10), np.linspace(0, -4, 10), np.linspace(-4, 0, 10)]
    xb = np.cumsum(u) / FS
    assert descriptors(xb, np.zeros_like(xb), 7)["n_axis_reversals"] == 1
    assert descriptors(np.zeros(5), np.zeros(5), 7)["ok"] is False


def test_ball_phases_identifiable_catch_and_jump_flag():
    n = 50
    px = np.linspace(0, 20, n); py = np.zeros(n)                       # receiver runs along x at 4 yd/s
    bx = np.empty(n); by = np.empty(n)
    bx[:15] = -10; by[:15] = 10                                          # ball static at the passer
    k = np.arange(15, 30)                                                # flight: straight line to the receiver
    f = (k - 14) / 15.0
    bx[15:30] = -10 + f * (px[29] + 10); by[15:30] = 10 - f * 10
    bx[30:] = px[30:] + 0.3; by[30:] = 0.2                                # held
    r = ball_phases(px, py, bx, by)
    assert r["identifiable"] and r["held"] and not r["jump_near_contact"]
    assert 27 <= r["contact"] <= 30 and r["n_flight"] >= 10 and r["ball_static_before_throw"]
    # teleport right after contact: flagged, not identifiable
    bx2 = bx.copy(); bx2[r["contact"] + 1] += 5.0
    r2 = ball_phases(px, py, bx2, by)
    assert r2["jump_near_contact"] and not r2["identifiable"]
    # ball never reaches the receiver
    r3 = ball_phases(px, py, np.full(n, -10.0), np.full(n, 10.0))
    assert r3["contact"] == -1 and not r3["identifiable"]


def test_harmonise_only_listed_aliases():
    assert harmonise("SKILL_DRILLS_DB", "LINE") == "LINE_DRILL"
    assert harmonise("SKILL_DRILLS_WR", "POST_CORNER_ROUTE_LEFT") == "POST_CORNER_ROUTE_LEFT"
    assert harmonise("SKILL_DRILLS_DL", "SHORT_ZONE_BREAKS") == "SHORT_ZONE_BREAKS"
