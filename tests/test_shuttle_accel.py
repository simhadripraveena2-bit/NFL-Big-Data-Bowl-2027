"""Tests for the Phase 12 short-shuttle straight-exit acceleration measurement (synthetic data only)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nfl_bdb.features.shuttle_accel import (ShuttleParams, analyse_attempt, deviation_deg, drill_axis, legs,  # noqa: E402
                                            with_)

FS = 10.0
P = ShuttleParams()


def ramp(v0, v1, secs):
    return np.linspace(v0, v1, int(round(secs * FS)), endpoint=False)


def shuttle_u(a2=4.6):
    """Axis velocity of a synthetic 5-10-5: leg 1 (+), reversal, leg 2 (-) accelerating at a2, reversal, leg 3 (+)."""
    t_up2 = 5.5 / a2
    return np.r_[ramp(0.3, 3.2, 1.0), ramp(3.2, 0.0, 0.7),
                 ramp(0.0, -5.5, t_up2), ramp(-5.5, 0.0, 0.9),
                 ramp(0.0, 6.0, 1.1), np.full(3, 6.0)]


def path(u, angle_deg=10.0, lateral=None):
    """Integrate axis velocity along a line at ``angle_deg`` to +x; optional lateral velocity profile."""
    e = np.array([np.cos(np.radians(angle_deg)), np.sin(np.radians(angle_deg))]); nrm = np.array([-e[1], e[0]])
    w = np.zeros_like(u) if lateral is None else lateral
    vx = u * e[0] + w * nrm[0]; vy = u * e[1] + w * nrm[1]
    x = 40 + np.r_[0, np.cumsum(vx[:-1])] / FS; y = 20 + np.r_[0, np.cumsum(vy[:-1])] / FS
    return x, y, np.hypot(vx, vy)


def test_drill_axis_recovers_line_direction():
    x, y, _ = path(shuttle_u(), angle_deg=10.0)
    e = drill_axis(x, y)
    assert e[0] > 0
    assert np.degrees(np.arctan2(e[1], e[0])) == pytest.approx(10.0, abs=0.5)


def test_legs_and_merge():
    u = np.r_[np.full(5, 2.0), np.full(2, 1.0), np.full(5, 2.0), np.full(3, 0.0), np.full(6, -2.0), np.full(2, -3.0)]
    assert legs(u, P) == [(0, 11, 1), (15, 22, -1)]
    assert legs(np.r_[np.full(2, 2.0), np.zeros(5)], P) == []          # shorter than min_leg_frames


def test_deviation_deg():
    vx = np.array([1.0, 0.0, -1.0, 1.0]); vy = np.array([0.0, 1.0, 0.0, 1.0])
    u = vx.copy()                                                        # axis = +x
    np.testing.assert_allclose(deviation_deg(vx, vy, u, 1), [0, 90, 180, 45], atol=1e-9)
    np.testing.assert_allclose(deviation_deg(vx, vy, u, -1), [180, 90, 0, 135], atol=1e-9)


def test_two_reversals_valid_straight_windows_and_true_acceleration():
    a2 = 4.6
    x, y, s = path(shuttle_u(a2))
    r = analyse_attempt(x, y, s, P)
    assert r["ok"] and r["n_reversals"] == 2
    r1, r2 = r["reversals"]
    assert r1["sign_in"] == 1 and r1["sign_out"] == -1 and r2["sign_out"] == 1
    assert r1["valid"] and r2["valid"]
    # window does not overlap the turn region and is straight and centripetal-free
    assert not r1["window_overlaps_turn"] and r1["window"][0] == r1["k0"] > r1["turn_end"]
    assert r1["window_max_dev_deg"] <= P.straight_deg and r1["window_straightness"] > 0.999
    assert r1["window_normal_share"] < 0.01 and r1["window_frames"] == 6
    # the synthetic leg-2 ramp accelerates at a2; the SG estimate within 15 %
    assert r1["accel"] == pytest.approx(a2, rel=0.15)
    assert r1["v_entry"] == pytest.approx(3.2, abs=0.5)        # SG flattens the sharp synthetic peak
    assert 0.1 <= r1["gap_min_to_window"] <= 0.4
    assert r1["heading_change_deg"] > 150


def test_accel_tracks_planted_acceleration():
    lo = analyse_attempt(*path(shuttle_u(3.5)), P)["reversals"][0]["accel"]
    hi = analyse_attempt(*path(shuttle_u(6.0)), P)["reversals"][0]["accel"]
    assert lo == pytest.approx(3.5, rel=0.15) and hi == pytest.approx(6.0, rel=0.15) and hi > lo


def test_unobserved_approach_is_invalid():
    u = shuttle_u()[12:]                                  # recording starts 0.5 s before the first stop
    r = analyse_attempt(*path(u), P)
    r1 = r["reversals"][0]
    assert r1["approach_frames"] < P.approach_frames
    assert not r1["valid"] and r1["reason"] == "approach_not_observed"


def test_recording_end_truncates_second_window():
    u = shuttle_u()
    leg3 = len(u) - 14                                    # leg 3 starts at len - 14; keep only 7 frames of it
    r = analyse_attempt(*path(u[:leg3 + 7]), P)
    r2 = r["reversals"][1]
    assert not r2["valid"] and r2["reason"] == "window_truncated_by_recording_end"


def test_curved_exit_is_not_straight_or_starts_later():
    u = shuttle_u()
    i_rev = 17                                            # first reversal frame
    lat = np.zeros_like(u)
    lat[i_rev:i_rev + 10] = -2.5 * np.sin(np.linspace(0, np.pi, 10))   # sideways bulge just after the reversal
    r_curved = analyse_attempt(*path(u, lateral=lat), P)["reversals"][0]
    r_straight = analyse_attempt(*path(u), P)["reversals"][0]
    assert (not r_curved["valid"] and r_curved["reason"] == "window_not_straight") or \
        r_curved["k0"] > r_straight["k0"]
    if r_curved["valid"]:
        assert r_curved["window_max_dev_deg"] <= P.straight_deg


def test_start_offset_shifts_window_and_bad_source_raises():
    x, y, s = path(shuttle_u())
    r0 = analyse_attempt(x, y, s, P)["reversals"][0]
    r2 = analyse_attempt(x, y, s, with_(P, start_offset=2))["reversals"][0]
    assert r2["window"][0] == r0["window"][0] + 2
    with pytest.raises(ValueError):
        analyse_attempt(x, y, s, with_(P, speed_source="bogus"))


def test_too_short():
    assert analyse_attempt(np.zeros(8), np.zeros(8), np.zeros(8))["reason"] == "too_short"
