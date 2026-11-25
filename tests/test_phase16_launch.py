"""Tests for the Phase 16 frozen launch definition, the straight-start generator and the covariate G-study."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nfl_bdb.features.launch import gstudy_cov, launch  # noqa: E402
from nfl_bdb.features.phase15_measures import gstudy  # noqa: E402
from nfl_bdb.simulation.start_synth import StartTrial, sample_start, simulate_start  # noqa: E402


def test_generator_truth_and_consistency():
    tr = StartTrial(A0=8.0, kappa=0.9, ramp=0.2, step_amp=0.0, sway=0.0)
    sim = simulate_start(tr)
    t = sim["t"]
    assert np.all(sim["speed"][t < tr.t0] < 1e-9)
    tt = sim["truth"]
    assert tr.t0 < tt["t_onset"] < tr.t0 + 0.5
    np.testing.assert_allclose(np.hypot(np.gradient(sim["x"], 0.001), np.gradient(sim["y"], 0.001))[5:-5], sim["speed"][5:-5], atol=5e-3)   # cumulative-sum integration: half-step offset (a*dt/2)
    assert 0 < tt["launch_p95_trend"] <= 0.9 * 8.0 + 1e-9
    # without step oscillation the instantaneous and trend truths agree
    assert tt["launch_p95_inst"] == pytest.approx(tt["launch_p95_trend"], rel=0.02)


def test_launch_recovers_onset_and_ranks_acceleration():
    est, truth = [], []
    for A0 in (6.0, 7.0, 8.0, 9.0):
        sim = simulate_start(StartTrial(A0=A0, kappa=0.9, step_amp=0.0, sway=0.0, rec_offset=0.3))
        sm = sample_start(sim, 0.04, "gauss", 0.0, np.random.default_rng(0))
        L = launch(sm["x"], sm["y"])
        assert L["valid"]
        assert abs(sm["ts"][0] + L["onset_time"] - sim["truth"]["t_onset"]) <= 0.1
        est.append(L["p95"]); truth.append(sim["truth"]["launch_p95_trend"])
    assert np.all(np.diff(est) > 0)
    assert np.all(np.array(est) < np.array(truth))          # smoothing biases the 95th percentile downwards


def test_launch_rejections():
    t = np.arange(0, 3, 0.1)
    assert launch(5 + 3 * t, np.zeros_like(t))["reason"] == "moving_at_first_frame"
    assert launch(np.zeros(30), np.zeros(30))["reason"] == "no_onset"
    sim = simulate_start(StartTrial(rec_offset=0.3, rec_len=1.0, step_amp=0.0))
    sm = sample_start(sim, 0.0, "gauss", 0.0, np.random.default_rng(0))
    assert launch(sm["x"], sm["y"])["reason"] in ("window_incomplete", "too_short")
    late = simulate_start(StartTrial(rec_offset=-0.4, step_amp=0.0))
    s2 = sample_start(late, 0.0, "gauss", 0.0, np.random.default_rng(0))
    assert launch(s2["x"], s2["y"])["reason"] == "moving_at_first_frame"


def test_gstudy_cov_absorbs_athlete_variance():
    rng = np.random.default_rng(3); rows = []
    for a in range(120):
        z = rng.normal(); pa = 0.9 * z + rng.normal(0, 0.45)
        for r in rng.choice(10, 8, replace=False):
            for _ in range(2 if rng.random() < 0.2 else 1):
                rows.append(dict(nfl_id=a, route=r, cell=f"{r}", y=pa + rng.normal(0, 0.6) + rng.normal(0, 0.4), z=z))
    d = pd.DataFrame(rows)
    g0 = gstudy(d, "y"); g1 = gstudy_cov(d, "y", ["z"])
    share = 1 - g1["s2_athlete"] / g0["s2_athlete"]
    assert 0.55 < share < 0.95 and g1["coefs"]["z"] == pytest.approx(0.9, abs=0.2)
