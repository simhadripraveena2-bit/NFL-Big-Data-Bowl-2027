"""Phase 15 Part A supplement (measurement only): truncation-valid peak speed, cell-standardised G-study and the
decomposition of the speed-expression measures. Reads the git-ignored attempt table written by
run_phase15_wr_gstudy.py (same run). No NFL game data.

Pre-stated truncation rule (physical validity, not reliability): a route peak is valid only if the speed maximum is
not in the last 3 frames of the recording (otherwise the recording ended while the athlete was still accelerating);
routes where more than half of the attempts violate this (SLANT_ROUTE_LEFT, SLOT_STRIKE_ROUTE_LEFT) are excluded
from every peak-speed analysis.

Usage: python scripts/run_phase15_wr_supplement.py <wr_run_id>
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

SEED = 1517
B = 200
N_GRID = [1, 4, 6, 8, 10, 12]


def main():
    from nfl_bdb.features.phase15_measures import g_coef, gstudy
    from run_phase15_wr_gstudy import _boot
    run = sys.argv[1]
    A = pl.read_parquet(ROOT / "data" / "interim" / "phase15" / run / "wr_route_attempts.parquet").filter((pl.col("window") == 7) & pl.col("valid"))
    trunc_share = A.group_by("route").agg(pl.col("peak_in_last3").mean().alias("s"))
    bad = trunc_share.filter(pl.col("s") > 0.5)["route"].to_list()
    A = A.with_columns(pl.when(pl.col("peak_in_last3").fill_null(True) | pl.col("route").is_in(bad)).then(None).otherwise(pl.col("peak_speed")).alias("peak_valid"))
    A = A.with_columns(pl.when(pl.col("valid_tracked_40").fill_null(False)).then(pl.col("peak_valid")).otherwise(None).alias("peak_valid_xsub"),
                       (pl.col("peak_valid").log() - pl.col("x_peak").log()).alias("expr_logdiff_valid"))
    for c in ("peak_valid", "a_t_p95", "a_n_p95", "mean_speed_moving"):
        A = A.with_columns(((pl.col(c) - pl.col(c).mean().over("cell")) / pl.col(c).std().over("cell")).alias(f"{c}_z"))
    feats = ["peak_valid", "peak_valid_xsub", "expr_logdiff_valid", "peak_valid_z", "a_t_p95_z", "a_n_p95_z", "mean_speed_moving_z"]
    pdf = A.select("nfl_id", "route", "cell", *feats).to_pandas()
    rows, jobs = [], []
    for f in feats:
        d = pdf[["nfl_id", "route", "cell", f]].dropna()
        g = gstudy(d, f)
        rows.append(dict(feature=f, **g, **{f"G_{n}": g_coef(g["s2_athlete"], g["s2_athlete_route"], g["s2_residual"], n) for n in N_GRID}))
        jobs += [(f, SEED * 1000 + i, d.to_dict("records")) for i in range(B)]
    with ProcessPoolExecutor(max_workers=4, mp_context=get_context("spawn")) as ex:
        res = list(ex.map(_boot, jobs, chunksize=4))
    boot = {}
    for (f, _, _), r in zip(jobs, res):
        boot.setdefault(f, []).append(r)
    for row in rows:
        R = np.array(boot[row["feature"]], float); R = R[~np.isnan(R).any(axis=1)]
        for n in N_GRID:
            gg = [g_coef(a, b, c, n) for a, b, c in R]
            row[f"G_{n}_lo"], row[f"G_{n}_hi"] = (float(q) for q in np.percentile(gg, [2.5, 97.5]))
    # leave-one-route-out for the truncation-valid peak and the z-scored acceleration
    loro = []
    for f in ("peak_valid", "a_t_p95_z", "a_t_p95"):
        src = pdf if f in pdf else A.select("nfl_id", "route", "cell", f).to_pandas()
        for r in sorted(src["route"].unique()):
            d = src[src["route"] != r][["nfl_id", "route", "cell", f]].dropna()
            g = gstudy(d, f); loro.append(dict(feature=f, drop=r, G_10=g_coef(g["s2_athlete"], g["s2_athlete_route"], g["s2_residual"], 10), converged=g["converged"]))
    # expression decomposition (athlete level): cell-centred route log peak vs log tracked-40 peak
    first = A.filter((pl.col("attempt_order") == 0) & pl.col("valid_tracked_40").fill_null(False) & pl.col("peak_valid").is_not_null())
    first = first.with_columns((pl.col("peak_valid").log() - pl.col("peak_valid").log().mean().over("cell")).alias("lr"))
    am = first.group_by("nfl_id").agg(pl.col("lr").mean(), pl.col("x_peak").first().log().alias("lx"), pl.len().alias("k"))
    lr, lx = am["lr"].to_numpy(), am["lx"].to_numpy(); lx_c = lx - lx.mean(); ld = lr - lx_c
    dec = dict(n=am.height, var_log_route_athlete_mean=float(lr.var()), var_log_x_peak=float(lx.var()), cov=float(np.cov(lr, lx)[0, 1]),
               corr_route_vs_x=float(np.corrcoef(lr, lx)[0, 1]), corr_logdiff_vs_logx=float(np.corrcoef(ld, lx)[0, 1]),
               corr_logdiff_vs_route=float(np.corrcoef(ld, lr)[0, 1]), share_of_logdiff_var_from_x=float(lx.var() / ld.var()))
    out = ROOT / "experiments" / "phase15" / run
    pl.DataFrame(rows).write_csv(out / "wr_gstudy_supplement.csv"); pl.DataFrame(loro).write_csv(out / "wr_loro_supplement.csv")
    json.dump(dict(truncation_share=dict(trunc_share.iter_rows()), excluded_from_peak=bad, expression_decomposition=dec), open(out / "wr_supplement.json", "w"), indent=1)
    print("done", bad, dec)


if __name__ == "__main__":
    main()
