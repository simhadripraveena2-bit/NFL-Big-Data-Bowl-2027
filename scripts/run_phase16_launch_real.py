"""Phase 16 Parts A, C-F: WR route-launch acceleration vs straight-line sprint references (Combine data only).

Inputs: combine_tracking (WR route drills and WR FORTY_YARD_DASH), combine_results (ten_yd_split, forty, year) and the
registered combine-only tracked-40 peak (predictors.parquet: nfl_id, x_peak, valid_tracked_40). No NFL game data.
Definitions and decision rules: configs/phase16_protocol.json (committed 2a3fc47 before this script was run).

Usage: python scripts/run_phase16_launch_real.py
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
from scipy.stats import pearsonr, spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

INTERIM = ROOT / "data" / "interim"
JOIN_RUN = "20261121T135032Z"
SEED = 1616
B = 200
ROUTES = ["COMEBACK_ROUTE_RIGHT", "CURL_ROUTE_RIGHT", "DAGGER_ROUTE_LEFT", "GO_ROUTE_RIGHT", "OVER_SHOULDER_ADJUST",
          "POST_CORNER_ROUTE_LEFT", "POST_CORNER_ROUTE_RIGHT", "RED_ZONE_FADE_RIGHT", "SLANT_ROUTE_LEFT",
          "SLOT_SAIL_ROUTE_RIGHT", "SLOT_STRIKE_ROUTE_LEFT", "SPEED_OUT_ROUTE_LEFT", "SPEED_OUT_LEFT"]
HARMONISED = ["COMEBACK_ROUTE_RIGHT", "CURL_ROUTE_RIGHT", "DAGGER_ROUTE_LEFT", "GO_ROUTE_RIGHT", "OVER_SHOULDER_ADJUST",
              "POST_CORNER_ROUTE_RIGHT", "RED_ZONE_FADE_RIGHT", "SLANT_ROUTE_LEFT", "SLOT_SAIL_ROUTE_RIGHT", "SLOT_STRIKE_ROUTE_LEFT"]
N_GRID = [1, 4, 6, 8, 10, 12]
REFS = ["forty_launch", "ten_yd_split", "forty", "x_peak"]


def _boot_cov(args):
    feat, covs, seed, rows = args
    import pandas as pd
    from nfl_bdb.features.launch import gstudy_cov
    from nfl_bdb.features.phase15_measures import gstudy
    d = pd.DataFrame(rows); rng = np.random.default_rng(seed)
    ids = d["nfl_id"].unique(); pick = rng.choice(ids, len(ids), replace=True)
    parts = []
    for j, a in enumerate(pick):
        x = d[d["nfl_id"] == a].copy(); x["nfl_id"] = f"{a}_{j}"; parts.append(x)
    dd = pd.concat(parts)
    try:
        g0 = gstudy(dd, feat); g1 = gstudy_cov(dd, feat, covs)
        return (g0["s2_athlete"], g0["s2_athlete_route"], g0["s2_residual"], g1["s2_athlete"], g1["s2_athlete_route"], g1["s2_residual"])
    except Exception:
        return (np.nan,) * 6


def ci(x, fn, B_=2000, seed=SEED):
    rng = np.random.default_rng(seed); n = len(x[0]); out = []
    for _ in range(B_):
        j = rng.integers(0, n, n)
        out.append(fn(*[a[j] for a in x]))
    return [float(q) for q in np.nanpercentile(out, [2.5, 97.5])]


def main():
    from nfl_bdb.features.launch import gstudy_cov, launch
    from nfl_bdb.features.phase15_measures import g_coef, gstudy
    from nfl_bdb.evaluation.repeatability import two_attempt_stats
    from run_phase15_wr_gstudy import _boot
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dout = INTERIM / "phase16" / run; eout = ROOT / "experiments" / "phase16" / f"real_{run}"
    dout.mkdir(parents=True); eout.mkdir(parents=True); t0 = time.time()
    cr = pl.read_parquet(INTERIM / "combine_results.parquet").filter(pl.col("combine_position") == "WR").select("nfl_id", "draft_year", "ten_yd_split", "forty")
    xp = pl.read_parquet(INTERIM / "confirmatory_join" / JOIN_RUN / "predictors.parquet", columns=["nfl_id", "x_peak", "valid_tracked_40"])
    ct = pl.read_parquet(INTERIM / "combine_tracking.parquet").filter(
        (pl.col("entity_type") == "PLAYER") & pl.col("nfl_id").is_in(cr["nfl_id"].implode())
        & (((pl.col("drill_type") == "SKILL_DRILLS_WR") & pl.col("drill_name").is_in(ROUTES)) | (pl.col("drill_type") == "FORTY_YARD_DASH"))).sort("event_id", "time")
    rows = []
    for (eid,), g in ct.group_by(["event_id"], maintain_order=True):
        x, y = g["x"].to_numpy(), g["y"].to_numpy()
        for w in (5, 7, 9):
            L = launch(x, y, window=w)
            rows.append(dict(event_id=eid, nfl_id=int(g["nfl_id"][0]), drill=g["drill_type"][0], route=g["drill_name"][0],
                             draft_year=int(g["draft_year"][0]), t0=g["time"][0], n_frames=len(x), window=w,
                             **{k: L.get(k) for k in ("valid", "reason", "onset", "start_speed")},
                             **{k: L.get(k, np.nan) for k in ("p95", "mean_at", "net_gain")}))
    A = (pl.DataFrame(rows, infer_schema_length=None).sort("nfl_id", "drill", "route", "window", "t0")
         .with_columns(pl.int_range(pl.len()).over("nfl_id", "drill", "route", "window").alias("order"),
                       (pl.col("route") + "_" + pl.col("draft_year").cast(pl.Utf8)).alias("cell")))
    A.write_parquet(dout / "launch_attempts.parquet")
    summ = dict(run=run)
    # ---------------- Part A coverage / distributions ----------------
    for drill in ("SKILL_DRILLS_WR", "FORTY_YARD_DASH"):
        d = A.filter((pl.col("drill") == drill) & (pl.col("window") == 7))
        summ[f"coverage_{drill}"] = dict(attempts=d.height, athletes=int(d["nfl_id"].n_unique()), valid=int(d["valid"].sum()),
                                         reasons={str(k): int(v) for k, v in d.filter(~pl.col("valid")).group_by("reason").agg(pl.len().alias("c")).iter_rows()},
                                         onset_frame_pct=[float(q) for q in np.percentile(d.filter(pl.col("valid"))["onset"].to_numpy(), [5, 50, 95])])
    RW = A.filter((pl.col("drill") == "SKILL_DRILLS_WR") & pl.col("valid"))
    dist = RW.filter(pl.col("window") == 7).group_by("route", "draft_year").agg(
        pl.len().alias("n"), pl.col("p95").mean().alias("p95_mean"), pl.col("p95").std().alias("p95_sd"),
        pl.col("mean_at").mean().alias("mean_at_mean"), pl.col("net_gain").mean().alias("net_gain_mean"),
        pl.col("onset").median().alias("onset_median"), pl.col("n_frames").median().alias("frames_median")).sort("route", "draft_year")
    dist.write_csv(eout / "route_launch_distributions.csv")
    yr_cov = A.filter((pl.col("drill") == "SKILL_DRILLS_WR") & (pl.col("window") == 7)).group_by("draft_year").agg(
        pl.len().alias("attempts"), pl.col("valid").mean().alias("valid_rate"), (pl.col("start_speed") > 1.0).mean().alias("moving_at_first_frame"),
        pl.col("onset").median().alias("onset_median"), pl.col("n_frames").median().alias("frames_median"),
        pl.col("p95").filter(pl.col("valid")).mean().alias("p95_mean"), pl.col("p95").filter(pl.col("valid")).std().alias("p95_sd")).sort("draft_year")
    yr_cov.write_csv(eout / "year_coverage.csv")

    # athlete-level route score: z within route x year cell (all valid attempts), athlete mean over routes of route means
    def zscore(df, col):
        return df.with_columns(((pl.col(col) - pl.col(col).mean().over("cell")) / pl.col(col).std().over("cell")).alias(f"{col}_z"),
                               (pl.col(col) - pl.col(col).mean().over("cell")).alias(f"{col}_c"))
    R7 = zscore(RW.filter(pl.col("window") == 7), "p95")
    ath = (R7.group_by("nfl_id", "route").agg(pl.col("p95_z").mean(), pl.col("p95_c").mean())
           .group_by("nfl_id").agg(pl.col("p95_z").mean().alias("route_launch_z"), pl.col("p95_c").mean().alias("route_launch_c"), pl.len().alias("n_routes")))
    # forty reference: identical definition
    F7 = A.filter((pl.col("drill") == "FORTY_YARD_DASH") & (pl.col("window") == 7) & pl.col("valid"))
    fa = F7.group_by("nfl_id").agg(pl.col("p95").mean().alias("forty_launch"), pl.col("mean_at").mean().alias("forty_launch_mean"), pl.len().alias("n_forty"))
    f2 = F7.sort("nfl_id", "order").group_by("nfl_id", maintain_order=True).head(2).group_by("nfl_id").agg(pl.col("p95")).filter(pl.col("p95").list.len() == 2)
    a_, b_ = np.array([v[0] for v in f2["p95"].to_list()]), np.array([v[1] for v in f2["p95"].to_list()])
    st = two_attempt_stats(a_, b_)
    summ["forty_launch_test_retest"] = dict(n_pairs=len(a_), icc31=st["icc31"], icc21=st["icc21"], te=st["te"], te_pct=st["te_pct"],
                                            icc31_ci=ci([a_, b_], lambda p, q: two_attempt_stats(p, q)["icc31"], 1000))
    AT = ath.join(cr, on="nfl_id", how="left").join(fa, on="nfl_id", how="left").join(xp, on="nfl_id", how="left").with_columns(
        pl.when(pl.col("valid_tracked_40").fill_null(False)).then(pl.col("x_peak")).otherwise(None).alias("x_peak"))
    AT.write_parquet(dout / "athlete_launch_scores.parquet")
    summ["athlete_counts"] = dict(route_score=AT.height, **{f"with_{r}": int(AT[r].is_not_null().sum()) for r in REFS},
                                  with_all_refs=int(AT.drop_nulls(REFS).height))

    # ---------------- Part C correlations ----------------
    comp = []
    for score in ("route_launch_z", "route_launch_c"):
        for r in REFS:
            d = AT.select(score, r, "draft_year").drop_nulls()
            x, y = d[score].to_numpy(), d[r].to_numpy()
            yc = (d.with_columns((pl.col(r) - pl.col(r).mean().over("draft_year")).alias("rc"))["rc"]).to_numpy()
            comp.append(dict(score=score, ref=r, n=d.height, missing=AT.height - d.height, pearson=float(pearsonr(x, y).statistic),
                             pearson_ci=ci([x, y], lambda p, q: np.corrcoef(p, q)[0, 1]), spearman=float(spearmanr(x, y).statistic),
                             spearman_ci=ci([x, y], lambda p, q: spearmanr(p, q).statistic), pearson_ref_year_centred=float(np.corrcoef(x, yc)[0, 1])))
    json.dump(comp, open(eout / "sprint_comparison.json", "w"), indent=1)
    # variance explained (OLS), athletes with all references; standardised references
    d = AT.drop_nulls(REFS + ["route_launch_z"])
    yv = d["route_launch_z"].to_numpy(); r2 = []
    for cols in (["forty_launch"], ["ten_yd_split"], ["forty"], ["x_peak"], ["forty_launch", "x_peak"], REFS):
        X = np.column_stack([np.ones(len(yv))] + [(d[c].to_numpy() - d[c].mean()) / d[c].std() for c in cols])
        beta, *_ = np.linalg.lstsq(X, yv, rcond=None); res = yv - X @ beta
        rr = 1 - res.var() / yv.var(); k = len(cols)
        r2.append(dict(refs="+".join(cols), n=len(yv), r2=float(rr), adj_r2=float(1 - (1 - rr) * (len(yv) - 1) / (len(yv) - k - 1))))
    pl.DataFrame(r2).write_csv(eout / "variance_explained_ols.csv")
    nr = d["n_routes"].to_numpy()

    # ---------------- Part F G-study (frozen definition) ----------------
    def gst_rows(df, feat):
        g = gstudy(df, feat)
        return dict(**g, **{f"G_{n}": g_coef(g["s2_athlete"], g["s2_athlete_route"], g["s2_residual"], n) for n in N_GRID})
    gs, jobs = [], []
    for w in (5, 7, 9):
        Rw = zscore(RW.filter(pl.col("window") == w), "p95")
        for feat in ("p95", "p95_z"):
            pdf = Rw.select("nfl_id", "route", "cell", "draft_year", feat).drop_nulls().to_pandas()
            gs.append(dict(window=w, feature=feat, sample="all", **gst_rows(pdf, feat)))
            if w == 7:
                jobs += [(feat, SEED * 1000 + i, pdf[["nfl_id", "route", "cell", feat]].to_dict("records")) for i in range(B)]
                for yr in (2023, 2024, 2025):
                    sub = pdf[pdf["draft_year"] == yr]
                    gs.append(dict(window=w, feature=feat, sample=f"year={yr}", **gst_rows(sub, feat)))
                    subh = sub[sub["route"].isin(HARMONISED)]
                    gs.append(dict(window=w, feature=feat, sample=f"year={yr}_harmonised", **gst_rows(subh, feat)))
                gs.append(dict(window=w, feature=feat, sample="harmonised_all_years", **gst_rows(pdf[pdf["route"].isin(HARMONISED)], feat)))
                for r in ROUTES:
                    gs.append(dict(window=w, feature=feat, sample=f"drop={r}", **gst_rows(pdf[pdf["route"] != r], feat)))
    with ProcessPoolExecutor(max_workers=4, mp_context=get_context("spawn")) as ex:
        bres = list(ex.map(_boot, jobs, chunksize=4))
    boot = {}
    for (f, _, _), r in zip(jobs, bres):
        boot.setdefault(f, []).append(r)
    GS = pl.DataFrame(gs, infer_schema_length=None)
    cis = []
    for f, rs in boot.items():
        Rr = np.array(rs, float); Rr = Rr[~np.isnan(Rr).any(axis=1)]
        cis.append(dict(feature=f, n_boot=len(Rr), **{f"G_{n}_ci": [float(q) for q in np.percentile([g_coef(a, b, c, n) for a, b, c in Rr], [2.5, 97.5])] for n in N_GRID}))
    GS.write_csv(eout / "gstudy.csv"); json.dump(cis, open(eout / "gstudy_ci.json", "w"), indent=1)

    # ---------------- Part D residual athlete component ----------------
    Rz = zscore(RW.filter(pl.col("window") == 7), "p95").join(AT.select("nfl_id", *REFS), on="nfl_id", how="left")
    for c in REFS:
        Rz = Rz.with_columns(((pl.col(c) - pl.col(c).mean()) / pl.col(c).std()).alias(f"{c}_s"))
    dres = []
    for label, covs in (("forty_launch", ["forty_launch_s"]), ("all_refs", [f"{c}_s" for c in REFS])):
        pdf = Rz.select("nfl_id", "route", "cell", "p95_z", *[f"{c}_s" for c in REFS]).drop_nulls().to_pandas()
        g0 = gstudy(pdf, "p95_z"); g1 = gstudy_cov(pdf, "p95_z", covs)
        jobs2 = [("p95_z", covs, SEED * 7000 + i, pdf.to_dict("records")) for i in range(B)]
        with ProcessPoolExecutor(max_workers=4, mp_context=get_context("spawn")) as ex:
            br = np.array(list(ex.map(_boot_cov, jobs2, chunksize=4)), float)
        br = br[~np.isnan(br).any(axis=1)]
        share = 1 - br[:, 3] / br[:, 0]
        gres = np.array([g_coef(a, b, c, 10) for a, b, c in br[:, 3:]])
        dres.append(dict(covariates=label, n_athletes=g0["n_athletes"], n_obs=g0["n_obs"], s2_athlete_without=g0["s2_athlete"], s2_athlete_with=g1["s2_athlete"],
                         share_explained=1 - g1["s2_athlete"] / g0["s2_athlete"], share_explained_ci=[float(q) for q in np.percentile(share, [2.5, 97.5])],
                         G10_without=g_coef(g0["s2_athlete"], g0["s2_athlete_route"], g0["s2_residual"], 10),
                         G10_residual=g_coef(g1["s2_athlete"], g1["s2_athlete_route"], g1["s2_residual"], 10),
                         G10_residual_ci=[float(q) for q in np.percentile(gres, [2.5, 97.5])], coefs=g1["coefs"], n_boot=len(br)))
    json.dump(dres, open(eout / "residual_component.json", "w"), indent=1)
    summ["seconds"] = round(time.time() - t0)
    json.dump(summ, open(eout / "summary.json", "w"), indent=1, default=str)
    (ROOT / "experiments" / "phase16" / "LATEST_real").write_text(f"real_{run}")
    print(f"done in {time.time() - t0:.0f}s -> {eout}")


if __name__ == "__main__":
    main()
