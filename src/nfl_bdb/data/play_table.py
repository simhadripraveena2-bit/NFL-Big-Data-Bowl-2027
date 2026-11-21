"""Regular-season player-play analysis table with pre-registered context definitions (Phase 3.5).

Combines player_play (REG only), games and the Phase 3 tracking features
(data/interim/phase3_play_features.parquet, built by scripts/run_phase3_screening.py features).

Only the *position label* is taken from combine_results. No combine measurement is joined here:
combine predictors are attached only in the confirmatory stage, after pre-registration.
"""
from __future__ import annotations

import numpy as np
import polars as pl

from nfl_bdb.data.io import INTERIM, load

# Pre-registered route-depth classes (route-tree definition, fixed before any outcome association).
DEEP_ROUTES = ("GO", "POST", "CORNER", "WHEEL")
SHORT_ROUTES = ("HITCH", "SLANT", "OUT", "FLAT", "SCREEN", "ANGLE")
AMBIGUOUS_ROUTES = ("IN", "CROSS")  # dig vs shallow cross cannot be separated from the label
FEATURES = INTERIM / "phase3_play_features.parquet"


def reg_play_table() -> pl.DataFrame:
    games = load("games", lazy=False).select("game_id", "season", "season_type", "week")
    pos = load("combine_results", lazy=False).select("nfl_id", pl.col("combine_position").alias("pos"), "draft_year")
    pp = (load("player_play", lazy=False).join(games, on="game_id").filter(pl.col("season_type") == "REG")
          .join(pos, on="nfl_id", how="inner"))
    feat = pl.read_parquet(FEATURES).select("game_id", "play_id", "nfl_id", "k_pf", "vmax_play", "vmax_prepass")
    d = pp.join(feat, on=["game_id", "play_id", "nfl_id"], how="left")
    d = d.with_columns(
        (pl.col("pass_result").fill_null("") != "").alias("is_pass"),
        (pl.col("k_pf") / 10).alias("time_to_throw"),
        (pl.col("season") - pl.col("draft_year") + 1).alias("nfl_year"),
        pl.when(pl.col("yards_to_go") <= 3).then(pl.lit("short")).when(pl.col("yards_to_go") <= 7)
        .then(pl.lit("med")).otherwise(pl.lit("long")).alias("ytg_bin"),
    ).with_columns(
        pl.when(pl.col("time_to_throw").is_null()).then(pl.lit("NA")).when(pl.col("time_to_throw") < 2.5)
        .then(pl.lit("<2.5")).when(pl.col("time_to_throw") < 3.5).then(pl.lit("2.5-3.5"))
        .otherwise(pl.lit(">=3.5")).alias("ttt_bin"),
        pl.when(pl.col("route_ran").is_in(DEEP_ROUTES)).then(pl.lit("deep"))
        .when(pl.col("route_ran").is_in(SHORT_ROUTES)).then(pl.lit("short"))
        .when(pl.col("route_ran").is_not_null()).then(pl.lit("ambiguous")).alias("route_depth"),
        pl.when(pl.col("coverage_assignment") == "MAN").then(pl.lit("man"))
        .when(pl.col("coverage_assignment").str.starts_with("DEEP") | pl.col("coverage_assignment").str.starts_with("QUARTERS"))
        .then(pl.lit("deep_zone"))
        .when(pl.col("coverage_assignment").is_in(["NO_ASSIGNMENT", "PREVENT"])).then(pl.lit("excluded"))
        .when(pl.col("coverage_assignment").is_not_null()).then(pl.lit("under_zone")).alias("cov_role"),
    )
    return d


def h1_frame(d: pl.DataFrame, pos: str) -> pl.DataFrame:
    """Rows, outcome `y` (play max speed) and task context `ctx` for H1/H5 in one position."""
    x = d.filter(pl.col("pos") == pos)
    if pos in ("WR", "TE"):
        x = x.filter(pl.col("is_pass") & pl.col("route_depth").is_in(["deep", "short"]))
        x = x.with_columns(pl.col("vmax_prepass").alias("y"), pl.col("route_depth").alias("ctx"))
    elif pos == "DB":
        x = x.filter(pl.col("is_pass") & pl.col("cov_role").is_in(["man", "deep_zone", "under_zone"]))
        x = x.with_columns(pl.col("vmax_play").alias("y"), pl.col("cov_role").alias("ctx"))
    elif pos == "DL":
        x = x.filter((pl.col("is_pass") & pl.col("player_get_off").is_not_null()) | ~pl.col("is_pass"))
        x = x.with_columns(pl.col("vmax_play").alias("y"),
                           pl.when(pl.col("is_pass")).then(pl.lit("pass_rush")).otherwise(pl.lit("run")).alias("ctx"))
    elif pos == "OL":
        x = x.filter((pl.col("is_pass") & pl.col("pass_rushers_encountered").is_not_null()) | ~pl.col("is_pass"))
        x = x.with_columns(pl.col("vmax_play").alias("y"),
                           pl.when(pl.col("is_pass")).then(pl.lit("pass_block")).otherwise(pl.lit("run")).alias("ctx"))
    return x.filter(pl.col("y").is_not_null())


H1_COVARIATES = {
    "WR": ["route_ran", "team_coverage_type", "down", "ytg_bin", "offense_formation", "ttt_bin", "season"],
    "TE": ["route_ran", "team_coverage_type", "down", "ytg_bin", "offense_formation", "ttt_bin", "season"],
    "DB": ["ctx", "team_coverage_type", "lined_up_position", "down", "ytg_bin", "ttt_bin", "season"],
    "DL": ["ctx", "lined_up_position", "down", "ytg_bin", "offense_formation", "season"],
    "OL": ["ctx", "lined_up_position", "down", "ytg_bin", "offense_formation", "season"],
}
H2_COVARIATES = ["route_ran", "team_coverage_type", "down", "ytg_bin", "offense_formation", "in_motion_at_ball_snap",
                 "ttt_bin", "season"]


def residualise(df: pl.DataFrame, y: str, ctx: list[str]) -> np.ndarray:
    """Play-level OLS residual of y on one-hot pre-snap context (+ grand mean). Context-specific
    means are removed only through the covariates (route_ran is nested in route depth)."""
    d = df.select([y] + ctx).with_columns([pl.col(c).cast(pl.Utf8).fill_null("NA") for c in ctx])
    X = d.select(ctx).to_dummies(drop_first=True).to_numpy().astype(float)
    X = np.column_stack([np.ones(len(d)), X])
    yy = d[y].to_numpy().astype(float)
    beta, *_ = np.linalg.lstsq(X, yy, rcond=None)
    return yy - X @ beta + yy.mean()
