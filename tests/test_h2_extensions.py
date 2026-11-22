import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nfl_bdb.models import confirmatory as cf  # noqa: E402
from nfl_bdb.models import h2_extensions as h2  # noqa: E402


def _toy(seed, beta_x, P=120, n=60):
    rng = np.random.default_rng(seed)
    F = rng.standard_normal(P); x = 0.8 * F + 0.6 * rng.standard_normal(P); ten = 0.5 * F + rng.standard_normal(P)
    lev = 0.25 * F + beta_x * x + 0.3 * rng.standard_normal(P)
    pid = np.repeat(np.arange(P), n); team = pid % 40
    W = rng.standard_normal((len(pid), 3))
    y = 3 + lev[pid] + W @ [0.2, -0.1, 0.0] + rng.normal(0, 1.5, len(pid))
    return pid, team, y, W, F, x, ten, rng


def test_true_scale_matches_frozen_partial():
    pid, team, y, W, F, x, ten, rng = _toy(1, 0.2)
    r = h2.fit(pid, team, y, W, F, x)
    assert abs(r["partial"] - cf.h2_reml(pid, team, y, W, F, x)["partial"]) < 1e-12
    assert 0 <= r["dR2_true"] <= r["R2_true_full"] <= 1


def test_cv_extended_detects_increment_only_when_present():
    for bx, sign in ((0.35, 1), (0.0, -1)):
        pid, team, y, W, F, x, ten, rng = _toy(2, bx)
        S = cf.player_sufficient(pid, W, y, len(F))
        s = h2.cv_extended(S, F, x, ten, pid[:: 60] % 3, np.quantile(x, [0, 1 / 3, 2 / 3, 1]), rng, repeats=3)
        assert (s["dR2_CV"] > 0.05) if sign > 0 else (s["dR2_CV"] < 0.01)


def test_eiv_tipping_point_and_bootstrap_shapes():
    pid, team, y, W, F, x, ten, rng = _toy(3, 0.05)
    r = cf.residualise_np(W, y); m, n, sw2 = cf.player_stats(pid, r, len(F))
    grid = h2.eiv_grid(m, n, sw2, F, x)
    assert len(grid) == 8
    tp = h2.tipping_point(m, n, sw2, F, x, 0.987)
    assert tp is None or 0.5 < tp < 1
    arr = dict(pid=pid, team=team, y=y, W=W)
    bs = h2.reml_bootstrap(arr, arr, F, x, 3, 7)
    assert bs["deep_beta_P"].shape == (3,) and np.isfinite(bs["deep_beta_P"]).all()


def test_precision_artefact_zero_when_forty_perfect():
    assert abs(h2.precision_artefact(0.8, 1.0, 1.0, 0.5)) < 1e-6
    assert h2.precision_artefact(0.814, 0.90, 0.987, 0.6) > 0.05


def test_tipping_point_never_returns_the_eiv_singularity():
    rng = np.random.default_rng(9); P = 60
    F = rng.standard_normal(P); x = 0.85 * F + np.sqrt(1 - 0.85 ** 2) * rng.standard_normal(P)
    m = 0.05 * F - 0.02 * x + 0.1 * rng.standard_normal(P); n = np.full(P, 100.0)
    bound = h2.admissible_rel_F(F, x, 0.987)
    tp = h2.tipping_point(m, n, 1.0, F, x, 0.987)
    assert tp is None or tp > bound + 1e-4
