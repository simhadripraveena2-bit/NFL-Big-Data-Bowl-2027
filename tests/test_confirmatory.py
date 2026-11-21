import sys
import warnings
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nfl_bdb.features import demand as dm  # noqa: E402
from nfl_bdb.models import confirmatory as cf  # noqa: E402
from nfl_bdb.models.reml import fit_reml  # noqa: E402


def _toy_h1(seed, rho_h, rho_l, P=150, T=60):
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(P)
    Sb = np.array([[0.06, 0.04], [0.04, 0.08]])
    c_true = Sb[0, 1] / np.sqrt(Sb[0, 0] * Sb[1, 1])
    ru = (c_true - rho_h * rho_l) / np.sqrt((1 - rho_h ** 2) * (1 - rho_l ** 2))
    u1 = rng.standard_normal(P); u2 = ru * u1 + np.sqrt(1 - ru ** 2) * rng.standard_normal(P)
    lev = np.column_stack([np.sqrt(Sb[0, 0]) * (rho_h * z + np.sqrt(1 - rho_h ** 2) * u1),
                           np.sqrt(Sb[1, 1]) * (rho_l * z + np.sqrt(1 - rho_l ** 2) * u2)])
    tau = rng.normal(0, 0.1, T); teams = [rng.choice(T, rng.integers(1, 4), replace=False) for _ in range(P)]
    pl_, c_, t_, y_ = [], [], [], []
    for i in range(P):
        for c in (0, 1):
            n = int(rng.integers(60, 200)); t = rng.choice(teams[i], n)
            y = 6 + c + lev[i, c] + tau[t] + rng.normal(0, [0.9, 1.2][c], n)
            pl_ += [i] * n; c_ += [c] * n; t_ += list(t); y_ += list(y)
    player, ctx, team, y = map(np.array, (pl_, c_, t_, y_))
    Xw = np.column_stack([(ctx == 0), (ctx == 1)]).astype(float)
    return player, ctx, team, y, Xw, z, rng


def test_reml_matches_statsmodels_random_intercept():
    import statsmodels.api as sm
    warnings.filterwarnings("ignore")
    rng = np.random.default_rng(1)
    P = 40; g = np.repeat(np.arange(P), rng.integers(20, 80, P)); n = len(g)
    x = rng.normal(size=n); y = 1 + 0.4 * x + rng.normal(0, 0.5, P)[g] + rng.normal(0, 1, n)
    X = np.column_stack([np.ones(n), x])
    f = fit_reml(y, X, g, np.zeros(n, int), None, 1)
    m = sm.MixedLM(y, X, groups=g).fit(reml=True)
    assert np.allclose(f.beta, m.fe_params, atol=1e-4)
    assert abs(f.sigma_b[0, 0] - np.asarray(m.cov_re)[0, 0]) < 1e-3
    assert abs(f.s2_resid[0] - m.scale) < 1e-3


def test_reml_recovers_crossed_variance_components():
    player, ctx, team, y, Xw, z, rng = _toy_h1(2, 0.0, 0.0, P=200)
    f = fit_reml(y, Xw, player, ctx, team, 2)
    assert f.converged
    assert abs(f.sigma_b[0, 0] - 0.06) < 0.02 and abs(f.sigma_b[1, 1] - 0.08) < 0.025
    assert abs(f.s2_team - 0.01) < 0.008
    assert np.allclose(f.s2_resid, [0.81, 1.44], rtol=0.05)


def test_h1_reml_recovers_delta():
    est = []
    for s in range(6):
        player, ctx, team, y, Xw, z, rng = _toy_h1(10 + s, 0.6, 0.2, P=150)
        est.append(cf.h1_reml(player, ctx, team, y, Xw, z).delta)
    assert abs(np.mean(est) - 0.4) < 0.08


def test_moment_rho_disattenuates():
    rng = np.random.default_rng(3)
    P, n = 4000, 30
    z = rng.standard_normal(P); lev = 0.2 * (0.5 * z + np.sqrt(0.75) * rng.standard_normal(P))
    m = (lev + rng.standard_normal(P) / np.sqrt(n))[:, None]
    rho, raw = cf.moment_rho(z, m, np.full((P, 1), n, float), np.array([1.0]))
    assert abs(rho[0] - 0.5) < 0.05 and raw[0] < 0.4


def test_h1_procedure_null_and_effect_decisions():
    p1, c1, t1, y1, X1, z1, r1 = _toy_h1(20, 0.7, 0.1, P=150)
    res = cf.h1_procedure(p1, c1, t1, y1, X1, np.zeros((len(y1), 0)), z1, 500, r1)
    assert res["supported"]
    p0, c0, t0, y0, X0, z0, r0 = _toy_h1(21, 0.3, 0.3, P=150)
    res0 = cf.h1_procedure(p0, c0, t0, y0, X0, np.zeros((len(y0), 0)), z0, 500, r0)
    assert res0["ci_lo"] < 0.0 + 1e-9 or not res0["supported"]


