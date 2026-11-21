"""The single registered Combine-to-game-outcome join (preregistration §3–§5, §14).

Registered rules implemented here, and nowhere else, for the confirmatory stage:
  * Linking key: `nfl_id` (competition identifier; player_matching_report.md). Exact key equality, no name matching.
  * Position: `combine_results.combine_position`.
  * Predictors (combine only, §3.1):
      valid attempt  = mono-exponential R^2 > 0.95 and attempt max speed <= 12.5 yd/s
      x_peak         = max over valid attempts of the attempt max speed (primary);  x_peak_mean (sensitivity)
      F              = official electronic 40 (s); modelling uses it sign-reversed
      standardisation within combine position over ALL combine participants with a value (not only eligible)
  * Outcomes (§3.2, §4): REG season only; plays nullified by penalty removed; faulty game 2025101205 plays
    1289/1314 and any player-play with s > 12.5 yd/s removed (tracking features are missing for those, and are
    also re-checked here); plays without a ball_snap frame have no tracking feature and are dropped.
  * Eligibility (§4): valid tracked 40; >= 100 primary REG opportunities (routes / coverage snaps / pass rushes /
    pass blocks); H1/H5 additionally >= 20 plays in each contrast context; H2 additionally an official 40,
    >= 30 deep routes with separation and >= 20 short routes with separation.
  * Missing data (§5): never imputed; covariate nulls become the "NA" level at model time (not here).
The join is performed once per eligible frame as an inner m:1 join on nfl_id (validated), so a play row can never
be multiplied. Outputs are written once and never overwrite existing files.
"""
from __future__ import annotations

import polars as pl

from nfl_bdb.data.play_table import H1_COVARIATES, H2_COVARIATES, h1_frame, reg_play_table

R2_MIN = 0.95
S_MAX = 12.5
MIN_PRIMARY_OPP = 100
MIN_CTX_PLAYS = 20
H2_MIN_DEEP = 30
H2_MIN_SHORT = 20
FAULTY = [(2025101205, 1289), (2025101205, 1314)]
CONTRASTS = {"WR": ["deep", "short"], "TE": ["deep", "short"], "DB": ["man", "under_zone"],
             "DL": ["pass_rush", "run"], "OL": ["pass_block", "run"]}
PRIMARY_OPP = {"WR": "route", "TE": "route", "DB": "coverage", "DL": "pass_rush", "OL": "pass_block"}
# registered counts at freezing (§4)
REGISTERED_N = {"all": {"WR": 57, "TE": 18, "DB": 56, "DL": 53, "OL": 53},
                "h1": {"WR": 57, "TE": 17, "DB": 52, "DL": 53, "OL": 53}, "h2": {"WR": 57}}


def predictor_table(attempts: pl.DataFrame, combine_results: pl.DataFrame) -> pl.DataFrame:
    """attempts: one row per tracked 40 attempt with nfl_id, attempt, vpeak, r2. Combine data only."""
    valid = attempts.filter((pl.col("r2") > R2_MIN) & (pl.col("vpeak") <= S_MAX))
    x = valid.group_by("nfl_id").agg(pl.col("vpeak").max().alias("x_peak"), pl.col("vpeak").mean().alias("x_peak_mean"),
                                     pl.len().alias("n_valid_attempts"))
    cr = combine_results.select("nfl_id", pl.col("combine_position").alias("pos"), "draft_year", "forty")
    t = cr.join(x, on="nfl_id", how="left", validate="1:1")
    z = lambda c: ((pl.col(c) - pl.col(c).mean().over("pos")) / pl.col(c).std().over("pos"))  # noqa: E731  (nulls ignored)
    return t.with_columns(z("x_peak").alias("x_peak_z"), z("x_peak_mean").alias("x_peak_mean_z"),
                          (-z("forty")).alias("forty_rev_z"), pl.col("x_peak").is_not_null().alias("valid_tracked_40"))


def outcome_table() -> tuple[pl.DataFrame, dict]:
    """REG play table with every registered play exclusion applied. Outcome-side only (no combine values)."""
    d = reg_play_table()
    log = {"reg_player_plays": d.height}
    d = d.filter(pl.col("play_nullified_by_penalty").fill_null("N") != "Y"); log["after_nullified"] = d.height
    bad = pl.DataFrame({"game_id": [g for g, _ in FAULTY], "play_id": [p for _, p in FAULTY]})
    d = d.join(bad, on=["game_id", "play_id"], how="anti"); log["after_faulty_game"] = d.height
    spikes = d.filter((pl.col("vmax_play") > S_MAX) | (pl.col("vmax_prepass") > S_MAX)).height
    d = d.filter(~((pl.col("vmax_play") > S_MAX) | (pl.col("vmax_prepass") > S_MAX)).fill_null(False))
    log["spike_rows_removed_here"] = spikes
    log["no_tracking_feature_rows"] = int(d["vmax_play"].is_null().sum())   # incl. no ball_snap / faulty / spike seqs
    return d, log


def primary_opp_counts(d: pl.DataFrame) -> pl.DataFrame:
    e = {"route": pl.col("pos").is_in(["WR", "TE"]) & pl.col("is_pass") & pl.col("route_ran").is_not_null(),
         "pass_rush": pl.col("player_get_off").is_not_null(),
         "pass_block": pl.col("pass_rushers_encountered").is_not_null(),
         "coverage": pl.col("is_pass") & pl.col("coverage_assignment").is_not_null() & (pl.col("coverage_assignment") != "NO_ASSIGNMENT")}
    return d.group_by("nfl_id", "pos").agg(*[v.sum().alias(k) for k, v in e.items()])


