"""H2: secondary, ESTIMATION-FOCUSED analysis (D4). Does combine tracked peak speed add information about WR deep-route
separation beyond the official 40?  Registered model, variables, sample and analyses (preregistration §2-§5, §10, §12,
§13; spec §2) are unchanged; their decision criteria are evaluated and reported DESCRIPTIVELY (no confirmatory claim).

Declared before the run:
  data       : the single validated join 20261121T135032Z, h2_WR.parquet (57 WRs; deep = GO/POST/CORNER/WHEEL,
               short = HITCH/SLANT/OUT/FLAT/SCREEN/ANGLE; outcome separation_at_pass_forward; thrown passes)
  predictors : F = official 40 sign-reversed (higher = faster); x = tracked 40 peak speed (max over valid attempts);
               M3 reference only: official 10-yd split, sign-reversed (combine_results)
  model      : s_ij = mu + gamma'w_ij + kappa nfl_year + beta_F F_i + beta_P x_i + b_i + tau_team-season + eps (REML),
               w = route_ran, team_coverage_type, down, ytg_bin, offense_formation, in_motion_at_ball_snap, ttt_bin, season
  CI         : the registered "player-cluster bootstrap CI (B = 2000, percentile)" is taken as the bootstrap of the REML fit
               (duplicated players distinct, team-season shared); the Phase-4-validated two-stage WLS bootstrap (B = 2000)
               and the Wald SE are reported as checks
  CV         : held-out PLAYERS only. Registered criterion uses the Phase-4-validated frozen h2_cv (10-fold x 20) and its
               player bootstrap (B = 500) lower bound; the extended stratified CV (M0/M1/M2/M2s/M3, RMSE, Spearman, LPD)
               and leave-one-player-out are reported alongside
  ME grid    : EIV regression calibration at R_F {0.85, 0.90, 0.95, 0.99} x R_x {0.94, 0.987} + tipping-point R_F
  N3         : same model on short routes; beta_P^deep - beta_P^short (descriptive)
  seeds      : SEEDS below
The run happens once (refuses a second run and uncommitted code). `--dry-run DIR` replaces separation by synthetic
noise on 15 players with small B, to test code paths only.
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
from scipy import stats  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nfl_bdb.models import confirmatory as cf  # noqa: E402
from nfl_bdb.models import h2_extensions as h2  # noqa: E402

JOIN = ROOT / "data/interim/confirmatory_join/20261121T135032Z"
OUTROOT = ROOT / "experiments/h2_estimation"
SEEDS = dict(two_stage_boot=7001, reml_boot=[7101, 7102, 7103, 7104], cv=7201, cv_boot=7202, cv_ext=7203, eiv_boot=7301)
B = 2000; B_CV = 500; SESOI_PARTIAL = 0.10; SESOI_DR2 = 0.02


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def load(dry=False):
    df = pl.read_parquet(JOIN / "h2_WR.parquet")
    cr = pl.read_parquet(ROOT / "data/interim/combine_results.parquet").select("nfl_id", "ten_yd_split")
    if dry:
        keep = sorted(df["nfl_id"].unique().to_list())[:15]; df = df.filter(pl.col("nfl_id").is_in(keep))
        rng = np.random.default_rng(1)
        df = df.with_columns(pl.Series("separation_at_pass_forward", 3 + rng.standard_normal(df.height)))
    ids = sorted(df["nfl_id"].unique().to_list())
    pp = df.group_by("nfl_id").agg(pl.col("forty").first(), pl.col("x_peak").first(), pl.col("draft_year").first()).join(cr, on="nfl_id", how="left")
    pp = pl.DataFrame({"nfl_id": ids}).join(pp, on="nfl_id", how="left")
    F = -pp["forty"].to_numpy().astype(float); x = pp["x_peak"].to_numpy().astype(float)
    ten = -pp["ten_yd_split"].to_numpy().astype(float); dc = pp["draft_year"].to_numpy()
    out = {}
    for depth in ("deep", "short"):
        d = h2.index(df.filter(pl.col("route_depth") == depth), ids)
        out[depth] = dict(df=d, pid=d["pid"].to_numpy(), team=d["team_i"].to_numpy(), y=d["separation_at_pass_forward"].to_numpy().astype(float),
                          W=h2.design(d), season=d["season"].to_numpy())
    return ids, F, x, ten, dc, out


def boot_chunk(args):
    seed, b, dry = args
    ids, F, x, ten, dc, A = load(dry)
    strip = lambda a: {k: a[k] for k in ("pid", "team", "y", "W")}  # noqa: E731
    return h2.reml_bootstrap(strip(A["deep"]), strip(A["short"]), F, x, b, seed)


def pct(v, lev=0.95):
    v = v[np.isfinite(v)]; a = (1 - lev) / 2
    return [float(np.percentile(v, 100 * a)), float(np.percentile(v, 100 * (1 - a)))]


def main(dry_run=None):
    dry = dry_run is not None
    if not dry:
        if git("status", "--porcelain", "--", "src", "scripts", "tests"):
            raise SystemExit("refusing to run from uncommitted code")
        if OUTROOT.exists() and any(p.name != "LATEST" for p in OUTROOT.iterdir()):
            raise SystemExit("an H2 estimation run already exists; the registered analysis is run once")
    b_main = 40 if dry else B; b_cv = 10 if dry else B_CV; reps = 2 if dry else 20
    t0 = time.time()
    ids, F, x, ten, dc, A = load(dry)
    P = len(ids); D, Sh = A["deep"], A["short"]
    print(f"H2: {P} WRs; deep {len(D['y'])} plays; short {len(Sh['y'])} plays; W columns {D['W'].shape[1]}", flush=True)

    # ---- model estimates (REML; frozen h2_reml + true-scale quantities) ----
    deep = h2.fit(D["pid"], D["team"], D["y"], D["W"], F, x)
    short = h2.fit(Sh["pid"], Sh["team"], Sh["y"], Sh["W"], F, x)
    z = deep["beta_P"] / deep["se_wald"]
    wald = dict(z=float(z), p_normal=float(2 * stats.norm.sf(abs(z))), p_t_df=float(2 * stats.t.sf(abs(z), P - 3)), df=P - 3,
                ci95=[deep["beta_P"] - 1.96 * deep["se_wald"], deep["beta_P"] + 1.96 * deep["se_wald"]])
    # two-stage equivalent (frozen; Phase-4 validated) and its bootstrap
    r = cf.residualise_np(D["W"], D["y"]); m, n, sw2 = cf.player_stats(D["pid"], r, P)
    b2, se2, s2b2 = cf.wls_two_stage(m, n, sw2, F, x)
    bt2 = cf.h2_bootstrap(m, n, sw2, F, x, b_main, np.random.default_rng(SEEDS["two_stage_boot"]))
    reliability = float(np.mean(deep["s2b"] / (deep["s2b"] + deep["s2"] / n)))

    # ---- REML player-cluster bootstrap (registered CI), parallel chunks with declared seeds ----
    chunks = [(s, b_main // 4, dry) for s in SEEDS["reml_boot"]]
    with ProcessPoolExecutor(4, mp_context=mp.get_context("spawn")) as ex:
        parts = list(ex.map(boot_chunk, chunks))
    BS = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    contrast = BS["deep_beta_P"] - BS["short_beta_P"]
    reml_ci = {k: dict(ci95=pct(v), ci90=pct(v, 0.90), se=float(np.nanstd(v)), n_ok=int(np.isfinite(v).sum())) for k, v in BS.items()}
    p_boot = cf.boot_p(BS["deep_beta_P"][np.isfinite(BS["deep_beta_P"])])

    # ---- measurement error ----
    grid = h2.eiv_grid(m, n, sw2, F, x)
    tips = {str(rx): h2.tipping_point(m, n, sw2, F, x, rx) for rx in (0.94, 0.987)}
    rng = np.random.default_rng(SEEDS["eiv_boot"]); eb = []
    for _ in range(b_main):
        i = rng.integers(0, P, P)
        try:
            eb.append(cf.eiv_two_stage(m[i], n[i], sw2, F[i], x[i], rel_F=0.95, rel_x=0.987)[1])
        except np.linalg.LinAlgError:
            pass
    eiv_reg = dict(beta_P=float(cf.eiv_two_stage(m, n, sw2, F, x, rel_F=0.95, rel_x=0.987)[1]), ci95=pct(np.array(eb)))
    validity_obs = float(np.sqrt(deep["R2_true_F"]))          # corr(true level, observed F)
    art = [dict(rel_F=rf, a=a, spurious_partial=h2.precision_artefact(deep["r_F_x"], rf, rx, a), rel_x=rx)
           for rx in (0.94, 0.987) for rf in (0.80, 0.85, 0.90, 0.95, 0.99) for a in (0.3, 0.6, min(validity_obs / np.sqrt(rf), 0.99))]

    # ---- prediction on held-out players ----
    S = cf.player_sufficient(D["pid"], D["W"], D["y"], P)
    cv = cf.h2_cv(S, F, x, np.random.default_rng(SEEDS["cv"]), 10, reps)
    lb90, cvb = cf.h2_cv_bootstrap(S, F, x, np.random.default_rng(SEEDS["cv_boot"]), B=b_cv, folds=10, repeats=2)
    knots = np.quantile(pl.read_parquet(JOIN / "predictors.parquet").filter((pl.col("pos") == "WR") & pl.col("x_peak").is_not_null())["x_peak"].to_numpy(),
                        [0, 1 / 3, 2 / 3, 1])
    ten_ok = np.isfinite(ten)
    ten_f = np.where(ten_ok, ten, np.nanmean(ten))   # M3 reference only; missing splits set to the mean (reported)
    cv_ext = h2.cv_extended(S, F, x, ten_f, dc, knots, np.random.default_rng(SEEDS["cv_ext"]), 10, reps)
    loo = h2.lopo(S, F, x, ten_f, dc, knots)
    sf = h2.season_forward(D["pid"], D["W"], D["y"], D["season"], F, x)

    # ---- registered decision criteria, evaluated DESCRIPTIVELY (D4) ----
    ci_bp = reml_ci["deep_beta_P"]["ci95"]
    crit = dict(beta_P_positive=bool(deep["beta_P"] > 0), ci95_excludes_0=bool(ci_bp[0] > 0),
                dR2_CV_ge_0_02=bool(cv["dr2"] >= SESOI_DR2), dR2_CV_lb90_gt_0=bool(lb90 > 0),
                season_forward_dRMSE_le_0=bool(np.isfinite(sf.get("dRMSE", np.nan)) and sf["dRMSE"] <= 0),
                eiv_beta_P_positive_at_RF_0_95=bool(eiv_reg["beta_P"] > 0),
                partial_ci90_entirely_below_0_10=bool(reml_ci["deep_partial"]["ci90"][1] < SESOI_PARTIAL))
    crit["registered_supported_pattern"] = all(crit[k] for k in ("beta_P_positive", "ci95_excludes_0", "dR2_CV_ge_0_02", "dR2_CV_lb90_gt_0",
                                                                 "season_forward_dRMSE_le_0", "eiv_beta_P_positive_at_RF_0_95"))
    crit["registered_falsified_pattern"] = crit["partial_ci90_entirely_below_0_10"]
    crit["label"] = ("criteria pattern 'supported' (estimation only, not confirmatory)" if crit["registered_supported_pattern"]
                     else "criteria pattern 'falsified' (partial < SESOI)" if crit["registered_falsified_pattern"] else "criteria pattern 'inconclusive'")

    result = dict(dry_run=dry, code_commit=git("rev-parse", "HEAD"), join_run=JOIN.name, seeds=SEEDS, B=b_main, B_cv=b_cv,
                  sample=dict(players=P, plays_deep=len(D["y"]), plays_short=len(Sh["y"]), team_seasons_deep=int(D["team"].max() + 1),
                              deep_plays_per_player=dict(min=int(n.min()), median=float(np.median(n)), max=int(n.max())),
                              ten_yd_split_missing=int((~ten_ok).sum()), r_F_x=deep["r_F_x"],
                              seasons=D["df"].group_by("season").agg(pl.len().alias("plays"), pl.col("nfl_id").n_unique().alias("players")).sort("season").to_dicts()),
                  deep=deep, short=short, wald=wald, two_stage=dict(beta_P=float(b2[2]), se_hc3=float(se2[2]), ci95_boot=list(bt2["ci"]), p_boot=bt2["p"], se_boot=bt2["se"]),
                  reml_bootstrap=reml_ci, p_boot_reml=p_boot, contrast_N3=dict(estimate=deep["beta_P"] - short["beta_P"], ci95=pct(contrast), ci90=pct(contrast, 0.90),
                                                                                   se=float(np.nanstd(contrast))),
                  reliability_deep_level=reliability, eiv_registered=eiv_reg, eiv_grid=grid, eiv_tipping_RF=tips, validity_obs=validity_obs,
                  precision_artefact=art, cv_frozen=dict(**cv, lb90=lb90, boot_mean=float(np.mean(cvb)), boot_sd=float(np.std(cvb))),
                  cv_extended=cv_ext, cv_lopo=loo, season_forward=sf, criteria=crit, seconds=time.time() - t0)
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = (Path(dry_run) if dry else OUTROOT) / run; out.mkdir(parents=True)
    np.savez(out / "bootstraps.npz", **BS, two_stage=bt2["boot"], cv_boot=cvb, eiv_boot=np.array(eb))
    json.dump(result, open(out / "h2_result.json", "w"), indent=1, default=float)
    if not dry:
        (OUTROOT / "LATEST").write_text(run)
    print("->", out, round(time.time() - t0), "s")


if __name__ == "__main__":
    main(sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--dry-run" else None)
