import sys
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
import phase4_stages as ps  # noqa: E402


def _fake_warp(seed=0, reps=300, nb=10, shift=0.0, sd=0.1):
    rng = np.random.default_rng(seed)
    d = shift + rng.normal(0, sd, reps)
    boots = [list(map(float, d[r] + rng.normal(0, sd, nb))) for r in range(reps)]
    return pl.DataFrame(dict(scenario=[1] * reps, label=["x"] * reps, rep=list(range(reps)), delta_reml=d,
                             true_delta_obs=[shift] * reps, reml_boot=boots))


def test_warp_pvalue_matches_warp_ci_decision():
    for shift in (0.0, 0.25):
        df = _fake_warp(shift=shift)
        p = ps.warp_pvalues(df, "delta_reml", "reml_boot").sort("rep")
        dec = ps.warp_decisions(df, "delta_reml", "reml_boot")
        rej_p = ((p["p_warp"] < 0.05) & (p["delta_reml"] > 0)).mean()
        assert abs(rej_p - dec["reject"][0]) <= 2 / df.height   # identical up to quantile ties


def test_warp_calibrated_when_bootstrap_matches_sampling():
    df = _fake_warp(seed=1, reps=2000, nb=20)
    dec = ps.warp_decisions(df, "delta_reml", "reml_boot")
    assert abs(dec["reject"][0] - 0.025) < 0.012 and abs(dec["coverage95"][0] - 0.95) < 0.015
