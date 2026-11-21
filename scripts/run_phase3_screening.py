"""Phase 3: NFL performance-linkage *discovery* (outcome inventory, temporal matching, opportunity
adjustment, outcome-blind feasibility screening).

Design rules enforced here
  * Outcomes are REGULAR-SEASON only (competition: "regular-season NFL game performance").
    POST/PRE rows are counted in the inventory but never used as outcomes.
  * player_career_successes is NOT read.
  * Outcome-BLIND screening: no combine-measure x game-outcome association is computed.
    We compute (i) outcome availability, (ii) opportunity counts, (iii) outcome reliability
    (game-parity split-half, season-to-season), (iv) predictor-side structure (combine measures
    among themselves), (v) power / minimum detectable effects. Hypotheses are therefore
    specified before any linkage is seen, and the later tests can be confirmatory.
  * Unit of inference = player. Tracking exclusions as in CLAUDE.md.

Stages
  features : per player-play tracking features (REG), one season at a time
             -> data/interim/phase3_play_features.parquet, data/interim/phase3_matchups.parquet
  analyse  : all tables -> experiments/phase3_screening/<run_id>/

Usage:  python scripts/run_phase3_screening.py features
        python scripts/run_phase3_screening.py analyse
"""
from __future__ import annotations

import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")
from nfl_bdb.data.game_kinematics import load_game_sequences  # noqa: E402
from nfl_bdb.data.io import INTERIM, load  # noqa: E402

CFG = dict(season_types=["REG"], seed=11, n_boot=1000, min_opp=100, min_opp_season=40,
           burst_times=[1.0, 1.5, 2.0], alpha=0.05, power=0.80,
           deep_routes=["GO", "POST", "CORNER", "WHEEL"],
           short_routes=["SLANT", "HITCH", "OUT", "IN", "FLAT", "ANGLE", "SCREEN"])
POS = ["WR", "TE", "OL", "DL", "DB"]
FEAT = INTERIM / "phase3_play_features.parquet"
MATCH = INTERIM / "phase3_matchups.parquet"
FIELD_W = 160 / 3


