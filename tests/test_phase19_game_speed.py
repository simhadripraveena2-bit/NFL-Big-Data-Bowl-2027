"""Tests for the Phase 19 synthetic power study (no data; synthetic design)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nfl_bdb.models import confirmatory as cf  # noqa: E402  (frozen; called, never modified)
from nfl_bdb.simulation import game_speed_incremental as gs  # noqa: E402


def _design(P=57, T=40, seed=0):
    rng = np.random.default_rng(seed)
    n = rng.integers(40, 500, (P, 2)).astype(float)
    W = np.zeros((2, P, T))
    for i in range(P):
        ts = rng.choice(T, rng.integers(1, 4), replace=False)
        for c in range(2):
            w = rng.random(len(ts)); W[c, i, ts] = w / w.sum()
    R_P = np.where(rng.random(P) < 0.18, 0.89, 0.94)
    return gs.Design(n=n, W=W, R_P=R_P)


def test_wls_hc3_matches_frozen_two_stage():
    rng = np.random.default_rng(1)
    P = 57
    m = rng.normal(size=P); v = rng.uniform(0.002, 0.02, P); F = rng.normal(size=P); x = 0.8 * F + rng.normal(size=P) * 0.5
    b_f, se_f, s2b = cf.wls_two_stage(m, 1 / v, 1.0, F, x)
    X = np.column_stack([np.ones(P), cf.standardise(F), cf.standardise(x)])
    b, se = gs._wls_hc3(X[None], m[None], (1 / (s2b + v))[None])
    np.testing.assert_allclose(b[0], b_f, rtol=1e-10)
    np.testing.assert_allclose(se[0], se_f, rtol=1e-10)


def test_eiv_matches_frozen():
    rng = np.random.default_rng(2)
    P = 57
    m = rng.normal(size=P); F = rng.normal(size=P); x = 0.8 * F + 0.5 * rng.normal(size=P)
    e_f = cf.eiv_two_stage(m, np.ones(P), 1.0, F, x, 0.9, 0.94)
    Wz = np.column_stack([cf.standardise(F), cf.standardise(x)])
    S = np.cov(Wz.T); S[0, 0] -= 0.1 * S[0, 0]; S[1, 1] -= 0.06 * S[1, 1]
    c = np.array([np.cov(Wz[:, k], m)[0, 1] for k in range(2)])
    np.testing.assert_allclose(np.linalg.solve(S, c), e_f, rtol=1e-10)


def test_population_targets_single_construct():
    b_obs, b_true, rho = gs.population_targets(0.5, 0.0, 0.99, 0.94, 0.851)
    assert abs(b_true[1]) < 1e-12 and abs(b_obs[1]) < 0.02          # nearly no artefact when the 40 is reliable
    b_obs2, _, rho2 = gs.population_targets(0.5, 0.0, 0.78, 0.931, 0.851)
    assert rho2 > 0.99 and b_obs2[1] > 0.05                          # precision artefact when R_F is at its bound


def test_simulated_sigma_b_and_correlation():
    d = _design()
    r = gs.simulate_cell(d, a=0.5, pi=0.3, R_F=0.9, reps=1500, rng=np.random.default_rng(3), do_cv=False)
    assert r["coverage_obs"] > 0.92 and abs(r["bias_beta_P"]) < 0.01
    r0 = gs.simulate_cell(d, a=0.5, pi=0.0, R_F=0.99, reps=1500, rng=np.random.default_rng(4), do_cv=False)
    assert 0.025 <= r0["power"] <= 0.08
    assert r["power"] > r0["power"]


def test_cv_returns_sane_r2():
    d = _design(seed=5)
    r = gs.simulate_cell(d, a=0.7, pi=0.0, R_F=0.99, reps=200, rng=np.random.default_rng(6), cv_repeats=2)
    assert 0.2 < r["r2_m1"] < 0.6 and r["dr2_m3_m1"] < 0.01


def test_composite_reliability_bounds():
    d = _design()
    with_team, sampling = gs.composite_reliability(d)
    assert 0 < with_team < sampling < 1


def test_mde():
    assert gs.mde([0, 0.1, 0.2], [0.05, 0.6, 1.0]) == pytest.approx(0.15)
    assert np.isnan(gs.mde([0, 0.1], [0.05, 0.5]))
