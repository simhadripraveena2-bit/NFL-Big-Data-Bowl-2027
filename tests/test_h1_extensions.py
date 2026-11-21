import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nfl_bdb.models import confirmatory as cf  # noqa: E402
from nfl_bdb.models import h1_extensions as hx  # noqa: E402
from nfl_bdb.models.reml import fit_reml  # noqa: E402
from test_confirmatory import _toy_h1  # noqa: E402


def test_reml_criterion_reproduces_fit():
    player, ctx, team, y, Xw, z, rng = _toy_h1(40, 0.6, 0.2, P=50)
    xp = (z - z.mean()) / z.std(ddof=1)
    X = np.column_stack([Xw] + [xp[player] * (ctx == c) for c in (0, 1)])
    fit = fit_reml(y, X, player, ctx, team, 2)
    f = hx.reml_criterion(y, X, player, ctx, team, 2)
    assert abs(f(fit.theta) - fit.neg2ll) < 1e-6
    w = hx.wald_delta(player, ctx, team, y, Xw, z)
    assert abs(w["delta"] - cf.h1_reml(player, ctx, team, y, Xw, z).delta) < 1e-6
    assert w["hessian_min_eig"] > 0 and 0.02 < w["se"] < 0.5


def test_natural_spline_basis_linear_beyond_boundary_and_derivative():
    kn = np.array([-2.0, -0.5, 0.5, 2.0]); x = np.linspace(-3, 3, 601)
    B = hx.ns_basis(x, kn); D = hx.ns_basis(x, kn, deriv=True)
    num = np.gradient(B, x, axis=0)
    assert np.allclose(num[5:-5], D[5:-5], atol=1e-2)
    out = x > 2.05
    assert np.allclose(np.diff(D[out], axis=0), 0, atol=1e-8)       # linear beyond the boundary knot


def test_spline_recovers_linear_slopes():
    player, ctx, team, y, Xw, z, rng = _toy_h1(41, 0.7, 0.1, P=150)
    r = hx.spline_fit(player, ctx, team, y, Xw, z, np.quantile(z, [0, 1 / 3, 2 / 3, 1]))
    lin = cf.h1_reml(player, ctx, team, y, Xw, z)
    assert np.allclose(r["avg_deriv"], lin.beta, atol=0.03)


def test_permutation_control_centres_near_zero():
    player, ctx, team, y, Xw, z, rng = _toy_h1(42, 0.7, 0.1, P=80)
    import polars as pl
    df = pl.DataFrame(dict(pid=player, ctx_i=ctx, game_id=np.arange(len(y)), play_id=np.zeros(len(y), int), team_i=team, y=y))
    ds = []
    for s in range(8):
        p = hx.permute_within_player(df, np.random.default_rng(s))
        X = np.column_stack([(p["ctx_i"] == 0).to_numpy(), (p["ctx_i"] == 1).to_numpy()]).astype(float)
        ds.append(cf.h1_reml(p["pid"].to_numpy(), p["ctx_i"].to_numpy(), p["team_i"].to_numpy(), p["y"].to_numpy(), X, z).delta)
    assert abs(np.mean(ds)) < 0.08
