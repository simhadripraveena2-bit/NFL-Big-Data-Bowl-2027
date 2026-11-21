"""Phase 3.5: simulation-based power analysis for the pre-registered H1, H2 and H5 tests.

Firewall (pre-registration):
  * Outcome side: REG-season play-level outcomes are used ONLY to estimate nuisance parameters
    (within-player SD, between-player variance, cross-context covariance, play counts).
  * Predictor side: combine measurements are used ONLY for their own distribution
    (within-position SDs and the peak-speed / 40 correlation), from all combine participants.
  * No combine value is joined to any game outcome. The only link is a player-ID availability
    flag (has a valid tracked 40), needed to reproduce the eligible sample sizes.
  * Effect sizes are a pre-specified GRID, not estimates.

Stages:  calibrate  -> experiments/power_analysis/<run>/calibration.json (+ residual pools)
         simulate   -> power tables (reads the LATEST calibration)
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nfl_bdb.data.io import load  # noqa: E402
from nfl_bdb.data.play_table import H1_COVARIATES, H2_COVARIATES, h1_frame, reg_play_table, residualise  # noqa: E402
from nfl_bdb.models import power as pw  # noqa: E402

OUTROOT = ROOT / "experiments" / "power_analysis"
CFG = dict(
    seed=3501, n_sims=2000, n_boot=400, alpha=0.05, holm_m=3,  # holm_m=3: conservative sensitivity; primary uses fixed-sequence (H1-WR -> H2)
    min_primary_opp=100,          # routes / rushes / blocks / coverage snaps (Phase 3 eligibility)
    min_ctx_plays=20,             # per context, H1 / H5
    min_deep_routes=30,           # H2 (deep routes with a separation value)
    contrasts={"WR": ["deep", "short"], "TE": ["deep", "short"], "DB": ["man", "under_zone"],
               "DL": ["pass_rush", "run"], "OL": ["pass_block", "run"]},
    rho_low_grid=[0.1, 0.3, 0.5], delta_grid=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
    h2_partial_grid=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7], h2_rho_forty_grid=[0.0, 0.3],
    forty_reliability_grid=[0.90, 0.95, 0.99], peak_reliability=0.987,
)
PRIMARY_OPP = {"WR": "route", "TE": "route", "DB": "coverage", "DL": "pass_rush", "OL": "pass_block"}


def tracked40_ids() -> pl.Series:
    run = (ROOT / "experiments/real_capacity/LATEST").read_text().strip()
    att = pl.read_parquet(ROOT / "experiments/real_capacity" / run / "combine_forty_attempts.parquet")
    return att.filter(pl.col("r2") > 0.95)["nfl_id"].unique()


def primary_opp_counts(d: pl.DataFrame) -> pl.DataFrame:
    e = {
        "route": pl.col("pos").is_in(["WR", "TE"]) & pl.col("is_pass") & pl.col("route_ran").is_not_null(),
        "pass_rush": pl.col("player_get_off").is_not_null(),
        "pass_block": pl.col("pass_rushers_encountered").is_not_null(),
        "coverage": pl.col("is_pass") & pl.col("coverage_assignment").is_not_null()
        & (pl.col("coverage_assignment") != "NO_ASSIGNMENT"),
    }
    return d.group_by("nfl_id", "pos").agg(*[v.sum().alias(k) for k, v in e.items()])


def variance_components(x: pl.DataFrame, col: str, ctxs: list[str]):
    """Moment estimates: pooled within-player SD per context; true between-player covariance of
    player-context means (observed covariance minus mean sampling variance on the diagonal)."""
    g = x.group_by("nfl_id", "ctx").agg(pl.len().alias("n"), pl.col(col).mean().alias("m"), pl.col(col).var().alias("v"))
    sw2 = {c: float((g.filter(pl.col("ctx") == c)["v"] * (g.filter(pl.col("ctx") == c)["n"] - 1)).sum()
                    / (g.filter(pl.col("ctx") == c)["n"] - 1).sum()) for c in ctxs}
    wide = g.pivot(index="nfl_id", on="ctx", values=["m", "n"]).drop_nulls()
    M = np.column_stack([wide[f"m_{c}"].to_numpy() for c in ctxs]); N = np.column_stack([wide[f"n_{c}"].to_numpy() for c in ctxs])
    S_obs = np.cov(M.T)
    S_true = S_obs - np.diag([np.mean(sw2[c] / N[:, k]) for k, c in enumerate(ctxs)])
    rel = [S_true[k, k] / S_obs[k, k] for k in range(len(ctxs))]
    corr_true = S_true[0, 1] / np.sqrt(max(S_true[0, 0], 1e-12) * max(S_true[1, 1], 1e-12))
    return dict(contexts=ctxs, n_players=int(M.shape[0]), counts=N.astype(int).tolist(),
                sd_within=[float(np.sqrt(sw2[c])) for c in ctxs], var_between=[float(S_true[k, k]) for k in range(len(ctxs))],
                reliability_mean=[float(r) for r in rel], corr_between_true=float(corr_true),
                median_plays=[float(np.median(N[:, k])) for k in range(len(ctxs))])


def calibrate():
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); out = OUTROOT / run; out.mkdir(parents=True, exist_ok=True)
    d = reg_play_table()
    ids = tracked40_ids()
    opp = primary_opp_counts(d)
    cal = {"config": CFG, "h1": {}, "h2": {}, "predictors": {}, "eligibility": {}}
    resid_pool = []
    for p, ctxs in CFG["contrasts"].items():
        elig = opp.filter((pl.col("pos") == p) & (pl.col(PRIMARY_OPP[p]) >= CFG["min_primary_opp"]) & pl.col("nfl_id").is_in(ids))
        x = h1_frame(d, p).join(elig.select("nfl_id"), on="nfl_id")
        x = x.with_columns(pl.Series("y_adj", residualise(x, "y", H1_COVARIATES[p])))
        cnt = x.group_by("nfl_id", "ctx").len().pivot(index="nfl_id", on="ctx", values="len").fill_null(0)
        keep = cnt.filter(pl.all_horizontal([pl.col(c) >= CFG["min_ctx_plays"] for c in ctxs]))["nfl_id"]
        x = x.filter(pl.col("nfl_id").is_in(keep) & pl.col("ctx").is_in(ctxs))
        vc = variance_components(x, "y_adj", ctxs)
        vc["eligible_primary"] = elig.height
        cal["h1"][p] = vc
        g = x.with_columns((pl.col("y_adj") - pl.col("y_adj").mean().over("nfl_id", "ctx")).alias("r"))
        resid_pool.append(g.select(pl.lit(p).alias("pos"), "ctx", "r"))
        print(p, {k: vc[k] for k in ("n_players", "sd_within", "var_between", "reliability_mean", "corr_between_true", "median_plays")}, flush=True)
    # H2: WR separation on deep routes (and short routes for the descriptive contrast)
    elig = opp.filter((pl.col("pos") == "WR") & (pl.col("route") >= CFG["min_primary_opp"]) & pl.col("nfl_id").is_in(ids))
    w = d.filter((pl.col("pos") == "WR") & pl.col("is_pass") & pl.col("route_depth").is_in(["deep", "short"])
                 & pl.col("separation_at_pass_forward").is_not_null()).join(elig.select("nfl_id"), on="nfl_id")
    w = w.with_columns(pl.Series("sep_adj", residualise(w, "separation_at_pass_forward", H2_COVARIATES)), pl.col("route_depth").alias("ctx"))
    nd = w.filter(pl.col("ctx") == "deep").group_by("nfl_id").len()
    keep = nd.filter(pl.col("len") >= CFG["min_deep_routes"])["nfl_id"]
    wk = w.filter(pl.col("nfl_id").is_in(keep))
    cnt = wk.group_by("nfl_id", "ctx").len().pivot(index="nfl_id", on="ctx", values="len").fill_null(0).filter(pl.col("short") >= CFG["min_ctx_plays"])
    vc = variance_components(wk.filter(pl.col("nfl_id").is_in(cnt["nfl_id"])), "sep_adj", ["deep", "short"])
    vc["eligible_primary"] = elig.height
    vc["eligible_deep_threshold"] = int(keep.len())
    cal["h2"]["WR"] = vc
    g = wk.with_columns((pl.col("sep_adj") - pl.col("sep_adj").mean().over("nfl_id", "ctx")).alias("r"))
    resid_pool.append(g.select(pl.lit("WR_sep").alias("pos"), "ctx", "r"))
    print("H2", {k: vc[k] for k in ("n_players", "sd_within", "var_between", "reliability_mean", "corr_between_true", "median_plays")})
    # eligibility funnel by threshold (counts only)
    for p in CFG["contrasts"]:
        o = opp.filter(pl.col("pos") == p)
        cal["eligibility"][p] = {str(t): int(o.filter((pl.col(PRIMARY_OPP[p]) >= t) & pl.col("nfl_id").is_in(ids)).height) for t in (50, 100, 200)}
    # predictor distribution (combine only, all participants)
    cr = load("combine_results", lazy=False).select("nfl_id", pl.col("combine_position").alias("pos"), "forty")
    run40 = (ROOT / "experiments/real_capacity/LATEST").read_text().strip()
    peak = (pl.read_parquet(ROOT / "experiments/real_capacity" / run40 / "combine_forty_attempts.parquet")
            .filter(pl.col("r2") > 0.95).group_by("nfl_id").agg(pl.col("vpeak").max().alias("peak")))
    c = cr.join(peak, on="nfl_id").drop_nulls()
    for p in CFG["contrasts"]:
        cc = c.filter(pl.col("pos") == p)
        cal["predictors"][p] = dict(n=cc.height, sd_peak=float(cc["peak"].std()), sd_forty=float(cc["forty"].std()),
                                    r_peak_forty=float(np.corrcoef(cc["peak"], cc["forty"])[0, 1]))
    json.dump(cal, open(out / "calibration.json", "w"), indent=1)
    pl.concat(resid_pool).write_parquet(out / "residual_pool.parquet")
    (OUTROOT / "LATEST").write_text(run)
    print("calibration ->", out)


def simulate():
    run = (OUTROOT / "LATEST").read_text().strip(); out = OUTROOT / run
    cal = json.load(open(out / "calibration.json")); pool = pl.read_parquet(out / "residual_pool.parquet")
    rng = np.random.default_rng(CFG["seed"]); t0 = time.time()
    a1 = pw.holm_first_alpha(CFG["alpha"], CFG["holm_m"])
    # ---- H1 / H5: dependent-correlation contrast within position -------------------------------
    rows = []
    for p, vc in cal["h1"].items():
        for rl in CFG["rho_low_grid"]:
            for dl in CFG["delta_grid"]:
                rh = rl + dl
                if rh > 0.95:
                    continue
                res = pw.power_h1(vc, rho_high=rh, rho_low=rl, n_sims=CFG["n_sims"], n_boot=CFG["n_boot"], rng=rng,
                                  alphas=(CFG["alpha"], a1), peak_rel=CFG["peak_reliability"])
                rows.append(dict(pos=p, rho_low=rl, delta=dl, n_players=vc["n_players"], **res))
        print("H1", p, round(time.time() - t0), "s", flush=True)
    h1 = pl.DataFrame(rows, infer_schema_length=None); h1.write_parquet(out / "power_h1.parquet")
    # sensitivity: player sample (n) and plays per context, WR + DB
    sens = []
    for p in ("WR", "DB", "OL"):
        vc = cal["h1"][p]
        for n in (18, 30, 45, 57, 80, 120):
            for ps in (0.5, 1.0, 2.0, 5.0):
                res = pw.power_h1(vc, rho_high=0.5, rho_low=0.3, n_sims=600, n_boot=200, rng=rng, alphas=(CFG["alpha"], a1),
                                  peak_rel=CFG["peak_reliability"], n_players=n, play_scale=ps)
                sens.append(dict(pos=p, n_players=n, play_scale=ps, rho_low=0.3, delta=0.2, **res))
    pl.DataFrame(sens, infer_schema_length=None).write_parquet(out / "power_h1_sensitivity.parquet")
    print("H1 sens", round(time.time() - t0), flush=True)
    # play-level validation of the player-level shortcut (empirical non-normal residuals)
    val = []
    for p in ("WR", "DB"):
        r = {c: pool.filter((pl.col("pos") == p) & (pl.col("ctx") == c))["r"].to_numpy() for c in cal["h1"][p]["contexts"]}
        for mode in ("normal", "empirical"):
            res = pw.power_h1(cal["h1"][p], rho_high=0.5, rho_low=0.3, n_sims=400, n_boot=200, rng=rng, alphas=(CFG["alpha"], a1),
                              peak_rel=CFG["peak_reliability"], play_level=True, resid=r if mode == "empirical" else None)
            val.append(dict(pos=p, mode=mode, **res))
    pl.DataFrame(val).write_parquet(out / "power_h1_playlevel_check.parquet")
    print("H1 val", round(time.time() - t0), flush=True)
    # ---- H2 -------------------------------------------------------------------------------------
    vc = cal["h2"]["WR"]; pr = cal["predictors"]["WR"]
    rows = []
    for relf in CFG["forty_reliability_grid"]:
        for rf in CFG["h2_rho_forty_grid"]:
            for pc in CFG["h2_partial_grid"]:
                res = pw.power_h2(vc, r_obs_peak_forty=abs(pr["r_peak_forty"]), forty_rel=relf, peak_rel=CFG["peak_reliability"],
                                  rho_forty=rf, partial=pc, n_sims=CFG["n_sims"], rng=rng, alphas=(CFG["alpha"], a1))
                rows.append(dict(forty_rel=relf, rho_forty=rf, partial=pc, n_players=vc["n_players"], **res))
    # (partial = 0 rows with forty_rel < 1 are the "false incremental value" scenario: the outcome depends on
    #  true 40 speed only, but the official 40 carries measurement error, so peak speed can look incremental.)
    pl.DataFrame(rows, infer_schema_length=None).write_parquet(out / "power_h2.parquet")
    # H2 vs number of players
    rows = []
    for n in (30, 41, 57, 80, 120, 200):
        for pc in (0.2, 0.3, 0.4):
            res = pw.power_h2(vc, r_obs_peak_forty=abs(pr["r_peak_forty"]), forty_rel=0.95, peak_rel=CFG["peak_reliability"],
                              rho_forty=0.3, partial=pc, n_sims=1000, rng=rng, alphas=(CFG["alpha"], a1), n_players=n)
            rows.append(dict(n_players=n, partial=pc, **res))
    pl.DataFrame(rows).write_parquet(out / "power_h2_by_n.parquet")
    # ---- H5: OL vs demand-model prediction (agreement test power) -------------------------------
    print("done", round(time.time() - t0), "s ->", out)


if __name__ == "__main__":
    {"calibrate": calibrate, "simulate": simulate}[sys.argv[1]]()
