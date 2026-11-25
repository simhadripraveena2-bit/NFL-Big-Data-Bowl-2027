"""Tests for the Phase 17 outcome-study power simulator (simulation only; no data)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nfl_bdb.simulation.outcome_power import _batched_ols_hc3, _solve_s2b, mde, simulate_cell  # noqa: E402

RNG = np.random.default_rng(5)
COUNTS = RNG.integers(120, 1300, 54).astype(float)
TEAMS = RNG.integers(1, 5, 54).astype(float)


def test_solve_s2b_hits_target_reliability():
    for R_y, tau in ((0.44, 1.1), (0.61, 1.1), (0.61, 0.0)):
        s2b = _solve_s2b(R_y, COUNTS, TEAMS, tau, 1.85 ** 2)
        rel = np.mean(s2b / (s2b + tau * s2b / TEAMS + 1.85 ** 2 / COUNTS))
        assert rel == pytest.approx(R_y, abs=1e-4)
    # with team noise the mean reliability is bounded by mean(1 / (1 + tau / k)); above that it is infeasible
    assert np.isnan(_solve_s2b(0.99, COUNTS, TEAMS, 1.1, 1.85 ** 2))


def test_hc3_matches_direct_formula():
    rng = np.random.default_rng(1)
    n = 40
    X = np.column_stack([np.ones(n), rng.normal(size=(n, 2))])
    y = X @ np.array([0.5, 1.0, -0.3]) + rng.normal(size=n) * (1 + np.abs(X[:, 1]))
    b, se = _batched_ols_hc3(X[None], y[None])
    XtXi = np.linalg.inv(X.T @ X)
    bd = XtXi @ X.T @ y
    e = y - X @ bd
    h = np.diag(X @ XtXi @ X.T)
    V = XtXi @ (X.T * (e / (1 - h)) ** 2) @ X @ XtXi
    np.testing.assert_allclose(b[0], bd, rtol=1e-10)
    np.testing.assert_allclose(se[0], np.sqrt(np.diag(V)), rtol=1e-10)


def _cell(rho, **kw):
    base = dict(N=92, n_elig=54, counts=COUNTS, team_counts=TEAMS, R_y=0.61, R_x=0.64, reps=1500,
                rng=np.random.default_rng(11))
    base.update(kw)
    return simulate_cell(rho, **base)


def test_size_near_nominal_and_power_increases():
    r0 = _cell(0.0)
    assert r0["feasible"] and 0.025 <= r0["power_two_sided"] <= 0.075
    p = [_cell(rho)["power_two_sided"] for rho in (0.0, 0.3, 0.6)]
    assert p[0] < p[1] < p[2]


def test_disattenuated_estimate_recovers_truth():
    r = _cell(0.5, reps=3000)
    assert r["mean_r_hat"] < 0.5 * 0.75                         # attenuated by sqrt(R_x R_y) ~ 0.62
    assert r["mean_r_disattenuated"] == pytest.approx(0.5, abs=0.06)
    assert 0.92 <= r["coverage_disattenuated"] <= 0.97


def test_actual_rx_uses_g_coefficient():
    r = _cell(0.2, R_x="actual", n_routes=np.array([8, 12]), g_components=(0.182, 0.316, 0.510), reps=200)
    g8, g12 = (0.182 / (0.182 + 0.826 / k) for k in (8, 12))
    assert g8 < r["rx_mean"] < g12


def test_infeasible_cell_flagged():
    assert _cell(0.2, R_y=0.99)["feasible"] is False


def test_mde_interpolation():
    assert mde([0, 0.1, 0.2], [0.05, 0.6, 1.0]) == pytest.approx(0.15)
    assert np.isnan(mde([0, 0.1], [0.05, 0.5]))
