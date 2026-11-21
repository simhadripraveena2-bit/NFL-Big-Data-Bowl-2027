import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nfl_bdb.models import power as pw  # noqa: E402

VC = dict(contexts=["h", "l"], n_players=300, counts=[[150, 150]] * 50, sd_within=[1.0, 1.0],
          var_between=[0.06, 0.06], corr_between_true=0.6)


def test_solve_ru_reproduces_true_correlation():
    rh, rl, c = 0.5, 0.2, 0.6
    ru = pw._solve_ru(c, rh, rl)
    assert abs(rh * rl + ru * np.sqrt((1 - rh**2) * (1 - rl**2)) - c) < 1e-9


def test_h1_estimator_unbiased_and_powered_at_large_n():
    rng = np.random.default_rng(0)
    r = pw.power_h1(VC, rho_high=0.5, rho_low=0.2, n_sims=60, n_boot=150, rng=rng, alphas=(0.05,))
    assert abs(r["mean_delta_hat"] - 0.3 * np.sqrt(0.987)) < 0.03
    assert r["power_a0.0500"] > 0.9


def test_h1_null_size_reasonable():
    rng = np.random.default_rng(1)
    r = pw.power_h1(VC, rho_high=0.3, rho_low=0.3, n_sims=200, n_boot=150, rng=rng, alphas=(0.05,))
    assert r["power_a0.0500"] < 0.08


def test_h2_null_and_signal():
    vc = dict(counts=[[140, 140]] * 50, var_between=[0.05, 0.05], sd_within=[1.0, 1.0], n_players=400)
    rng = np.random.default_rng(2)
    null = pw.power_h2(vc, 0.8, 1.0, 1.0, 0.3, 0.0, 300, rng, alphas=(0.05,))
    sig = pw.power_h2(vc, 0.8, 1.0, 1.0, 0.3, 0.4, 200, rng, alphas=(0.05,))
    assert null["power_a0.0500"] < 0.06 and sig["power_a0.0500"] > 0.8


def test_mde_interpolation():
    assert abs(pw.mde([0, 0.1, 0.2], [0.05, 0.5, 0.9]) - 0.175) < 1e-9
    assert np.isnan(pw.mde([0, 0.1], [0.05, 0.3]))
