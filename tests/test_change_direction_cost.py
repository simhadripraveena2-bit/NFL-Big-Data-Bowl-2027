import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nfl_bdb.features.change_direction_cost import (  # noqa: E402
    AthleteLimits, drill_paths, linear_sprint_time, min_time_nlp, min_time_profile, path_from_waypoints,
    segment_time, simulate_execution)

LIM = AthleteLimits(A0=8.9, S0=11.6, D=6.5, C=7.0)


def test_straight_line_matches_closed_form():
    p = path_from_waypoints([[0, 0], [40, 0]], [])
    _, T, _ = min_time_profile(p, LIM)
    assert abs(T - linear_sprint_time(40, LIM)) / T < 1e-3


def test_forward_backward_matches_nlp_for_independent_limits():
    r = min_time_nlp(drill_paths()["cut_90"], LIM, n_nodes=50)
    assert abs(r["T_nlp"] - r["T_fb_same_grid"]) / r["T_fb_same_grid"] < 1e-4


def test_lateral_cap_on_circle():
    p = path_from_waypoints([[0, 0], [10, 0], [10, 10]], [3.0])
    v, _, _ = min_time_profile(p, LIM)
    on_arc = np.isclose(p.kappa, 1 / 3.0)
    assert np.max(v[on_arc]) <= np.sqrt(LIM.C * 3.0) + 1e-6


def test_zero_execution_cost_for_perfect_execution():
    p = drill_paths()["three_cone"]
    ex = simulate_execution(p, LIM, (1, 1, 1), 0.0, noise_sd=0.0, rng=np.random.default_rng(0))
    T_gate = ex["T_true"] - np.interp(0.5, p.s, ex["t_profile"])
    assert abs(T_gate - segment_time(p, LIM, 0.5)) < 1e-9
