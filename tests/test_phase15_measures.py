"""Tests for Phase 15 measures: SG gain, arc geometry, G-study helper and the synthetic arc generator."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nfl_bdb.features.phase15_measures import ArcParams, arc_measures, arc_segment, g_coef, gstudy, sg_speed_gain  # noqa: E402
from nfl_bdb.features.skill_drills import kinematics  # noqa: E402
from nfl_bdb.simulation.arc_synth import ArcTrial, sample_arc, simulate_arc  # noqa: E402


@pytest.mark.parametrize("w", [5, 7, 9])
def test_sg_gain_matches_circular_motion_and_heading_rate_is_unbiased(w):
    for om in (1.0, 2.0, 3.0):
        t = np.arange(0, 8, 0.1); R = 3.0
        k = kinematics(R * np.cos(om * t), R * np.sin(om * t), w)
        mid = slice(10, -10)
        assert np.median(k["speed"][mid]) / (R * om) == pytest.approx(sg_speed_gain(om, w), rel=1e-6)
        assert np.median(k["omega"][mid]) == pytest.approx(om, rel=1e-6)
    g = sg_speed_gain(np.array([0.5, 1.5, 3.0]), w)
    assert np.all(np.diff(g) < 0) and np.all(g < 1)
    assert sg_speed_gain(0.0, w) == 1.0


def test_gain_increases_attenuation_with_window():
    assert sg_speed_gain(2.0, 5) > sg_speed_gain(2.0, 7) > sg_speed_gain(2.0, 9)


def _sampled(tr, phase=0.04, noise="gauss", sigma=0.0):
    sm = sample_arc(simulate_arc(tr), phase, noise, sigma, np.random.default_rng(0))
    return sm


def test_generator_heading_and_consistency():
    tr = ArcTrial(v0=4.0, a_t=0.0, R=3.0, dtheta_deg=100, ramp=0.2, direction=-1)
    sim = simulate_arc(tr)
    assert abs(np.degrees(sim["omega"].sum() * 0.001)) == pytest.approx(100, abs=4)
    dx = np.gradient(sim["x"], 0.001); dy = np.gradient(sim["y"], 0.001)
    np.testing.assert_allclose(np.hypot(dx, dy)[5:-5], sim["speed"][5:-5], rtol=1e-3)
    assert np.isclose(sim["kappa"].max(), 1 / 3.0)


def test_arc_segment_side_validity_and_straight_path():
    for d, side in ((1, "left"), (-1, "right")):
        sm = _sampled(ArcTrial(v0=4.0, a_t=0.5, R=3.5, dtheta_deg=100, direction=d))
        seg = arc_segment(sm["x"], sm["y"])
        assert seg["valid"] and seg["side"] == side and 60 < seg["heading_deg"] < 120
    t = np.arange(0, 3, 0.1)
    assert arc_segment(10 + 5 * t, np.full_like(t, 3.0))["reason"] == "no_arc"
    # arc running into the end of the recording is flagged truncated
    sm = _sampled(ArcTrial(v0=4.0, R=3.0, dtheta_deg=140, lead_out=0.0))
    seg = arc_segment(sm["x"], sm["y"])
    assert seg["truncated"] and not seg["valid"]


def test_arc_measures_speed_correction_on_steady_arc():
    tr = ArcTrial(v0=4.0, a_t=0.0, R=3.0, dtheta_deg=150, ramp=0.1, direction=1)
    sm = _sampled(tr)
    u = arc_measures(sm["x"], sm["y"], ArcParams(), correct=False)
    c = arc_measures(sm["x"], sm["y"], ArcParams(), correct=True)
    assert u["speed"] < 4.0 and c["speed"] == pytest.approx(4.0, rel=0.01)
    assert u["a_n"] < 4.0 ** 2 / 3.0
    b = arc_measures(sm["x"], sm["y"], ArcParams(), band=(3.5, 4.5))
    assert b["band_frames"] >= 3 and b["band_curvature"] > 0


def test_gstudy_recovers_components_and_g_coef():
    rng = np.random.default_rng(1); rows = []
    for a in range(150):
        pa = rng.normal(0, 1.0); yr = rng.integers(0, 3)
        for r in rng.choice(12, rng.integers(6, 13), replace=False):
            pr = rng.normal(0, 0.7)
            for _ in range(2 if rng.random() < 0.25 else 1):
                rows.append(dict(nfl_id=a, route=r, cell=f"{r}_{yr}", v=0.4 * r + pa + pr + rng.normal(0, 0.5)))
    g = gstudy(pd.DataFrame(rows), "v")
    assert g["s2_athlete"] == pytest.approx(1.0, abs=0.35)
    assert g["s2_athlete_route"] == pytest.approx(0.49, abs=0.2)
    assert g["s2_residual"] == pytest.approx(0.25, abs=0.12)
    assert g_coef(1.0, 0.5, 0.25, 1) == pytest.approx(1 / 1.75)
    assert g_coef(1.0, 0.5, 0.25, 12) > g_coef(1.0, 0.5, 0.25, 6) > g_coef(1.0, 0.5, 0.25, 1)