# ----------------------------------------------------------------------------------------------
# Stage 1: tracking features per player-play
# ----------------------------------------------------------------------------------------------
def features():
    pp = load("player_play").select("game_id", "play_id", "nfl_id", "team_abbr", "possession_team",
                                    "play_direction", "pass_result").collect()
    out, matches, reps = [], [], {}
    for yr in (2023, 2024, 2025):
        df, rep = load_game_sequences(seasons=(yr,), season_types=("REG",),
                                      cols=["game_id", "play_id", "nfl_id", "time", "x", "y", "s", "event"])
        reps[yr] = rep
        snap = df.filter(pl.col("event") == "ball_snap").group_by("seq").agg(pl.col("time").min().alias("t_snap"))
        pf = (df.filter(pl.col("event").is_in(["pass_forward", "pass_shovel"])).group_by("seq")
              .agg(pl.col("time").min().alias("t_pf")))
        df = (df.join(snap, on="seq").join(pf, on="seq", how="left")
              .join(pp, on=["game_id", "play_id", "nfl_id"], how="left")
              .with_columns(
                  ((pl.col("time") - pl.col("t_snap")).dt.total_milliseconds() / 100).round().cast(pl.Int32).alias("k"),
                  ((pl.col("t_pf") - pl.col("t_snap")).dt.total_milliseconds() / 100).round().cast(pl.Int32).alias("k_pf"),
                  pl.when(pl.col("play_direction") == "left").then(120 - pl.col("x")).otherwise(pl.col("x")).alias("xn"),
                  pl.when(pl.col("play_direction") == "left").then(FIELD_W - pl.col("y")).otherwise(pl.col("y")).alias("yn"),
                  pl.when(pl.col("team_abbr") == pl.col("possession_team")).then(1).otherwise(-1).alias("side"))
              .filter(pl.col("k") >= 0)
              .sort("seq", "k"))
        df = df.with_columns(
            (pl.col("xn").diff().pow(2) + pl.col("yn").diff().pow(2)).sqrt().over("seq").fill_null(0).alias("step"))

        def at(col, kk):
            return pl.col(col).filter(pl.col("k") == kk).first()
        agg = df.group_by("seq").agg(
            pl.col("game_id").first(), pl.col("play_id").first(), pl.col("nfl_id").first(),
            pl.col("side").first(), pl.col("k_pf").first(), pl.col("k").max().alias("k_end"),
            pl.col("s").max().alias("vmax_play"),
            pl.col("s").filter(pl.col("k") <= pl.col("k_pf")).max().alias("vmax_prepass"),
            pl.col("s").filter(pl.col("k") == pl.col("k_pf")).first().alias("s_pf"),
            at("xn", 0).alias("x0"), at("yn", 0).alias("y0"), at("s", 0).alias("s0"),
            *[at("xn", int(t * 10)).alias(f"x{int(t*10)}") for t in CFG["burst_times"]],
            *[at("yn", int(t * 10)).alias(f"y{int(t*10)}") for t in CFG["burst_times"]],
            *[at("s", int(t * 10)).alias(f"s{int(t*10)}") for t in CFG["burst_times"]],
            pl.col("step").filter((pl.col("k") >= 1) & (pl.col("k") <= 20)).sum().alias("path_2s"),
            # first time (s) speed reaches 4 yd/s after the snap (burst latency)
            (pl.col("k").filter(pl.col("s") >= 4.0).min() / 10).alias("t_to_4"),
        )
        agg = agg.with_columns(
            *[(pl.col(f"x{int(t*10)}") - pl.col("x0")).mul(pl.col("side")).alias(f"fwd_{int(t*10)}")
              for t in CFG["burst_times"]],
            *[(pl.col(f"y{int(t*10)}") - pl.col("y0")).abs().alias(f"lat_{int(t*10)}") for t in CFG["burst_times"]],
            *[((pl.col(f"x{int(t*10)}") - pl.col("x0")) ** 2 + (pl.col(f"y{int(t*10)}") - pl.col("y0")) ** 2).sqrt()
              .alias(f"disp_{int(t*10)}") for t in CFG["burst_times"]],
            pl.lit(yr).alias("season"),
        ).drop([c for c in agg.columns if c[0] in "xy" and c[1:].isdigit()])
        out.append(agg)
        # cohort matchups at pass_forward: offence (side +1) vs defence (side -1) on the same play
        at_pf = (df.filter(pl.col("k") == pl.col("k_pf"))
                 .select("game_id", "play_id", "nfl_id", "side", "xn", "yn"))
        o = at_pf.filter(pl.col("side") == 1); d = at_pf.filter(pl.col("side") == -1)
        m = o.join(d, on=["game_id", "play_id"], suffix="_d").with_columns(
            ((pl.col("xn") - pl.col("xn_d")) ** 2 + (pl.col("yn") - pl.col("yn_d")) ** 2).sqrt().alias("dist"))
        matches.append(m.select("game_id", "play_id", "nfl_id", "nfl_id_d", "dist").with_columns(pl.lit(yr).alias("season")))
        print(yr, rep, agg.height, m.height, flush=True)
        del df
    pl.concat(out).write_parquet(FEAT)
    pl.concat(matches).write_parquet(MATCH)
    json.dump(reps, open(INTERIM / "phase3_feature_report.json", "w"), indent=1)


# ----------------------------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------------------------
def boot_ci(f, n, rng, B):
    vals = []
    for _ in range(B):
        idx = rng.integers(0, n, n)
        try:
            vals.append(f(idx))
        except Exception:  # noqa: BLE001
            pass
    vals = np.asarray(vals, float); vals = vals[np.isfinite(vals)]
    return (np.nan, np.nan) if len(vals) < 50 else tuple(np.percentile(vals, [2.5, 97.5]))


def mde_r(n, alpha=0.05, power=0.80):
    """Smallest |rho| detectable (two-sided) with Fisher z."""
    if n <= 4:
        return np.nan
    z = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
    return float(np.tanh(z / np.sqrt(n - 3)))


def residualise(df: pl.DataFrame, y: str, ctx: list[str]) -> pl.Series:
    """OLS residual of play-level outcome on one-hot context (pooled within position)."""
    d = df.select([y] + ctx).with_columns([pl.col(c).cast(pl.Utf8).fill_null("NA") for c in ctx])
    X = d.select(ctx).to_dummies(drop_first=True).to_numpy().astype(float)
    X = np.column_stack([np.ones(len(d)), X])
    yy = d[y].to_numpy().astype(float)
    beta, *_ = np.linalg.lstsq(X, yy, rcond=None)
    return pl.Series(f"{y}_adj", yy - X @ beta + yy.mean())


