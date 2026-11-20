import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nfl_bdb.models.capacity_estimator import V_MIN, eb_shrink, fit_binned  # noqa: E402
from nfl_bdb.simulation.movement import GameSimConfig, simulate_game_tracks  # noqa: E402


def test_binned_recovers_exact_frontier():
    v = np.linspace(V_MIN, 11.0, 400)
    a = 8.0 * (1 - v / 11.5)
    r = fit_binned(v, a, np.zeros_like(v, int))
    assert abs(r["A0"] - 8.0) < 0.05 and abs(r["S0"] - 11.5) < 0.05


def test_generator_never_exceeds_frontier():
    rng = np.random.default_rng(0)
    out = simulate_game_tracks([8.5], [11.0], [6.0], [0.3], [50], GameSimConfig(noise_sd=0.0, round_to=0.0), rng)
    fr = 8.5 * (1 - out["v_true"] / 11.0)
    assert np.all(out["a_true"] <= fr + 1e-9)


def test_eb_shrink_pulls_uninformative_to_group_mean():
    est = np.array([[1.0], [1.2], [0.8], [5.0]])
    se = np.array([[0.05], [0.05], [0.05], [1e3]])
    pm, psd = eb_shrink(est, se, np.array(["g"] * 4))
    assert abs(pm[3, 0] - np.mean([1.0, 1.2, 0.8])) < 0.2
    assert psd[3, 0] > psd[0, 0]
