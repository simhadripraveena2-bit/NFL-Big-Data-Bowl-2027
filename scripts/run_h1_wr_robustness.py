"""H1-WR registered robustness checks, registered negative control, and interval diagnostics (post-primary).

The primary result (experiments/h1_wr_confirmatory/20261121T223645Z) is NOT touched or recomputed.

REGISTERED sensitivity analyses (preregistration §3.4, §5, §7, §10, §13; spec §1.4, §4), each with the registered
inference (full REML player-cluster bootstrap, B = 2000, `h1_registered_test`) unless stated:
  R1  eligibility threshold >= 50 primary opportunities (>= 20 plays per context)
  R2  eligibility threshold >= 200
  R3  without the time-to-throw covariate
  R4  REG + POST plays (same 57 players; POST features rebuilt with the validated Phase 3 definition)
  R5  leave-one-team-out (point estimates, 1 fit per team)
  R6  ceiling-robust outcome: bivariate player-level ME model (player bootstrap B = 2000)
  R7  natural cubic spline, 3 df: average-derivative difference (player bootstrap B = 2000) + player-grouped CV
  R8  mean-of-attempts combine peak speed
  R9  IN / CROSS assigned to short routes
  R10 eligibility (inverse-probability) weights  -> not computable with the frozen REML engine (documented)
  R11 playing-time sensitivity model (player log routes x context added)  [§3.4 "appear only in a sensitivity model"]
  R12 draft-class-specific estimates (§7 "class-specific sensitivity"); the 2025 class doubles as the §13 new-player subset
  R13 season-forward: 2023+2024 fit and 2025 fit, each with CI (spec §4 "sign and CI")
  R14 eligible vs ineligible WRs on official 40 and draft round (§5)
REGISTERED negative control (spec §4): N1 context labels permuted within player (500 permutations, point estimates).
  (The other two registered negative controls, OL contrast and WR short-route beta_P, belong to H5 / H2: not run.)
DIAGNOSTICS: Wald interval (spec §10 check; numerical REML Hessian), leave-one-team-season-out, jackknife influence.
Frames for R1, R2, R4, R9 are built with the frozen join functions from the single join's predictors.parquet.
Seeds are declared in SEEDS below before any run.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nfl_bdb.data import confirmatory_data as cd  # noqa: E402
from nfl_bdb.data.play_table import H1_COVARIATES, h1_frame  # noqa: E402
from nfl_bdb.models import confirmatory as cf  # noqa: E402
from nfl_bdb.models import h1_extensions as hx  # noqa: E402

JOIN = ROOT / "data/interim/confirmatory_join/20261121T135032Z"
PRIMARY = ROOT / "experiments/h1_wr_confirmatory/20261121T223645Z"
OUTROOT = ROOT / "experiments/h1_wr_robustness"
COVS = H1_COVARIATES["WR"]
B = cf.H1_B_REGISTERED
SEEDS = dict(R1=5001, R2=5002, R3=5003, R4=5004, R6=5006, R6_inner=5106, R7=5007, R7_cv=5107, R8=5008, R9=5009,
             R11=5011, R12_2023=5012, R12_2024=5112, R12_2025=5212, R13_2324=5013, R13_2025=5113, N1=6001)
N_PERM = 500


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


# ------------------------------------------------------------------------------------------------ frames
def frames():
    pred = pl.read_parquet(JOIN / "predictors.parquet")
    base = pl.read_parquet(JOIN / "h1_WR.parquet")
    d, _ = cd.outcome_table()
    cols = base.columns
    F = {"base": base}
    for t, k in ((50, "R1"), (200, "R2")):
        fr, el = cd.h1_eligible(d, pred, "WR", min_opp=t)
        F[k] = cd.join_predictors(fr, pred).select(cols)
    # R4: REG + POST for the same players
    post_feat = hx.prepass_features(("POST",))
    dp = hx.play_table(("POST",), post_feat)
    dp = dp.filter(pl.col("play_nullified_by_penalty").fill_null("N") != "Y")
    dp = dp.join(pl.DataFrame({"game_id": [g for g, _ in cd.FAULTY], "play_id": [p for _, p in cd.FAULTY]}), on=["game_id", "play_id"], how="anti")
    fp = h1_frame(dp, "WR").filter(pl.col("nfl_id").is_in(base["nfl_id"].unique().implode()) & pl.col("ctx").is_in(["deep", "short"]))
    fp = cd.join_predictors(fp, pred).select(cols)
    F["R4"] = pl.concat([base, fp]); F["R4_post_only_plays"] = fp
    # R9: IN / CROSS as short (same eligibility rule re-applied)
    w = d.filter((pl.col("pos") == "WR") & pl.col("is_pass") & pl.col("route_ran").is_in(["GO", "POST", "CORNER", "WHEEL", "HITCH", "SLANT", "OUT", "FLAT", "SCREEN", "ANGLE", "IN", "CROSS"]))
    w = w.with_columns(pl.col("vmax_prepass").alias("y"), pl.when(pl.col("route_depth") == "deep").then(pl.lit("deep")).otherwise(pl.lit("short")).alias("ctx")).filter(pl.col("y").is_not_null())
    el = pl.read_parquet(JOIN / "eligibility_h1_WR.parquet").filter(pl.col("elig_all"))
    w = hx.min_ctx_filter(w.filter(pl.col("nfl_id").is_in(el["nfl_id"].implode())))
    F["R9"] = cd.join_predictors(w, pred).select(cols)
    return F, pred, d


def run_test(args):
    name, df, covs, xcol, seed, extra = args
    t0 = time.time()
    dfi, ids = hx.index_frame(df)
    player, ctx, team, y = dfi["pid"].to_numpy(), dfi["ctx_i"].to_numpy(), dfi["team_i"].to_numpy(), dfi["y"].to_numpy().astype(float)
    xp = dfi.group_by("pid").agg(pl.col(xcol).first()).sort("pid")[xcol].to_numpy()
    Xw = cf.design_h1(dfi, covs, 2)
    if extra == "playtime":
        opp = pl.read_parquet(JOIN / "eligibility_h1_WR.parquet").select("nfl_id", "opp")
        lo = dfi.select("pid", "nfl_id").unique().sort("pid").join(opp, on="nfl_id", how="left")["opp"].to_numpy().astype(float)
        lz = (np.log(lo) - np.log(lo).mean()) / np.log(lo).std(ddof=1)
        Xw = np.column_stack([Xw] + [lz[player] * (ctx == c) for c in (0, 1)])
    r = cf.h1_registered_test(player, ctx, team, y, Xw, xp, seed=seed, B=B)
    boot = r.pop("boot")
    return dict(name=name, delta=r["delta"], rho_deep=float(r["rho"][0]), rho_short=float(r["rho"][1]), ci_lo=r["ci_lo"], ci_hi=r["ci_hi"],
                ci90=[float(v) for v in np.percentile(boot, [5, 95])], se_boot=r["se_boot"], p=r["p"], n_ok=r["n_ok"], converged=r["converged"],
                players=len(xp), plays=dfi.height, plays_deep=int((ctx == 0).sum()), plays_short=int((ctx == 1).sum()),
                team_seasons=int(team.max() + 1), seed=seed, seconds=time.time() - t0, boot=boot.tolist())


def run_spline(args):
    df, knots, seed = args
    dfi, _ = hx.index_frame(df)
    player, ctx, team, y = dfi["pid"].to_numpy(), dfi["ctx_i"].to_numpy(), dfi["team_i"].to_numpy(), dfi["y"].to_numpy().astype(float)
    xp = dfi.group_by("pid").agg(pl.col("x_peak").first()).sort("pid")["x_peak"].to_numpy()
    Xw = cf.design_h1(dfi, COVS, 2)
    full = hx.spline_fit(player, ctx, team, y, Xw, xp, knots)
    lin = cf.h1_reml(player, ctx, team, y, Xw, xp)
    bs = hx.spline_bootstrap(player, ctx, team, y, Xw, xp, knots, B, seed, start=full["fit"].theta)
    grid = np.linspace(full["xs"].min(), full["xs"].max(), 41)
    curves = (hx.ns_basis(grid, full["knots_std"]) @ full["coef"].T).T
    return dict(avg_deriv=full["avg_deriv"].tolist(), diff=full["diff"], linear_slope=lin.beta.tolist(), linear_slope_diff=float(lin.beta[0] - lin.beta[1]),
                converged=full["fit"].converged, boot=bs.tolist(), grid=grid.tolist(), curves=curves.tolist(), knots_std=full["knots_std"].tolist())


def run_spline_cv(args):
    df, knots, seed = args
    dfi, ids = hx.index_frame(df)
    xp = dfi.group_by("pid").agg(pl.col("x_peak").first()).sort("pid")["x_peak"].to_numpy()
    dc = dfi.group_by("pid").agg(pl.col("draft_year").first()).sort("pid")["draft_year"].to_numpy()
    return hx.grouped_cv_linear_vs_spline(dfi, COVS, xp, knots, dc, seed).to_dicts()


def run_perm(args):
    df, seeds = args
    dfi, _ = hx.index_frame(df)
    xp = dfi.group_by("pid").agg(pl.col("x_peak").first()).sort("pid")["x_peak"].to_numpy()
    out = []
    for s in seeds:
        p = hx.permute_within_player(dfi, np.random.default_rng(s))
        r = cf.h1_reml(p["pid"].to_numpy(), p["ctx_i"].to_numpy(), p["team_i"].to_numpy(), p["y"].to_numpy().astype(float), cf.design_h1(p, COVS, 2), xp)
        out.append(dict(seed=s, delta=r.delta, rho_deep=float(r.rho[0]), rho_short=float(r.rho[1]), converged=r.converged))
    return out


def point(df, drop_min_ctx=True):
    df = hx.min_ctx_filter(df) if drop_min_ctx else df
    dfi, _ = hx.index_frame(df)
    xp = dfi.group_by("pid").agg(pl.col("x_peak").first()).sort("pid")["x_peak"].to_numpy()
    r = cf.h1_reml(dfi["pid"].to_numpy(), dfi["ctx_i"].to_numpy(), dfi["team_i"].to_numpy(), dfi["y"].to_numpy().astype(float), cf.design_h1(dfi, COVS, 2), xp)
    return dict(delta=r.delta, rho_deep=float(r.rho[0]), rho_short=float(r.rho[1]), players=len(xp), plays=dfi.height, converged=r.converged)


def main():
    if git("status", "--porcelain", "--", "src", "scripts", "tests"):
        raise SystemExit("refusing to run from uncommitted code")
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); out = OUTROOT / run; out.mkdir(parents=True)
    t0 = time.time()
    F, pred, d = frames()
    base = F["base"]
    print("frames:", {k: (v.height, v["nfl_id"].n_unique()) for k, v in F.items()}, flush=True)
    wr_all_x = pred.filter((pl.col("pos") == "WR") & pl.col("x_peak").is_not_null())["x_peak"].to_numpy()
    knots = np.quantile(wr_all_x, [0, 1 / 3, 2 / 3, 1])   # tertiles of all WR combine participants (boundary widened to sample range)

    jobs = [("R1", F["R1"], COVS, "x_peak", SEEDS["R1"], None), ("R2", F["R2"], COVS, "x_peak", SEEDS["R2"], None),
            ("R3", base, [c for c in COVS if c != "ttt_bin"], "x_peak", SEEDS["R3"], None), ("R4", F["R4"], COVS, "x_peak", SEEDS["R4"], None),
            ("R8", base, COVS, "x_peak_mean", SEEDS["R8"], None), ("R9", F["R9"], COVS, "x_peak", SEEDS["R9"], None),
            ("R11", base, COVS, "x_peak", SEEDS["R11"], "playtime"),
            ("R13_2023_2024", hx.min_ctx_filter(base.filter(pl.col("season") <= 2024)), COVS, "x_peak", SEEDS["R13_2324"], None),
            ("R13_2025", hx.min_ctx_filter(base.filter(pl.col("season") == 2025)), COVS, "x_peak", SEEDS["R13_2025"], None)]
    for cls in (2023, 2024, 2025):
        jobs.append((f"R12_class_{cls}", base.filter(pl.col("draft_year") == cls), COVS, "x_peak", SEEDS[f"R12_{cls}"], None))
    perm_seeds = [SEEDS["N1"] + i for i in range(N_PERM)]
    res = {}
    # spawn (not fork): forking after polars' thread pool has started deadlocks (first attempt hung at 0 % CPU)
    with ProcessPoolExecutor(4, mp_context=mp.get_context("spawn")) as ex:
        fut_sp = ex.submit(run_spline, (base, knots, SEEDS["R7"]))
        fut_cv = ex.submit(run_spline_cv, (base, knots, SEEDS["R7_cv"]))
        futs = {j[0]: ex.submit(run_test, j) for j in jobs}
        fut_perm = [ex.submit(run_perm, (base, perm_seeds[i::4])) for i in range(4)]
        for k, f in futs.items():
            res[k] = f.result(); print(k, round(res[k]["delta"], 3), [round(res[k]["ci_lo"], 3), round(res[k]["ci_hi"], 3)], flush=True)
        spline = fut_sp.result(); cv = fut_cv.result(); perm = sum((f.result() for f in fut_perm), [])
    np.savez(out / "bootstraps.npz", **{k: np.array(v.pop("boot")) for k, v in res.items()}, spline=np.array(spline.pop("boot")))

    # R5 leave-one-team-out and diagnostic leave-one-team-season-out (point estimates)
    loto = [dict(team=t, **point(base.filter(pl.col("team_abbr") != t))) for t in sorted(base["team_abbr"].unique().to_list())]
    ts = base.with_columns((pl.col("team_abbr") + "_" + pl.col("season").cast(pl.Utf8)).alias("ts"))
    lotso = [dict(team_season=t, **point(ts.filter(pl.col("ts") != t).drop("ts"))) for t in sorted(ts["ts"].unique().to_list())]

    # R6 ceiling-robust
    dfi, _ = hx.index_frame(base)
    ct = hx.ceiling_table(dfi, SEEDS["R6_inner"])
    U = np.column_stack([ct.filter(pl.col("ctx_i") == c)["u"].to_numpy() for c in (0, 1)])
    VE = np.column_stack([ct.filter(pl.col("ctx_i") == c)["var_e"].to_numpy() for c in (0, 1)])
    xp = dfi.group_by("pid").agg(pl.col("x_peak").first()).sort("pid")["x_peak"].to_numpy()
    rho, beta, S = hx.ceiling_rho(U, VE, xp)
    rng = np.random.default_rng(SEEDS["R6"]); cb = []
    for _ in range(B):
        i = rng.integers(0, len(xp), len(xp)); r_, _, _ = hx.ceiling_rho(U[i], VE[i], xp[i]); cb.append(r_[0] - r_[1])
    cb = np.array(cb)
    ceiling = dict(delta=float(rho[0] - rho[1]), rho=rho.tolist(), beta=beta.tolist(), sigma_b=S.tolist(), ci=[float(v) for v in np.percentile(cb, [2.5, 97.5])],
                   ci90=[float(v) for v in np.percentile(cb, [5, 95])], se_boot=float(cb.std()), players=len(xp),
                   mean_upper_expression=U.mean(0).tolist(), mean_me_var=VE.mean(0).tolist(), min_plays=int(ct["n"].min()))

    # Wald check (spec §10) on the primary frame
    player, ctx, team, y = dfi["pid"].to_numpy(), dfi["ctx_i"].to_numpy(), dfi["team_i"].to_numpy(), dfi["y"].to_numpy().astype(float)
    wald = hx.wald_delta(player, ctx, team, y, cf.design_h1(dfi, COVS, 2), xp)
    wald["ci95"] = [wald["delta"] - 1.959964 * wald["se"], wald["delta"] + 1.959964 * wald["se"]]
    wald["ci90"] = [wald["delta"] - 1.644854 * wald["se"], wald["delta"] + 1.644854 * wald["se"]]

    # R14 eligible vs ineligible WRs (official 40, draft round; combine + draft data only)
    players = pl.read_parquet(ROOT / "data/interim/players.parquet").select("nfl_id", "draft_round")
    el = pl.read_parquet(JOIN / "eligibility_h1_WR.parquet").select("nfl_id", "elig_h1")
    wr = pred.filter((pl.col("pos") == "WR") & pl.col("valid_tracked_40")).join(el, on="nfl_id", how="left").with_columns(pl.col("elig_h1").fill_null(False)).join(players, on="nfl_id")
    selection = wr.group_by("elig_h1").agg(pl.len().alias("n"), pl.col("forty").mean().alias("mean_forty"), pl.col("forty").std().alias("sd_forty"),
                                           pl.col("x_peak").mean().alias("mean_peak"), pl.col("draft_round").cast(pl.Float64).mean().alias("mean_round"),
                                           pl.col("draft_round").is_null().mean().alias("share_undrafted")).sort("elig_h1").to_dicts()

    result = dict(run=run, code_commit=git("rev-parse", "HEAD"), primary_run=PRIMARY.name, join_run=JOIN.name, seeds=SEEDS, B=B,
                  primary=json.load(open(PRIMARY / "h1_wr_result.json"))["primary"],
                  registered=res, R5_leave_one_team_out=loto, R6_ceiling=ceiling, R7_spline=dict(**spline, cv=cv, knots_raw=knots.tolist()),
                  R14_selection=selection, N1_permutation=perm, diag_leave_one_team_season_out=lotso, wald=wald,
                  R4_post_plays=dict(plays=F["R4_post_only_plays"].height, players=F["R4_post_only_plays"]["nfl_id"].n_unique()),
                  seconds=time.time() - t0)
    json.dump(result, open(out / "robustness.json", "w"), indent=1, default=float)
    (OUTROOT / "LATEST").write_text(run)
    print("->", out, round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
