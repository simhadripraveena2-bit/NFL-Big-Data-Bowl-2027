"""Tests for the Phase 13 synthetic generator and candidate post-turn acceleration estimators."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nfl_bdb.features.exit_accel_candidates import e1_e2, e3, params_for_fs  # noqa: E402
from nfl_bdb.features.shuttle_accel import ShuttleParams, analyse_attempt  # noqa: E402
from nfl_bdb.simulation.shuttle_synth import Athlete, TrialParams, draw_trial, sample, simulate  # noqa: E402

ATH = Athlete(A0=9.5, V=9.0)


def test_generator_is_physically_consistent():
    sim = simulate(ATH, TrialParams(sway_amp=0.1, step_amp=0.3, delta_deg=6, rot_deg=33))
    dt = 0.001
    np.testing.assert_allclose(np.gradient(sim["x"], dt)[5:-5], sim["vx"][5:-5], atol=2e-3)
    np.testing.assert_allclose(np.gradient(sim["y"], dt)[5:-5], sim["vy"][5:-5], atol=2e-3)
    tr = sim["truth"]
    assert tr["t_min"] < tr["t_exit"] < tr["t_min"] + 0.6
    t = sim["t"]
    assert np.interp(tr["t_exit"], t, sim["speed"]) >= 1.0 - 1e-6
    # theta = mean tangential acceleration over the interval = speed change / duration
    sel = (t >= tr["t_exit"]) & (t <= tr["t_exit"] + 0.5)
    assert sim["a_t"][sel].mean() == pytest.approx(tr["theta_05"], abs=0.05)
    sel = (t >= tr["t_exit"] + 0.2) & (t <= tr["t_exit"] + 0.7)
    assert sim["a_t"][sel].mean() == pytest.approx(tr["theta_27"], abs=0.05)


def test_outgoing_acceleration_follows_force_velocity_profile():
    tp = TrialParams(sway_amp=0, step_amp=0, W=0.05, delta_deg=0)
    sim = simulate(ATH, tp); tr = sim["truth"]; t = sim["t"]
    i = int((tr["t_turn_end"] + 0.3) / 0.001)
    v = sim["speed"][i]
    assert sim["a_t"][i] == pytest.approx(ATH.A0 * (1 - v / ATH.V), rel=0.02)
    faster = simulate(Athlete(A0=11.0, V=9.0), tp)["truth"]["theta_05"]
    assert faster > tr["theta_05"]


def test_sampling_phase_noise_and_quantisation():
    sim = simulate(ATH, TrialParams())
    rng = np.random.default_rng(0)
    sm = sample(sim, 10.0, 0.037, "gauss", 0.0, rng)
    assert sm["ts"][0] == pytest.approx(0.037) and np.allclose(np.diff(sm["ts"]), 0.1)
    q = sample(sim, 10.0, 0.037, "quant30", 0.0, rng)
    assert np.allclose(q["x"] * 30, np.round(q["x"] * 30))
    assert np.abs(q["x"] - sm["x"]).max() <= 1 / 60 + 1e-9
    with pytest.raises(ValueError):
        sample(sim, 10.0, 0.0, "bogus", 0.0, rng)


def test_e1_reproduces_phase12_exactly():
    rng = np.random.default_rng(1)
    for _ in range(5):
        sim = simulate(ATH, draw_trial(rng, 0.15, 0.4))
        sm = sample(sim, 10.0, rng.uniform(0, 0.1), "quant30", 0.002, rng)
        ref = analyse_attempt(sm["x"], sm["y"], sm["s"], ShuttleParams())["reversals"][0]
        out = e1_e2(sm["x"], sm["y"], sm["s"], 10.0)
        assert out["valid"] == ref["valid"]
        if ref["valid"]:
            assert out["e1"] == pytest.approx(ref["accel"], abs=1e-12)
            assert out["e1_lo"] < out["e1"] < out["e1_hi"]
    assert params_for_fs(10.0) == ShuttleParams()


def test_e2_subframe_exit_lies_between_frames_and_is_closer_to_truth():
    rng = np.random.default_rng(2)
    e1_err, e2_err = [], []
    for _ in range(30):
        sim = simulate(ATH, draw_trial(rng, 0.0, 0.0))
        sm = sample(sim, 10.0, rng.uniform(0, 0.1), "gauss", 0.0, rng)
        out = e1_e2(sm["x"], sm["y"], sm["s"], 10.0)
        if not out["valid"]:
            continue
        assert out["e1_exit"] - 0.1 - 1e-9 <= out["e2_exit"] <= out["e1_exit"] + 1e-9
        t_exit = sim["truth"]["t_exit"]
        e1_err.append(abs(out["e1_exit"] + sm["t0"] - t_exit)); e2_err.append(abs(out["e2_exit"] + sm["t0"] - t_exit))
    assert len(e1_err) >= 25 and np.mean(e2_err) < np.mean(e1_err)


def test_e3_recovers_theta27_on_clean_data_and_bootstrap_interval():
    rng = np.random.default_rng(3)
    errs = []
    for i in range(10):
        sim = simulate(ATH, draw_trial(rng, 0.0, 0.0))
        sm = sample(sim, 10.0, rng.uniform(0, 0.1), "gauss", 0.0, rng)
        q = e3(sm["x"], sm["y"], sm["s"], 10.0, lam=1e-4, B=(30 if i == 0 else 0), rng=np.random.default_rng(4))
        assert q["e3_valid"]
        errs.append(q["e3"] - sim["truth"]["theta_27"])
        if i == 0:
            assert q["e3_lo"] <= q["e3"] <= q["e3_hi"]
    assert np.abs(errs).max() < 0.25


def test_e3_failure_when_fit_span_leaves_recording():
    sim = simulate(ATH, TrialParams(tail=0.9))
    sm = sample(sim, 10.0, 0.05, "gauss", 0.0, np.random.default_rng(5))
    q = e3(sm["x"], sm["y"], sm["s"], 10.0)
    assert not q["e3_valid"] and np.isnan(q["e3"])


def test_higher_fs_parameters_scale_with_time():
    p = params_for_fs(50.0)
    assert p.window == 35 and p.approach_frames == 25 and p.min_leg_frames == 15 and p.fs == 50.0
