import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nfl_bdb.features import demand as dm  # noqa: E402
from nfl_bdb.models import confirmatory as cf  # noqa: E402
from nfl_bdb.models import secondary as sc  # noqa: E402
from test_confirmatory import _toy_h1  # noqa: E402


def test_rho_wald_matches_h1_reml_and_has_positive_se():
    player, ctx, team, y, Xw, z, rng = _toy_h1(50, 0.6, 0.2, P=60)
    w = sc.rho_wald(player, ctx, team, y, Xw, z, 2)
    r = cf.h1_reml(player, ctx, team, y, Xw, z)
    assert np.allclose(w["rho"], r.rho, atol=1e-6) and (w["se"] > 0).all() and w["criterion_check"] < 1e-6


def test_meta_reml_full_matches_frozen_lambda():
    D = np.array([0.17, 0.01, 0.19, 0.03, 0.07, 0.03, 0.02, 0.03, 0.01, 0.01, 0.01])
    pos = ["WR", "WR", "TE", "TE", "DB", "DB", "DB", "DL", "DL", "OL", "OL"]
    rng = np.random.default_rng(1); rho = 0.3 + 1.5 * D + rng.normal(0, 0.05, 11); se = np.full(11, 0.08)
    lam, lse, om = dm.meta_regression_reml(rho, se, D, pos)
    full = sc.meta_reml_full(rho, se, D, pos)
    assert abs(full["lam"] - lam) < 1e-8 and abs(full["lam_se"] - lse) < 1e-8 and abs(full["omega2"] - om) < 1e-10


def test_holm_adjusted_monotone_and_consistent_with_frozen_holm():
    p = [0.012, 0.04, 0.02, 0.30]
    adj = sc.holm_adjusted(p)
    assert np.allclose(sorted(adj), [0.048, 0.06, 0.08, 0.30])
    dec = cf.holm([dict(p=v, direction_ok=True) for v in p])
    assert dec == [a < 0.05 for a in adj]


def test_dlb_bootstrap_runs_and_adjustment_absorbs_confounder():
    player, ctx, team, y, Xw, z, rng = _toy_h1(51, 0.6, 0.6, P=60)
    role = (z + rng.normal(0, 0.3, 60) > 0).astype(float)
    Xa = np.column_stack([Xw, sc.player_ctx_columns(role, player, ctx, 2)])
    out = sc.dlb_bootstrap(player, ctx, team, y, Xw, Xa, z, 3, 2)
    assert out.shape == (3, 6) and np.isfinite(out).all()
