"""THE confirmatory H1-WR analysis (sole primary hypothesis; preregistration §2, §6, §8–§12; deviations D1–D4).

Registered, frozen ingredients only:
  data      : the single validated join, data/interim/confirmatory_join/20261121T135032Z/h1_WR.parquet
              (57 WRs; deep = GO/POST/CORNER/WHEEL, short = HITCH/SLANT/OUT/FLAT/SCREEN/ANGLE; y = vmax_prepass)
  predictor : x = tracked 40 peak speed (max over valid attempts), standardised in-sample by h1_reml
  model     : y ~ 0 + ctx + ctx:(route_ran + team_coverage_type + down + ytg_bin + offense_formation + ttt_bin + season
              + nfl_year) + (0 + ctx | player) + (1 | team_season), varIdent(ctx)   [confirmatory.design_h1 / h1_reml]
  inference : confirmatory.h1_registered_test = REML + full REML player-cluster percentile bootstrap, B = 2000 (D1)
  decision  : supported  iff Delta_hat > 0, the 95 % CI excludes 0, and the 2025 season-forward estimate has the same sign
              falsified  iff 90 % CI upper bound < 0.15 (SESOI) or the 95 % CI lies entirely below 0
              otherwise inconclusive ("compatible with Delta from L to U")
Seed (declared before the run): bootstrap seed = 4004 (project base seed). The script runs ONCE: it refuses to run if a
previous confirmatory run exists or if src/, scripts/ or tests/ have uncommitted changes.

Registered accompanying reports (no influence on the decision): 90 % CI; BCa interval (jackknife over players, §10);
moment-estimator cross-check (spec §1.2); disattenuated rho with R_x 0.987 (registered) and 0.94 (within-WR, D3);
raw slopes per 0.25 yd/s; Bayesian sensitivity with skeptical prior Delta ~ N(0, 0.15^2) (§12.5).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nfl_bdb.data.play_table import H1_COVARIATES  # noqa: E402
from nfl_bdb.models import confirmatory as cf  # noqa: E402

JOIN = ROOT / "data/interim/confirmatory_join/20261121T135032Z/h1_WR.parquet"
OUTROOT = ROOT / "experiments/h1_wr_confirmatory"
SEED = 4004
B = cf.H1_B_REGISTERED          # 2000
ALPHA = 0.05
SESOI = 0.15
R_X = {"registered_pooled": 0.987, "within_WR_D3": 0.94}
COVS = H1_COVARIATES["WR"]


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def prepare(df: pl.DataFrame):
    """Index players / team-seasons / contexts exactly as the validated Phase 4 skeleton did."""
    df = df.with_columns(pl.when(pl.col("ctx") == "deep").then(0).otherwise(1).alias("ctx_i"),
                         (pl.col("team_abbr") + "_" + pl.col("season").cast(pl.Utf8)).alias("team_season"))
    ids = sorted(df["nfl_id"].unique().to_list()); pmap = {k: i for i, k in enumerate(ids)}
    ts = sorted(df["team_season"].unique().to_list()); tmap = {k: i for i, k in enumerate(ts)}
    df = df.with_columns(pl.col("nfl_id").replace_strict(pmap).alias("pid"), pl.col("team_season").replace_strict(tmap).alias("team_i"))
    df = df.sort("pid", "ctx_i", "game_id", "play_id")
    xp = df.group_by("pid").agg(pl.col("x_peak").first()).sort("pid")["x_peak"].to_numpy()
    return df, xp


def arrays(df):
    return df["pid"].to_numpy(), df["ctx_i"].to_numpy(), df["team_i"].to_numpy(), df["y"].to_numpy().astype(float)


def season_forward(df, xp):
    """Validated Phase 4 rule: REML H1 on the 2025 season only, players with >= 20 plays in each context (>= 15 players)."""
    d25 = df.filter(pl.col("season") == 2025)
    cnt = d25.group_by("pid", "ctx_i").len().pivot(index="pid", on="ctx_i", values="len").fill_null(0)
    okp = cnt.filter((pl.col("0") >= 20) & (pl.col("1") >= 20))["pid"].sort().to_list()
    d25 = d25.filter(pl.col("pid").is_in(okp))
    pm = {k: i for i, k in enumerate(okp)}
    tt = sorted(d25["team_i"].unique().to_list()); tm = {k: i for i, k in enumerate(tt)}
    d25 = d25.with_columns(pl.col("pid").replace_strict(pm).alias("p2"), pl.col("team_i").replace_strict(tm).alias("t2"))
    r = cf.h1_reml(d25["p2"].to_numpy(), d25["ctx_i"].to_numpy(), d25["t2"].to_numpy(), d25["y"].to_numpy().astype(float),
                   cf.design_h1(d25, COVS, 2), xp[okp])
    return dict(delta_2025=r.delta, rho_2025=r.rho.tolist(), n_players_2025=len(okp), n_plays_2025=d25.height, converged=r.converged)


def bca(delta, boot, jack):
    z0 = stats.norm.ppf((boot < delta).mean())
    jm = jack.mean(); a = np.sum((jm - jack) ** 3) / (6 * np.sum((jm - jack) ** 2) ** 1.5)
    out = {}
    for lev in (0.95, 0.90):
        zl, zu = stats.norm.ppf([(1 - lev) / 2, 1 - (1 - lev) / 2])
        q = [stats.norm.cdf(z0 + (z0 + zz) / (1 - a * (z0 + zz))) for zz in (zl, zu)]
        out[str(lev)] = [float(np.quantile(boot, q[0])), float(np.quantile(boot, q[1]))]
    return out, float(z0), float(a)


def main(dry_run: str | None = None):
    """dry_run: a directory. Replaces the REAL outcome by synthetic noise (no outcome is read into the model), keeps
    15 players, and writes there. Exercises every code path of the confirmatory run without touching real results."""
    if dry_run is None:
        if git("status", "--porcelain", "--", "src", "scripts", "tests"):
            raise SystemExit("refusing to run the confirmatory analysis from uncommitted code")
        if OUTROOT.exists() and any(p.name != "LATEST" for p in OUTROOT.iterdir()):
            raise SystemExit("a confirmatory H1-WR run already exists; the registered analysis is run once")
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = (Path(dry_run) if dry_run else OUTROOT) / run
    commit = git("rev-parse", "HEAD")
    t0 = time.time()
    raw = pl.read_parquet(JOIN)
    if dry_run:
        keep = sorted(raw["nfl_id"].unique().to_list())[:15]
        raw = raw.filter(pl.col("nfl_id").is_in(keep))
        rng = np.random.default_rng(1)
        raw = raw.with_columns(pl.Series("y", 6.0 + (raw["ctx"] == "deep").to_numpy() + rng.standard_normal(raw.height)))
    df, xp = prepare(raw)
    player, ctx, team, y = arrays(df)
    Xw = cf.design_h1(df, COVS, 2)
    print(f"design: {df.height} plays, {len(xp)} players, {team.max() + 1} team-seasons, {Xw.shape[1]} fixed-effect columns", flush=True)

    # ---------------- primary: registered test (D1) ----------------
    res = cf.h1_registered_test(player, ctx, team, y, Xw, xp, seed=SEED, B=B, alpha=ALPHA)
    boot = res.pop("boot")
    lo90, hi90 = np.percentile(boot, [5, 95])
    sf = season_forward(df, xp)
    supported = bool(res["supported"] and np.sign(sf["delta_2025"]) == np.sign(res["delta"]))
    falsified = bool(hi90 < SESOI or res["ci_hi"] < 0)
    decision = "SUPPORTED" if supported else ("FALSIFIED" if falsified else "INCONCLUSIVE")
    t_primary = time.time() - t0

    # ---------------- registered accompanying reports ----------------
    reml = cf.h1_reml(player, ctx, team, y, Xw, xp)          # same deterministic fit (diagnostics)
    jack = np.array([cf.h1_reml(*_drop(player, ctx, team, y, Xw, xp, i)).delta for i in range(len(xp))])
    bca_ci, z0, acc = bca(res["delta"], boot, jack)
    Wres = cf.full_rank(cf.one_hot(df, COVS))   # as the validated Phase 4 cross-check (sv._design)
    r = cf.residualise_np(Wres, y)
    m, n, sw2 = cf.player_context_stats(player, ctx, r, len(xp))
    mrho, mraw = cf.moment_rho(xp, m, n, sw2)
    sd_x = float(np.std(xp, ddof=1))
    tau2, se2 = SESOI ** 2, res["se_boot"] ** 2
    post_m = res["delta"] * tau2 / (tau2 + se2); post_sd = np.sqrt(tau2 * se2 / (tau2 + se2))
    cnt = df.group_by("ctx").agg(pl.len().alias("plays"), pl.col("nfl_id").n_unique().alias("players"))
    per_player = df.group_by("pid", "ctx").len().group_by("ctx").agg(pl.col("len").min().alias("min"), pl.col("len").median().alias("median"),
                                                                    pl.col("len").max().alias("max"))
    tsz = df.group_by("team_i").agg(pl.col("pid").n_unique().alias("players"))
    result = dict(
        run=run, code_commit=commit, join_run="20261121T135032Z", seed=SEED, B=B, alpha=ALPHA, sesoi=SESOI,
        decision=decision,
        primary=dict(delta=res["delta"], rho_deep=float(res["rho"][0]), rho_short=float(res["rho"][1]),
                     ci95_percentile=[res["ci_lo"], res["ci_hi"]], ci90_percentile=[float(lo90), float(hi90)],
                     se_boot=res["se_boot"], p_two_sided=res["p"],
                     ci_excludes_0_positive=bool(res["ci_lo"] > 0), delta_positive=bool(res["delta"] > 0),
                     season_forward=sf, season_forward_same_sign=bool(np.sign(sf["delta_2025"]) == np.sign(res["delta"])),
                     falsification=dict(ci90_upper_below_sesoi=bool(hi90 < SESOI), ci95_entirely_below_0=bool(res["ci_hi"] < 0)),
                     largest_delta_excluded_above=float(res["ci_hi"])),
        bootstrap=dict(n_ok=res["n_ok"], n_failed=B - res["n_ok"], quantiles={str(q): float(np.percentile(boot, q)) for q in (0.5, 2.5, 5, 25, 50, 75, 95, 97.5, 99.5)},
                       mean=float(boot.mean()), sd=float(boot.std()), median_minus_estimate=float(np.median(boot) - res["delta"]),
                       share_le_0=float((boot <= 0).mean())),
        bca=dict(ci=bca_ci, z0=z0, acceleration=acc, jackknife_sd=float(jack.std(ddof=0) * np.sqrt(len(jack) - 1)), jackknife_range=[float(jack.min()), float(jack.max())]),
        diagnostics=dict(converged=bool(reml.converged), sigma_b=reml.sigma_b.tolist(),
                         corr_b=float(reml.sigma_b[0, 1] / np.sqrt(reml.sigma_b[0, 0] * reml.sigma_b[1, 1])),
                         s2_team=float(reml.s2_team), s2_resid=[float(v) for v in reml.extra["s2_resid"]],
                         beta_std=[float(b) for b in reml.beta], fixed_effect_columns=int(Xw.shape[1]),
                         team_seasons=int(team.max() + 1), team_seasons_single_player=int((tsz["players"] == 1).sum()),
                         reliability_player_context_mean=[float(np.mean(reml.sigma_b[c, c] / (reml.sigma_b[c, c] + reml.extra["s2_resid"][c] / n[:, c]))) for c in (0, 1)]),
        sample=dict(players=len(xp), plays=df.height, by_context=cnt.sort("ctx").to_dicts(), plays_per_player_context=per_player.sort("ctx").to_dicts(),
                    seasons=df.group_by("season").agg(pl.len().alias("plays"), pl.col("nfl_id").n_unique().alias("players")).sort("season").to_dicts(),
                    x_peak_sd_sample=sd_x, x_peak_mean_sample=float(np.mean(xp))),
        effect_size=dict(raw_slope_per_0_25_yds=[float(b * 0.25 / sd_x) for b in reml.beta],
                         disattenuated={k: dict(rho_deep=float(res["rho"][0] / np.sqrt(v)), rho_short=float(res["rho"][1] / np.sqrt(v)),
                                                delta=float(res["delta"] / np.sqrt(v))) for k, v in R_X.items()}),
        cross_check_moment=dict(rho=mrho.tolist(), delta=float(mrho[0] - mrho[1]), raw_rho=mraw.tolist(),
                                disagrees_by_more_than_half_se=bool(abs(mrho[0] - mrho[1] - res["delta"]) > 0.5 * res["se_boot"]),
                                note="registered cross-check (spec §1.2); never used for decisions (D1)"),
        bayes_sensitivity=dict(prior="Delta ~ N(0, 0.15^2)", likelihood="normal, SE = bootstrap SE", posterior_mean=float(post_m), posterior_sd=float(post_sd),
                               p_delta_gt_0=float(1 - stats.norm.cdf(0, post_m, post_sd)), p_delta_gt_sesoi=float(1 - stats.norm.cdf(SESOI, post_m, post_sd))),
        seconds=dict(primary=t_primary, total=time.time() - t0),
    )
    out.mkdir(parents=True)
    np.save(out / "bootstrap_delta.npy", boot); np.save(out / "jackknife_delta.npy", jack)
    json.dump(result, open(out / "h1_wr_result.json", "w"), indent=1, default=float)
    if not dry_run:
        (OUTROOT / "LATEST").write_text(run)
    print(json.dumps({k: result[k] for k in ("decision", "primary")}, indent=1, default=float)); print("->", out)


def _drop(player, ctx, team, y, Xw, xp, i):
    k = player != i
    p2 = player[k]; p2 = np.where(p2 > i, p2 - 1, p2)
    _, t2 = np.unique(team[k], return_inverse=True)
    X2 = Xw[k]; X2 = cf.full_rank(X2[:, np.abs(X2).sum(0) > 0])
    return p2, ctx[k], t2, y[k], X2, np.delete(xp, i)


if __name__ == "__main__":
    main(sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--dry-run" else None)