def test_fixed_sequence_gatekeeping():
    sig, ns = dict(p=0.01, direction_ok=True), dict(p=0.30, direction_ok=True)
    wrong = dict(p=0.001, direction_ok=False)
    assert cf.fixed_sequence([sig, sig]) == [True, True]
    assert cf.fixed_sequence([ns, sig]) == [False, False]      # H2 never tested if H1-WR fails
    assert cf.fixed_sequence([sig, ns]) == [True, False]
    assert cf.fixed_sequence([wrong, sig]) == [False, False]   # wrong direction is not support


def test_holm_step_down():
    r = [dict(p=0.012, direction_ok=True), dict(p=0.04, direction_ok=True), dict(p=0.02, direction_ok=True)]
    assert cf.holm(r) == [True, True, True]       # 0.012<0.0167, 0.02<0.025, 0.04<0.05
    r[0]["p"] = 0.02
    assert cf.holm(r) == [False, False, False]    # 0.02 > 0.0167 stops the procedure
    r = [dict(p=0.001, direction_ok=True), dict(p=0.03, direction_ok=True), dict(p=0.2, direction_ok=True)]
    assert cf.holm(r) == [True, False, False]


def test_cv_holds_out_players_not_plays():
    rng = np.random.default_rng(5)
    P = 57
    for _ in range(5):
        fid = cf.player_folds(P, 10, rng)
        assert len(fid) == P and set(fid) == set(range(10))
        # every player belongs to exactly one fold, so the play-level train/test sets never share a player
        player = np.repeat(np.arange(P), 30)
        for f in range(10):
            tr = set(player[fid[player] != f]); te = set(player[fid[player] == f])
            assert tr.isdisjoint(te)


def test_h2_cv_detects_strong_increment_and_not_null():
    rng = np.random.default_rng(6)
    P = 300
    F = rng.standard_normal(P); x = 0.5 * F + np.sqrt(0.75) * rng.standard_normal(P)
    player = np.repeat(np.arange(P), 50); W = rng.standard_normal((len(player), 2))
    for beta_x, sign in ((0.3, 1), (0.0, -1)):
        lev = 0.2 * F + beta_x * x
        y = lev[player] + W @ [0.1, -0.1] + rng.normal(0, 1, len(player))
        S = cf.player_sufficient(player, W, y, P)
        dr2 = cf.h2_cv(S, F, x, rng, 10, 3)["dr2"]
        assert (dr2 > 0.05) if sign > 0 else (dr2 < 0.01)


def test_demand_shares_and_crossfit():
    plays = pl.DataFrame({"nfl_id": [1] * 10 + [2] * 10, "ctx": (["a"] * 5 + ["b"] * 5) * 2,
                          "vmax_play": [10, 10, 10, 10, 10, 1, 1, 1, 1, 1] + [5] * 10})
    sh = dm.player_shares(plays, absolute=None).sort("nfl_id", "ctx")
    assert sh.filter((pl.col("nfl_id") == 1) & (pl.col("ctx") == "a"))["share_90"][0] == 1.0
    assert sh.filter((pl.col("nfl_id") == 1) & (pl.col("ctx") == "b"))["share_90"][0] == 0.0
    a1, b1 = dm.crossfit_halves(np.arange(57)); a2, b2 = dm.crossfit_halves(np.arange(57))
    assert np.array_equal(a1, a2) and len(np.intersect1d(a1, b1)) == 0 and len(a1) + len(b1) == 57


def test_meta_regression_recovers_slope():
    D = np.array([0.17, 0.01, 0.19, 0.03, 0.07, 0.03, 0.02, 0.03, 0.01, 0.01, 0.01])
    pos = ["WR", "WR", "TE", "TE", "DB", "DB", "DB", "DL", "DL", "OL", "OL"]
    rho = 0.2 + 2.0 * D
    lam, se, om = dm.meta_regression_reml(rho, np.full(11, 0.01), D, pos)
    assert abs(lam - 2.0) < 1e-3


def test_h1_registered_test_uses_full_reml_bootstrap():
    import pytest
    player, ctx, team, y, Xw, z, rng = _toy_h1(30, 0.7, 0.1, P=60)
    with pytest.raises(ValueError):
        cf.h1_registered_test(player, ctx, team, y, Xw, z, seed=1, B=100)   # below the registered B
    # same engine as the registered bootstrap: identical draws for the same seed
    cf_b = cf.H1_B_REGISTERED
    assert cf_b == 2000
    reml = cf.h1_reml(player, ctx, team, y, Xw, z)
    bt = cf.h1_reml_bootstrap(player, ctx, team, y, Xw, z, 5, np.random.default_rng(7), start=reml.extra["theta"])
    bt2 = cf.h1_reml_bootstrap(player, ctx, team, y, Xw, z, 5, np.random.default_rng(7), start=reml.extra["theta"])
    assert np.allclose(bt["boot"], bt2["boot"])