def h1_eligible(d: pl.DataFrame, pred: pl.DataFrame, pos: str, min_opp: int = MIN_PRIMARY_OPP) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Returns (play frame restricted to eligible players and the two contrast contexts, per-player eligibility table)."""
    ctxs = CONTRASTS[pos]
    opp = primary_opp_counts(d).filter(pl.col("pos") == pos).select("nfl_id", pl.col(PRIMARY_OPP[pos]).alias("opp"))
    fr = h1_frame(d, pos).filter(pl.col("ctx").is_in(ctxs))
    cnt = fr.group_by("nfl_id", "ctx").len().pivot(index="nfl_id", on="ctx", values="len").fill_null(0)
    for c in ctxs:
        if c not in cnt.columns:
            cnt = cnt.with_columns(pl.lit(0, pl.UInt32).alias(c))
    el = (opp.join(cnt.select(["nfl_id"] + ctxs), on="nfl_id", how="left").fill_null(0)
          .join(pred.filter(pl.col("pos") == pos).select("nfl_id", "valid_tracked_40"), on="nfl_id", how="left")
          .with_columns(pl.col("valid_tracked_40").fill_null(False))
          .with_columns(elig_all=(pl.col("opp") >= min_opp) & pl.col("valid_tracked_40"))
          .with_columns(elig_h1=pl.col("elig_all") & pl.all_horizontal([pl.col(c) >= MIN_CTX_PLAYS for c in ctxs])))
    keep = el.filter(pl.col("elig_h1"))["nfl_id"].implode()
    return fr.filter(pl.col("nfl_id").is_in(keep)), el


def h2_eligible(d: pl.DataFrame, pred: pl.DataFrame, min_opp: int = MIN_PRIMARY_OPP) -> tuple[pl.DataFrame, pl.DataFrame]:
    opp = primary_opp_counts(d).filter(pl.col("pos") == "WR").select("nfl_id", pl.col("route").alias("opp"))
    w = d.filter((pl.col("pos") == "WR") & pl.col("is_pass") & pl.col("route_depth").is_in(["deep", "short"])
                 & pl.col("separation_at_pass_forward").is_not_null())
    cnt = w.group_by("nfl_id", "route_depth").len().pivot(index="nfl_id", on="route_depth", values="len").fill_null(0)
    el = (opp.join(cnt, on="nfl_id", how="left").fill_null(0)
          .join(pred.filter(pl.col("pos") == "WR").select("nfl_id", "valid_tracked_40", "forty"), on="nfl_id", how="left")
          .with_columns(pl.col("valid_tracked_40").fill_null(False))
          .with_columns(elig_h2=(pl.col("opp") >= min_opp) & pl.col("valid_tracked_40") & pl.col("forty").is_not_null()
                        & (pl.col("deep") >= H2_MIN_DEEP) & (pl.col("short") >= H2_MIN_SHORT)))
    keep = el.filter(pl.col("elig_h2"))["nfl_id"].implode()
    return w.filter(pl.col("nfl_id").is_in(keep)), el


PRED_COLS = ["nfl_id", "x_peak", "x_peak_mean", "x_peak_z", "x_peak_mean_z", "forty", "forty_rev_z", "n_valid_attempts"]


def join_predictors(frame: pl.DataFrame, pred: pl.DataFrame) -> pl.DataFrame:
    """THE join: inner, many-to-one on nfl_id (validated). Never multiplies a play row."""
    out = frame.join(pred.select(PRED_COLS), on="nfl_id", how="inner", validate="m:1")
    if out.height != frame.height:
        raise RuntimeError(f"join changed the row count: {frame.height} -> {out.height}")
    return out


def analysis_columns(pos: str, h2: bool = False) -> list[str]:
    base = ["game_id", "play_id", "nfl_id", "pos", "team_abbr", "season", "week", "nfl_year", "draft_year"]
    if h2:
        return base + ["route_depth", "separation_at_pass_forward"] + [c for c in H2_COVARIATES if c not in base]
    return base + ["ctx", "y"] + [c for c in H1_COVARIATES[pos] if c not in base + ["ctx"]]


def missingness(df: pl.DataFrame, cols: list[str]) -> pl.DataFrame:
    n = df.height
    return pl.DataFrame([dict(variable=c, n=n, missing=int(df[c].null_count() + (df[c].is_nan().sum() if df[c].dtype.is_float() else 0)))
                         for c in cols]).with_columns((pl.col("missing") / pl.col("n")).alias("share"))


def key_duplicates(df: pl.DataFrame, keys=("game_id", "play_id", "nfl_id")) -> int:
    return int(df.height - df.select(list(keys)).unique().height)


def standardisation_check(pred: pl.DataFrame) -> pl.DataFrame:
    return pred.group_by("pos").agg(pl.col("x_peak").is_not_null().sum().alias("n_x"), pl.col("x_peak_z").mean().alias("mean_z"),
                                    pl.col("x_peak_z").std().alias("sd_z"), pl.col("forty").is_not_null().sum().alias("n_forty")).sort("pos")


__all__ = ["predictor_table", "outcome_table", "h1_eligible", "h2_eligible", "join_predictors", "missingness",
           "key_duplicates", "analysis_columns", "standardisation_check", "CONTRASTS", "REGISTERED_N"]
