"""Phase 15 Part A: WR route-drill movement profile, coverage audit and unbalanced generalizability study.

Measurement only. Inputs: combine_tracking (WR route drills), combine_results (position, year) and the registered
combine-only tracked-40 peak speed (predictors.parquet: nfl_id, x_peak, valid_tracked_40 only). No NFL game data.

Usage: python scripts/run_phase15_wr_gstudy.py
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

INTERIM = ROOT / "data" / "interim"
JOIN_RUN = "20261121T135032Z"
SEED = 1515
B = 200
ROUTES = ["COMEBACK_ROUTE_RIGHT", "CURL_ROUTE_RIGHT", "DAGGER_ROUTE_LEFT", "GO_ROUTE_RIGHT", "OVER_SHOULDER_ADJUST",
          "POST_CORNER_ROUTE_LEFT", "POST_CORNER_ROUTE_RIGHT", "RED_ZONE_FADE_RIGHT", "SLANT_ROUTE_LEFT",
          "SLOT_SAIL_ROUTE_RIGHT", "SLOT_STRIKE_ROUTE_LEFT", "SPEED_OUT_ROUTE_LEFT", "SPEED_OUT_LEFT"]
# SPEED_OUT_LEFT (2024) failed the Phase 14 15% geometry rule on the minor extent (ratio 1.15, borderline): it is kept
# as its own route label here; merging is a sensitivity analysis only. POST_CORNER LEFT/RIGHT are different routes.
SHORT = {"COMEBACK_ROUTE_RIGHT", "CURL_ROUTE_RIGHT", "SLANT_ROUTE_LEFT", "SLOT_STRIKE_ROUTE_LEFT", "SPEED_OUT_ROUTE_LEFT", "SPEED_OUT_LEFT"}
FEATURES = ["peak_speed", "mean_speed_moving", "a_t_p95", "a_n_p95", "decel_p05"]
N_GRID = [1, 2, 4, 6, 8, 10, 12]
MIN_FRAMES = 20


def _boot(args):
    feat, seed, rows = args
    import pandas as pd
    from nfl_bdb.features.phase15_measures import gstudy
    d = pd.DataFrame(rows); rng = np.random.default_rng(seed)
    ids = d["nfl_id"].unique(); pick = rng.choice(ids, len(ids), replace=True)
    parts = []
    for j, a in enumerate(pick):
        x = d[d["nfl_id"] == a].copy(); x["nfl_id"] = f"{a}_{j}"; parts.append(x)
    try:
        g = gstudy(pd.concat(parts), feat)
        return (g["s2_athlete"], g["s2_athlete_route"], g["s2_residual"])
    except Exception:
        return (np.nan, np.nan, np.nan)


def main():
    from nfl_bdb.features.phase15_measures import g_coef, gstudy
    from nfl_bdb.features.skill_drills import descriptors
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dout = INTERIM / "phase15" / run; eout = ROOT / "experiments" / "phase15" / run
    dout.mkdir(parents=True); eout.mkdir(parents=True); t0 = time.time()
    ct = pl.read_parquet(INTERIM / "combine_tracking.parquet").filter(
        (pl.col("drill_type") == "SKILL_DRILLS_WR") & (pl.col("entity_type") == "PLAYER") & pl.col("drill_name").is_in(ROUTES)).sort("event_id", "time")
    xp = pl.read_parquet(INTERIM / "confirmatory_join" / JOIN_RUN / "predictors.parquet", columns=["nfl_id", "x_peak", "valid_tracked_40"])
    rows = []
    for (eid,), g in ct.group_by(["event_id"], maintain_order=True):
        x, y, s = g["x"].to_numpy(), g["y"].to_numpy(), g["s"].to_numpy()
        base = dict(event_id=eid, nfl_id=int(g["nfl_id"][0]), route=g["drill_name"][0], draft_year=int(g["draft_year"][0]),
                    t0=g["time"][0], n_frames=len(x))
        for w in (5, 7, 9):
            dsc = descriptors(x, y, window=w)
            from nfl_bdb.features.skill_drills import kinematics
            sp = kinematics(x, y, w)["speed"] if len(x) >= w + 2 else np.array([np.nan])
            rows.append(dict(base, window=w, ok=bool(dsc.get("ok")), **{f: dsc.get(f, np.nan) for f in FEATURES},
                             peak_in_last3=bool(np.nanargmax(sp) >= len(sp) - 3) if len(sp) > 3 else None,
                             start_moving=bool(dsc.get("start_speed", 0) >= 1.0), end_moving=bool(dsc.get("end_speed", 0) >= 1.0),
                             peak_speed_provided=float(np.max(s))))
    A = (pl.DataFrame(rows, infer_schema_length=None).sort("nfl_id", "route", "window", "t0")
         .with_columns(pl.int_range(pl.len()).over("nfl_id", "route", "window").alias("attempt_order"),
                       (pl.col("route") + "_" + pl.col("draft_year").cast(pl.Utf8)).alias("cell"))
         .join(xp, on="nfl_id", how="left"))
    A = A.with_columns(valid=(pl.col("ok") & (pl.col("n_frames") >= MIN_FRAMES)))
    A = A.with_columns((pl.col("peak_speed") / pl.col("x_peak")).alias("expr_ratio"),
                       (pl.col("peak_speed").log() - pl.col("x_peak").log()).alias("expr_logdiff"))
    A.write_parquet(dout / "wr_route_attempts.parquet")
    A7 = A.filter((pl.col("window") == 7) & pl.col("valid"))
    summ = dict(run=run, routes=ROUTES, min_frames=MIN_FRAMES)

    # ---------------- A1 coverage ----------------
    cov = (A.filter(pl.col("window") == 7).group_by("route", "draft_year").agg(
        pl.col("nfl_id").n_unique().alias("athletes"), pl.len().alias("attempts"), pl.col("valid").sum().alias("valid_attempts"),
        pl.col("n_frames").median().alias("frames_median"), pl.col("n_frames").min().alias("frames_min"),
        pl.col("start_moving").mean().alias("start_moving_share"), pl.col("end_moving").mean().alias("end_moving_share"),
        pl.col("peak_in_last3").mean().alias("peak_in_last3_share"),
        (pl.col("attempt_order") >= 1).sum().alias("repeat_attempts")).sort("route", "draft_year"))
    cov.write_csv(eout / "wr_coverage_route_year.csv")
    cohort = pl.read_parquet(INTERIM / "combine_results.parquet").filter(pl.col("combine_position") == "WR").select("nfl_id", "draft_year")
    wr_skill = A7.select("nfl_id").unique()
    per = A7.filter(pl.col("attempt_order") == 0).group_by("nfl_id", "draft_year").agg(pl.col("route").sort().alias("routes"), pl.len().alias("k"))
    combos = per.with_columns(pl.col("routes").list.join("|").alias("combo")).group_by("draft_year", "combo").len().sort("draft_year", "len", descending=[False, True])
    summ["coverage"] = dict(
        wr_combine=cohort.height, wr_with_valid_route=wr_skill.height,
        routes_per_athlete={str(k): int(v) for k, v in per.group_by("k").len().sort("k").iter_rows()},
        routes_per_athlete_by_year={str(y): {str(k): int(v) for k, v in per.filter(pl.col("draft_year") == y).group_by("k").len().sort("k").iter_rows()} for y in (2023, 2024, 2025)},
        distinct_route_sets=int(combos.height), most_common_sets=combos.group_by("draft_year").head(3).to_dicts(),
        invalid_attempts=int(A.filter((pl.col("window") == 7) & ~pl.col("valid")).height),
        with_x_peak=int(A7.filter(pl.col("valid_tracked_40").fill_null(False)).select("nfl_id").n_unique()))

    # ---------------- A3 G-study ----------------
    feats = FEATURES + ["expr_ratio", "expr_logdiff", "peak_speed_xsub"]
    A7 = A7.with_columns(pl.when(pl.col("valid_tracked_40").fill_null(False)).then(pl.col("peak_speed")).otherwise(None).alias("peak_speed_xsub"))
    pdf = A7.select("nfl_id", "route", "cell", "draft_year", *feats).to_pandas()
    gs_rows, boot_jobs = [], []
    for f in feats:
        d = pdf[["nfl_id", "route", "cell", f]].dropna()
        g = gstudy(d, f)
        gs_rows.append(dict(feature=f, sample="all", window=7, **g, **{f"G_{n}": g_coef(g["s2_athlete"], g["s2_athlete_route"], g["s2_residual"], n) for n in N_GRID}))
        recs = d.to_dict("records")
        boot_jobs += [(f, SEED * 1000 + i, recs) for i in range(B)]
    with ProcessPoolExecutor(max_workers=4, mp_context=get_context("spawn")) as ex:
        res = list(ex.map(_boot, boot_jobs, chunksize=4))
    boot = {}
    for (f, _, _), r in zip(boot_jobs, res):
        boot.setdefault(f, []).append(r)
    ci_rows = []
    for f, rs in boot.items():
        R = np.array(rs, float); R = R[~np.isnan(R).any(axis=1)]
        row = dict(feature=f, n_boot=len(R))
        for j, nm in enumerate(("s2_athlete", "s2_athlete_route", "s2_residual")):
            row[f"{nm}_lo"], row[f"{nm}_hi"] = np.percentile(R[:, j], [2.5, 97.5])
        for n in N_GRID:
            gg = np.array([g_coef(a, b, c, n) for a, b, c in R])
            row[f"G_{n}_lo"], row[f"G_{n}_hi"] = np.percentile(gg, [2.5, 97.5])
        ci_rows.append(row)
    GS = pl.DataFrame(gs_rows).join(pl.DataFrame(ci_rows), on="feature", how="left")
    GS.write_csv(eout / "wr_gstudy_main.csv")

    # within-year, processing sensitivity, SPEED_OUT merge, leave-one-route-out
    sens = []
    for f in FEATURES + ["expr_logdiff"]:
        for yr in (2023, 2024, 2025):
            d = pdf[pdf["draft_year"] == yr][["nfl_id", "route", "cell", f]].dropna()
            g = gstudy(d, f); sens.append(dict(feature=f, variant=f"year={yr}", **g, G_6=g_coef(g["s2_athlete"], g["s2_athlete_route"], g["s2_residual"], 6),
                                               G_10=g_coef(g["s2_athlete"], g["s2_athlete_route"], g["s2_residual"], 10)))
        for w in (5, 9):
            dw = A.filter((pl.col("window") == w) & pl.col("valid")).select("nfl_id", "route", "cell", f).drop_nulls().to_pandas()
            g = gstudy(dw, f); sens.append(dict(feature=f, variant=f"window={w}", **g, G_6=g_coef(g["s2_athlete"], g["s2_athlete_route"], g["s2_residual"], 6),
                                                G_10=g_coef(g["s2_athlete"], g["s2_athlete_route"], g["s2_residual"], 10)))
        dm = pdf[["nfl_id", "route", "cell", f]].dropna().copy()
        dm["route"] = dm["route"].replace({"SPEED_OUT_LEFT": "SPEED_OUT_ROUTE_LEFT"}); dm["cell"] = dm["cell"].str.replace("SPEED_OUT_LEFT", "SPEED_OUT_ROUTE_LEFT")
        g = gstudy(dm, f); sens.append(dict(feature=f, variant="speed_out_merged", **g, G_6=g_coef(g["s2_athlete"], g["s2_athlete_route"], g["s2_residual"], 6),
                                            G_10=g_coef(g["s2_athlete"], g["s2_athlete_route"], g["s2_residual"], 10)))
        for r in ROUTES:
            d = pdf[pdf["route"] != r][["nfl_id", "route", "cell", f]].dropna()
            g = gstudy(d, f); sens.append(dict(feature=f, variant=f"drop={r}", **g, G_6=g_coef(g["s2_athlete"], g["s2_athlete_route"], g["s2_residual"], 6),
                                               G_10=g_coef(g["s2_athlete"], g["s2_athlete_route"], g["s2_residual"], 10)))
    dp = A7.select("nfl_id", "route", "cell", pl.col("peak_speed_provided")).to_pandas()
    g = gstudy(dp, "peak_speed_provided")
    sens.append(dict(feature="peak_speed", variant="provided_s", **g, G_6=g_coef(g["s2_athlete"], g["s2_athlete_route"], g["s2_residual"], 6),
                     G_10=g_coef(g["s2_athlete"], g["s2_athlete_route"], g["s2_residual"], 10)))
    pl.DataFrame(sens, infer_schema_length=None).write_csv(eout / "wr_gstudy_sensitivity.csv")

    # empirical subset stability: disjoint random route subsets of size k (athletes with >= 2k routes), cell-centred values
    rng = np.random.default_rng(SEED)
    first = A7.filter(pl.col("attempt_order") == 0)
    stab = []
    for f in FEATURES + ["expr_logdiff"]:
        c = first.with_columns((pl.col(f) - pl.col(f).mean().over("cell")).alias("z")).filter(pl.col("z").is_not_null() & pl.col("z").is_not_nan())
        per_a = c.group_by("nfl_id").agg(pl.col("z"), pl.col("route"))
        for k in (2, 3, 4, 5, 6):
            el = [(np.array(z), np.array(rr)) for z, rr in zip(per_a["z"].to_list(), per_a["route"].to_list()) if len(z) >= 2 * k]
            if len(el) < 20:
                continue
            rs = []
            for _ in range(300):
                h1, h2 = [], []
                for z, _rr in el:
                    p = rng.permutation(len(z)); h1.append(z[p[:k]].mean()); h2.append(z[p[k:2 * k]].mean())
                rs.append(np.corrcoef(h1, h2)[0, 1])
            stab.append(dict(feature=f, k=k, athletes=len(el), r_median=float(np.median(rs)), r_lo=float(np.percentile(rs, 2.5)), r_hi=float(np.percentile(rs, 97.5))))
        # composition: short-route mean vs long-route mean
        cc = c.with_columns(pl.col("route").is_in(list(SHORT)).alias("short")).group_by("nfl_id", "short").agg(pl.col("z").mean(), pl.len().alias("n"))
        w = cc.pivot(index="nfl_id", on="short", values="z").drop_nulls()
        if w.height > 20:
            stab.append(dict(feature=f, k="short_vs_long", athletes=w.height, r_median=float(np.corrcoef(w["true"], w["false"])[0, 1])))
    pl.DataFrame(stab, infer_schema_length=None).write_csv(eout / "wr_subset_stability.csv")

    # A4: route speed vs tracked-40 peak (athlete level, cell-centred route peak means; descriptive)
    am = first.filter(pl.col("valid_tracked_40").fill_null(False)).with_columns((pl.col("peak_speed") - pl.col("peak_speed").mean().over("cell")).alias("zc")).group_by("nfl_id").agg(
        pl.col("zc").mean(), pl.col("peak_speed").mean().alias("raw_mean"), pl.col("x_peak").first(), pl.col("draft_year").first(), pl.len().alias("k"))
    summ["expression"] = dict(n_athletes=am.height, corr_raw_route_peak_vs_x_peak=float(np.corrcoef(am["raw_mean"], am["x_peak"])[0, 1]),
                              corr_cell_centred_route_peak_vs_x_peak=float(np.corrcoef(am["zc"], am["x_peak"])[0, 1]),
                              route_peak_over_x_peak_median=float(first.filter(pl.col("valid_tracked_40").fill_null(False))["expr_ratio"].median()),
                              route_peak_over_x_peak_p05_p95=[float(q) for q in np.nanpercentile(first.filter(pl.col("valid_tracked_40").fill_null(False))["expr_ratio"].to_numpy(), [5, 95])])
    summ["seconds"] = round(time.time() - t0)
    json.dump(dict(run=run, seed=SEED, B=B, routes=ROUTES, features=feats, n_grid=N_GRID, join_run=JOIN_RUN, min_frames=MIN_FRAMES), open(eout / "wr_config.json", "w"), indent=1)
    json.dump(summ, open(eout / "wr_summary.json", "w"), indent=1, default=str)
    (ROOT / "experiments" / "phase15" / "LATEST_wr").write_text(run)
    print(f"done in {time.time() - t0:.0f}s -> {eout}")


if __name__ == "__main__":
    main()