# ----------------------------------------------------------------------------------------------
# Stage 2: analysis
# ----------------------------------------------------------------------------------------------
def analyse():
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "experiments" / "phase3_screening" / run_id
    out.mkdir(parents=True, exist_ok=True)
    json.dump(CFG, open(out / "config.json", "w"), indent=1)
    rng = np.random.default_rng(CFG["seed"]); B = CFG["n_boot"]

    games = load("games", lazy=False)
    cr = load("combine_results", lazy=False)
    players = load("players", lazy=False)
    pp_all = (load("player_play", lazy=False)
              .join(games.select("game_id", "season", "season_type", "week"), on="game_id", how="left")
              .join(cr.select("nfl_id", pl.col("combine_position").alias("pos"), "draft_year"), on="nfl_id", how="left"))
    pp_all = pp_all.with_columns(
        (pl.col("pass_result").fill_null("") != "").alias("is_pass"),
        (pl.col("team_abbr") == pl.col("possession_team")).alias("is_off"))

    # ---------------- Task 1: inventory (non-null rates by position x season type) --------------
    outcome_cols = ["target", "rec_yards", "yards_after_catch", "expected_yards_after_catch", "route_ran",
                    "separation_at_pass_forward", "cushion", "dropback_duration", "pass_rushers_encountered",
                    "peak_pressure_probability_allowed", "pressure_allowed", "sack_allowed",
                    "time_to_pressure_allowed", "extended_sack_allowed", "player_get_off", "time_to_pressure",
                    "time_to_qb_hurry", "quick_pressure", "unblocked_pressure", "blitzing", "sack", "tackle",
                    "assist", "tackle_for_loss", "coverage_assignment", "coverage_assignment_at_snap",
                    "team_coverage_man_zone", "team_coverage_type", "offense_formation", "receiver_alignment",
                    "in_motion_at_ball_snap", "expected_points_added", "pass_length"]
    inv = (pp_all.group_by("pos", "season_type")
           .agg(pl.len().alias("rows"), pl.col("is_pass").mean().alias("pass_share"),
                *[pl.col(c).is_not_null().mean().alias(c) for c in outcome_cols]))
    inv.write_parquet(out / "inventory_nonnull.parquet")
    # conditional availability on the relevant opportunity set
    reg = pp_all.filter(pl.col("season_type") == "REG")
    cond = {}
    for p in POS:
        x = reg.filter(pl.col("pos") == p)
        xp = x.filter(pl.col("is_pass")); xr = x.filter(~pl.col("is_pass"))
        cond[p] = dict(
            rows=x.height, pass_rows=xp.height, run_rows=xr.height,
            route_on_pass=xp["route_ran"].is_not_null().mean(),
            sep_on_route=xp.filter(pl.col("route_ran").is_not_null())["separation_at_pass_forward"].is_not_null().mean() if p in ("WR", "TE") else None,
            sep_on_route_targeted=xp.filter(pl.col("target"))["separation_at_pass_forward"].is_not_null().mean() if p in ("WR", "TE") else None,
            sep_by_result={r: xp.filter((pl.col("pass_result") == r) & pl.col("route_ran").is_not_null())["separation_at_pass_forward"].is_not_null().mean() for r in ["C", "I", "IN", "S", "R"]} if p in ("WR", "TE") else None,
            getoff_on_pass=xp["player_get_off"].is_not_null().mean(),
            getoff_on_run=xr["player_get_off"].is_not_null().mean(),
            block_on_pass=xp["pass_rushers_encountered"].is_not_null().mean(),
            block_on_run=xr["pass_rushers_encountered"].is_not_null().mean(),
            cov_on_pass=xp["coverage_assignment"].is_not_null().mean(),
            cov_on_run=xr["coverage_assignment"].is_not_null().mean(),
            ttp_given_rush=x.filter(pl.col("player_get_off").is_not_null())["time_to_pressure"].is_not_null().mean(),
            ttp_without_getoff=int(x.filter(pl.col("player_get_off").is_null() & pl.col("time_to_pressure").is_not_null()).height),
            quickp_nonnull_iff_ttp=float((x["quick_pressure"].is_not_null() == x["time_to_pressure"].is_not_null()).mean()),
            pressure_allowed_rate=xp.filter(pl.col("pass_rushers_encountered").is_not_null())["pressure_allowed"].cast(pl.Float64).mean(),
            tackle_nonnull=x["tackle"].is_not_null().mean(), tackle_on_run=xr["tackle"].is_not_null().mean(),
            lined_up=x["lined_up_position"].value_counts(sort=True).head(6).to_dicts(),
        )
    json.dump(cond, open(out / "inventory_conditional.json", "w"), indent=1, default=str)

    # tracking linkage
    feat = pl.read_parquet(FEAT)
    regk = reg.join(feat.select("game_id", "play_id", "nfl_id", "k_pf", "k_end"), on=["game_id", "play_id", "nfl_id"], how="left")
    link = (regk.group_by("pos").agg(
        pl.len().alias("reg_rows"), pl.col("k_end").is_not_null().mean().alias("has_tracking_with_snap"),
        pl.col("k_pf").is_not_null().filter(pl.col("is_pass")).mean().alias("pass_forward_on_pass"),
        pl.col("k_pf").is_not_null().filter(pl.col("pass_result").is_in(["C", "I", "IN"])).mean().alias("pass_forward_on_attempt"),
        (pl.col("k_pf") / 10).filter(pl.col("is_pass")).median().alias("median_time_to_throw")))
    link.write_parquet(out / "tracking_linkage.parquet")

    # separation consistency check: cohort defender distance vs NGS separation at pass forward
    m = pl.read_parquet(MATCH).join(cr.select("nfl_id", pl.col("combine_position").alias("pos")), on="nfl_id") \
        .join(cr.select(pl.col("nfl_id").alias("nfl_id_d"), pl.col("combine_position").alias("pos_d")), on="nfl_id_d")
    nearest = m.group_by("game_id", "play_id", "nfl_id").agg(
        pl.col("dist").min().alias("d_min"), pl.col("pos").first(),
        pl.col("pos_d").sort_by("dist").first().alias("pos_d"), pl.len().alias("n_cohort_def"))
    nearest = nearest.join(reg.select("game_id", "play_id", "nfl_id", "separation_at_pass_forward", "route_ran", "target"),
                           on=["game_id", "play_id", "nfl_id"])
    rx = nearest.filter(pl.col("pos").is_in(["WR", "TE"]) & pl.col("separation_at_pass_forward").is_not_null())
    sep_check = dict(
        wr_te_route_plays_with_any_cohort_defender=rx.height,
        cohort_defender_within_3yd=int((rx["d_min"] < 3).sum()),
        cohort_def_is_nearest=int(((rx["d_min"] - rx["separation_at_pass_forward"]).abs() < 0.25).sum()),
        cohort_def_is_nearest_db=int(((rx["d_min"] - rx["separation_at_pass_forward"]).abs() < 0.25).filter(rx["pos_d"] == "DB").sum()),
        dmin_ge_sep_share=float((rx["d_min"] >= rx["separation_at_pass_forward"] - 0.25).mean()),
        median_abs_diff_when_close=float((rx["d_min"] - rx["separation_at_pass_forward"]).abs().filter(rx["d_min"] < 3).median()),
        distinct_wr_te=rx.filter((rx["d_min"] - rx["separation_at_pass_forward"]).abs() < 0.25)["nfl_id"].n_unique(),
    )
    json.dump(sep_check, open(out / "separation_consistency.json", "w"), indent=1)

    # ---------------- Task 2: temporal matching --------------------------------------------------
    att = pl.read_parquet(ROOT / "experiments" / "real_capacity" / (ROOT / "experiments/real_capacity/LATEST").read_text().strip()
                          / "combine_forty_attempts.parquet")
    tracked40 = att.filter(pl.col("r2") > 0.95).group_by("nfl_id").agg(
        pl.col("vpeak").max().alias("peak_speed"), pl.len().alias("n_40_attempts"))
    base = (cr.select("nfl_id", pl.col("combine_position").alias("pos"), "draft_year", "forty", "ten_yd_split",
                      "three_cone", "short_shuttle", "combine_weight", "vertical", "broad_jump")
            .join(players.select("nfl_id", "draft_round", "nfl_position"), on="nfl_id", how="left")
            .join(tracked40, on="nfl_id", how="left"))
    snaps = (pp_all.filter(pl.col("season_type") == "REG").group_by("nfl_id", "season")
             .agg(pl.len().alias("snaps"), pl.col("game_id").n_unique().alias("games")))
    leak = int(pp_all.filter(pl.col("season") < pl.col("draft_year")).height)
    seasons_obs = snaps.join(base.select("nfl_id", "draft_year"), on="nfl_id").with_columns(
        (pl.col("season") - pl.col("draft_year") + 1).alias("nfl_year"))
    seasons_obs.write_parquet(out / "player_season_snaps.parquet")
    tm = []
    for (dy, p), g in base.group_by("draft_year", "pos"):
        ids = g["nfl_id"]
        so = seasons_obs.filter(pl.col("nfl_id").is_in(ids))
        row = dict(draft_year=dy, pos=p, first_eligible_season=dy, post_combine_seasons_available=2025 - dy + 1,
                   combine_players=g.height, official_forty=int(g["forty"].is_not_null().sum()),
                   official_ten=int(g["ten_yd_split"].is_not_null().sum()),
                   tracked_40=int(g["peak_speed"].is_not_null().sum()),
                   tracked_40_and_forty=int((g["peak_speed"].is_not_null() & g["forty"].is_not_null()).sum()),
                   any_reg_snap=so["nfl_id"].n_unique(),
                   reg_snaps_total=int(so["snaps"].sum()))
        for s in (2023, 2024, 2025):
            row[f"players_{s}"] = so.filter(pl.col("season") == s)["nfl_id"].n_unique()
        tm.append(row)
    tm = pl.DataFrame(tm, infer_schema_length=None).sort("pos", "draft_year")
    tm.write_parquet(out / "temporal_matching.parquet")

    # ---------------- Task 3: opportunities ------------------------------------------------------
    r = reg.join(feat.select("game_id", "play_id", "nfl_id", "k_pf", "vmax_play", "vmax_prepass", "s_pf", "s10", "s15",
                             "fwd_10", "fwd_15", "lat_15", "disp_10", "disp_15", "path_2s", "t_to_4", "s0"),
                 on=["game_id", "play_id", "nfl_id"], how="left")
    r = r.with_columns(
        (pl.col("k_pf") / 10).alias("time_to_throw"),
        pl.when(pl.col("yards_to_go") <= 3).then(pl.lit("short")).when(pl.col("yards_to_go") <= 7).then(pl.lit("med")).otherwise(pl.lit("long")).alias("ytg_bin"),
        pl.col("time_to_pressure").is_not_null().cast(pl.Float64).alias("pressure_gen"),
        pl.col("pressure_allowed").cast(pl.Float64).alias("pressure_allowed_f"),
        pl.col("target").cast(pl.Float64).alias("target_f"),
        pl.when(pl.col("route_ran").is_in(CFG["deep_routes"])).then(pl.lit("deep"))
        .when(pl.col("route_ran").is_in(CFG["short_routes"])).then(pl.lit("short")).otherwise(pl.lit("other")).alias("route_depth"),
        pl.when(pl.col("coverage_assignment") == "MAN").then(pl.lit("man"))
        .when(pl.col("coverage_assignment").str.starts_with("DEEP") | pl.col("coverage_assignment").str.starts_with("QUARTERS"))
        .then(pl.lit("deep_zone")).when(pl.col("coverage_assignment") == "NO_ASSIGNMENT").then(pl.lit("no_assignment"))
        .when(pl.col("coverage_assignment").is_not_null()).then(pl.lit("under_zone")).alias("cov_role"),
    ).with_columns(
        pl.when(pl.col("time_to_throw").is_null()).then(pl.lit("NA"))
        .when(pl.col("time_to_throw") < 2.5).then(pl.lit("<2.5")).when(pl.col("time_to_throw") < 3.5).then(pl.lit("2.5-3.5"))
        .otherwise(pl.lit(">=3.5")).alias("ttt_bin"))
    opp_defs = {
        "route": (pl.col("pos").is_in(["WR", "TE"]) & pl.col("is_pass") & pl.col("route_ran").is_not_null()),
        "pass_rush": pl.col("player_get_off").is_not_null(),
        "pass_block": pl.col("pass_rushers_encountered").is_not_null(),
        "coverage": pl.col("coverage_assignment").is_not_null() & (pl.col("coverage_assignment") != "NO_ASSIGNMENT") & pl.col("is_pass"),
        "run_snap": ~pl.col("is_pass"),
    }
    r = r.with_columns([e.alias(f"opp_{k}") for k, e in opp_defs.items()])
    opp = r.group_by("nfl_id", "pos").agg(pl.len().alias("snaps"), pl.col("game_id").n_unique().alias("games"),
                                          *[pl.col(f"opp_{k}").sum().alias(k) for k in opp_defs])
    opp.write_parquet(out / "opportunities_player.parquet")
    opp_season = r.group_by("nfl_id", "pos", "season").agg(*[pl.col(f"opp_{k}").sum().alias(k) for k in opp_defs])
    opp_season.write_parquet(out / "opportunities_player_season.parquet")
    # context distributions within the main opportunity of each position
    ctx_tables = {}
    ctx_tables["WR_TE_route_by_depth"] = r.filter(pl.col("opp_route")).group_by("pos", "route_depth").len()
    ctx_tables["WR_TE_route_by_cov"] = r.filter(pl.col("opp_route")).group_by("pos", "team_coverage_man_zone").len()
    ctx_tables["rush_by_alignment"] = r.filter(pl.col("opp_pass_rush")).group_by("pos", "lined_up_position", "blitzing").len()
    ctx_tables["block_by_alignment"] = r.filter(pl.col("opp_pass_block")).group_by("pos", "lined_up_position").len()
    ctx_tables["cov_role"] = r.filter(pl.col("opp_coverage")).group_by("pos", "cov_role").len()
    ctx_tables["ttt_bin"] = r.filter(pl.col("is_pass")).group_by("pos", "ttt_bin").len()
    for k, v in ctx_tables.items():
        v.sort(v.columns[:-1]).write_parquet(out / f"context_{k}.parquet")

    # ---------------- Task 4 inputs: candidate outcomes, opportunity-adjusted, reliability --------
    # (outcome, position(s), opportunity filter, context covariates for adjustment)
    cands = [
        ("separation_at_pass_forward", ["WR", "TE"], "opp_route", ["route_ran", "team_coverage_type", "down", "ytg_bin", "offense_formation", "in_motion_at_ball_snap", "ttt_bin", "season"]),
        ("separation_deep", ["WR", "TE"], "opp_route", ["route_ran", "team_coverage_type", "down", "ytg_bin", "ttt_bin", "season"]),
        ("separation_short", ["WR", "TE"], "opp_route", ["route_ran", "team_coverage_type", "down", "ytg_bin", "ttt_bin", "season"]),
        ("target_f", ["WR", "TE"], "opp_route", ["route_ran", "team_coverage_type", "down", "ytg_bin", "season"]),
        ("vmax_prepass", ["WR", "TE"], "opp_route", ["route_ran", "ttt_bin", "down", "season"]),
        ("player_get_off", ["DL"], "opp_pass_rush", ["lined_up_position", "blitzing", "down", "ytg_bin", "offense_formation", "season"]),
        ("pressure_gen", ["DL"], "opp_pass_rush", ["lined_up_position", "blitzing", "down", "ytg_bin", "ttt_bin", "season"]),
        ("disp_10", ["DL"], "opp_pass_rush", ["lined_up_position", "blitzing", "down", "ytg_bin", "season"]),
        ("fwd_10", ["DL"], "opp_pass_rush", ["lined_up_position", "blitzing", "down", "ytg_bin", "season"]),
        ("t_to_4", ["DL"], "opp_pass_rush", ["lined_up_position", "blitzing", "down", "ytg_bin", "season"]),
        ("pressure_allowed_f", ["OL"], "opp_pass_block", ["lined_up_position", "pass_rushers_encountered", "down", "ytg_bin", "ttt_bin", "season"]),
        ("peak_pressure_probability_allowed", ["OL"], "opp_pass_block", ["lined_up_position", "pass_rushers_encountered", "down", "ytg_bin", "ttt_bin", "season"]),
        ("lat_15", ["OL"], "opp_pass_block", ["lined_up_position", "down", "ytg_bin", "season"]),
        ("vmax_play", ["DB"], "opp_coverage", ["cov_role", "team_coverage_type", "down", "ytg_bin", "ttt_bin", "season"]),
        ("vmax_play_man", ["DB"], "opp_coverage", ["team_coverage_type", "down", "ytg_bin", "ttt_bin", "season"]),
        ("vmax_play_deepzone", ["DB"], "opp_coverage", ["team_coverage_type", "down", "ytg_bin", "ttt_bin", "season"]),
        ("cushion", ["DB"], "opp_coverage", ["cov_role", "team_coverage_type", "down", "ytg_bin", "season"]),
        ("tackle", ["DB", "DL"], "opp_run_snap", ["lined_up_position", "down", "ytg_bin", "offense_formation", "season"]),
    ]
    r = r.with_columns(
        pl.when(pl.col("route_depth") == "deep").then(pl.col("separation_at_pass_forward")).alias("separation_deep"),
        pl.when(pl.col("route_depth") == "short").then(pl.col("separation_at_pass_forward")).alias("separation_short"),
        pl.when(pl.col("cov_role") == "man").then(pl.col("vmax_play")).alias("vmax_play_man"),
        pl.when(pl.col("cov_role") == "deep_zone").then(pl.col("vmax_play")).alias("vmax_play_deepzone"),
        pl.col("tackle").fill_null(0).cast(pl.Float64),
    )
    halves = (r.select("nfl_id", "game_id").unique().sort("nfl_id", "game_id")
              .with_columns((pl.int_range(pl.len()).over("nfl_id") % 2).alias("half")))
    r = r.join(halves, on=["nfl_id", "game_id"])
    rel_rows, player_tables = [], []
    for y, poss, oppcol, ctx in cands:
        for p in poss:
            d = r.filter((pl.col("pos") == p) & pl.col(oppcol) & pl.col(y).is_not_null())
            if d.height < 500:
                continue
            d = d.with_columns(residualise(d, y, ctx).alias("y_adj"))
            ctx_r2 = 1 - float(d["y_adj"].var() / d[y].var())
            for kind, col in (("raw", y), ("adj", "y_adj")):
                pm = d.group_by("nfl_id").agg(pl.len().alias("n"), pl.col(col).mean().alias("m"))
                ph = d.group_by("nfl_id", "half").agg(pl.len().alias("n"), pl.col(col).mean().alias("m"))
                ph = ph.pivot(index="nfl_id", on="half", values=["m", "n"])
                ph = ph.rename({c: c.replace('"', "") for c in ph.columns})
                ok = ph.filter((pl.col("n_0") >= CFG["min_opp"] / 2) & (pl.col("n_1") >= CFG["min_opp"] / 2)).drop_nulls()
                a0 = ok["m_0"].to_numpy(); a1 = ok["m_1"].to_numpy(); n = len(a0)
                rho = stats.spearmanr(a0, a1)[0] if n > 5 else np.nan
                ci = boot_ci(lambda i: stats.spearmanr(a0[i], a1[i])[0], n, rng, B) if n > 10 else (np.nan, np.nan)
                # season-to-season (consecutive seasons, >= min_opp_season each)
                ps = d.group_by("nfl_id", "season").agg(pl.len().alias("n"), pl.col(col).mean().alias("m")) \
                    .filter(pl.col("n") >= CFG["min_opp_season"])
                ss = ps.join(ps.with_columns((pl.col("season") - 1).alias("season")), on=["nfl_id", "season"], suffix="_next")
                rss = stats.spearmanr(ss["m"], ss["m_next"])[0] if ss.height > 8 else np.nan
                elig = pm.filter(pl.col("n") >= CFG["min_opp"])
                # between-player variance share (ICC-like, one-way ANOVA on plays, eligible players)
                de = d.join(elig.select("nfl_id"), on="nfl_id")
                grp = de.group_by("nfl_id").agg(pl.col(col).mean().alias("mu"), pl.col(col).var().alias("v"), pl.len().alias("k"))
                within = float((grp["v"] * (grp["k"] - 1)).sum() / (grp["k"] - 1).sum())
                between = float(grp["mu"].var() - (within / grp["k"]).mean())
                icc1 = between / (between + within) if between + within > 0 else np.nan
                rel_rows.append(dict(outcome=y, pos=p, kind=kind, opportunity=oppcol.replace("opp_", ""), plays=d.height,
                                     players_any=pm.height, players_eligible=elig.height,
                                     median_opp_eligible=float(elig["n"].median()) if elig.height else np.nan,
                                     context_r2=ctx_r2 if kind == "adj" else np.nan,
                                     play_icc=icc1, split_half_n=n, split_half_rho=rho,
                                     split_half_sb=float(2 * rho / (1 + rho)) if np.isfinite(rho) else np.nan,
                                     sb_lo=float(2 * ci[0] / (1 + ci[0])) if np.isfinite(ci[0]) else np.nan,
                                     sb_hi=float(2 * ci[1] / (1 + ci[1])) if np.isfinite(ci[1]) else np.nan,
                                     season_pairs=ss.height, season_rho=rss))
                if kind == "adj":
                    player_tables.append(pm.with_columns(pl.lit(y).alias("outcome"), pl.lit(p).alias("pos")))
    rel = pl.DataFrame(rel_rows, infer_schema_length=None)
    rel.write_parquet(out / "outcome_reliability.parquet")
    # player-level adjusted outcomes are saved for the NEXT phase only; they are not joined to combine data here.
    pl.concat(player_tables).write_parquet(out / "player_outcomes_adjusted.parquet")

    # cross-check: our tracked DL burst vs NGS get-off (validity of tracking metric; no combine data involved)
    dlv = r.filter((pl.col("pos") == "DL") & pl.col("opp_pass_rush") & pl.col("player_get_off").is_not_null()
                   & pl.col("disp_10").is_not_null())
    valid = dict(
        play_level_spearman_getoff_vs_disp10=float(stats.spearmanr(dlv["player_get_off"], dlv["disp_10"])[0]),
        play_level_spearman_getoff_vs_t_to_4=float(stats.spearmanr(*dlv.select("player_get_off", "t_to_4").drop_nulls().to_numpy().T)[0]),
        play_level_spearman_getoff_vs_fwd10=float(stats.spearmanr(dlv["player_get_off"], dlv["fwd_10"])[0]))
    dpl = dlv.group_by("nfl_id").agg(pl.len().alias("n"), pl.col("player_get_off").mean(), pl.col("disp_10").mean(), pl.col("fwd_10").mean()) \
        .filter(pl.col("n") >= CFG["min_opp"])
    valid["player_level_spearman_getoff_vs_disp10"] = float(stats.spearmanr(dpl["player_get_off"], dpl["disp_10"])[0])
    valid["player_level_n"] = dpl.height
    wv = r.filter(pl.col("opp_route") & pl.col("separation_at_pass_forward").is_not_null() & pl.col("time_to_throw").is_not_null())
    valid["sep_vs_time_to_throw_play_spearman"] = float(stats.spearmanr(wv["separation_at_pass_forward"], wv["time_to_throw"])[0])
    valid["sep_median_by_depth"] = {k: float(v) for k, v in wv.group_by("route_depth").agg(pl.col("separation_at_pass_forward").median()).iter_rows()}
    valid["sep_median_by_manzone"] = {str(k): float(v) for k, v in wv.group_by("team_coverage_man_zone").agg(pl.col("separation_at_pass_forward").median()).iter_rows()}
    json.dump(valid, open(out / "tracking_metric_validity.json", "w"), indent=1)

    # speed demand by position x context (descriptive; uses no combine data)
    dem = []
    for p in POS:
        d = r.filter((pl.col("pos") == p) & pl.col("vmax_play").is_not_null())
        if p in ("WR", "TE"):
            d = d.filter(pl.col("opp_route")); key = "route_depth"
        elif p == "DB":
            d = d.filter(pl.col("is_pass")).with_columns(pl.col("cov_role").fill_null("no_label")); key = "cov_role"
        else:
            d = d.with_columns(pl.when(pl.col("is_pass")).then(pl.lit("pass")).otherwise(pl.lit("run")).alias("pr")); key = "pr"
        top = d.group_by("nfl_id").agg(pl.col("vmax_play").top_k(5).mean().alias("top5"))
        d = d.join(top, on="nfl_id").with_columns((pl.col("vmax_play") / pl.col("top5")).alias("frac_of_own_top"))
        dem.append(d.group_by(key).agg(pl.len().alias("plays"), pl.col("vmax_play").median().alias("median_play_vmax"),
                                       (pl.col("frac_of_own_top") >= 0.9).mean().alias("share_plays_ge90pct_own_top"))
                   .rename({key: "context"}).with_columns(pl.lit(p).alias("pos")))
    pl.concat(dem, how="diagonal_relaxed").write_parquet(out / "speed_demand.parquet")

    # ---------------- predictor side (combine only; outcome-blind) ---------------------------------
    pred_rows = []
    for p in POS:
        g = base.filter(pl.col("pos") == p)
        for a_, b_ in [("peak_speed", "forty"), ("peak_speed", "ten_yd_split"), ("forty", "ten_yd_split"),
                       ("peak_speed", "combine_weight"), ("forty", "combine_weight"), ("ten_yd_split", "combine_weight"),
                       ("forty", "three_cone"), ("peak_speed", "three_cone")]:
            gg = g.select(a_, b_).drop_nulls()
            if gg.height < 10:
                continue
            rho = stats.spearmanr(gg[a_], gg[b_])[0]
            pr = stats.pearsonr(gg[a_], gg[b_])[0]
            pred_rows.append(dict(pos=p, a=a_, b=b_, n=gg.height, spearman=rho, pearson=pr, unique_var_a=1 - pr ** 2))
        # partial: peak speed vs forty controlling for weight (incremental-information potential)
        gg = g.select("peak_speed", "forty", "combine_weight").drop_nulls()
        if gg.height > 10:
            X = np.column_stack([np.ones(gg.height), gg["combine_weight"].to_numpy()])
            ra = gg["peak_speed"].to_numpy() - X @ np.linalg.lstsq(X, gg["peak_speed"].to_numpy(), rcond=None)[0]
            rb = gg["forty"].to_numpy() - X @ np.linalg.lstsq(X, gg["forty"].to_numpy(), rcond=None)[0]
            pred_rows.append(dict(pos=p, a="peak_speed|weight", b="forty|weight", n=gg.height,
                                  spearman=stats.spearmanr(ra, rb)[0], pearson=stats.pearsonr(ra, rb)[0],
                                  unique_var_a=1 - stats.pearsonr(ra, rb)[0] ** 2))
    pl.DataFrame(pred_rows).write_parquet(out / "predictor_structure.parquet")

    # ---------------- power / minimum detectable effects ------------------------------------------
    elig_counts = (opp.join(base.select("nfl_id", "peak_speed", "forty", "ten_yd_split"), on="nfl_id", how="left"))
    pw = []
    for p, oppk in [("WR", "route"), ("TE", "route"), ("DL", "pass_rush"), ("OL", "pass_block"), ("DB", "coverage"), ("DB", "run_snap"), ("DL", "run_snap")]:
        for thr in (50, 100, 200):
            e = elig_counts.filter((pl.col("pos") == p) & (pl.col(oppk) >= thr))
            for pred in ("peak_speed", "forty", "ten_yd_split"):
                n = int(e[pred].is_not_null().sum())
                pw.append(dict(pos=p, opportunity=oppk, min_opp=thr, predictor=pred, n=n,
                               mde_r=mde_r(n), mde_r_bonf5=mde_r(n, alpha=0.01)))
    pl.DataFrame(pw).write_parquet(out / "power.parquet")
    (ROOT / "experiments" / "phase3_screening" / "LATEST").write_text(run_id)
    print("done", out)


if __name__ == "__main__":
    {"features": features, "analyse": analyse}[sys.argv[1]]()
