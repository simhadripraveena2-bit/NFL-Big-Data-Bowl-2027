"""The single approved Combine-to-game-outcome join + join-validation report (no models, no associations).

Safety:
  * refuses to run if src/ or scripts/ have uncommitted changes (the output records the exact commit);
  * hashes every file under data/raw before and after (sha256) and aborts if anything changed;
  * reads only data/interim Parquet derived from raw; writes ONLY to a new directory
    data/interim/confirmatory_join/<run>/ (never overwrites) and experiments/confirmatory_join/<run>/;
  * computes counts, coverage, missingness and duplication checks only. It computes NO statistic that
    relates a combine predictor to a game outcome.

Usage: python scripts/run_confirmatory_join.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from nfl_bdb.data import confirmatory_data as cd  # noqa: E402
from run_real_capacity import forty_fits  # noqa: E402  (combine-only 40 fits)

RAW = ROOT / "data/raw"
INTERIM = ROOT / "data/interim"


def sha256_tree(root: Path) -> dict:
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h = hashlib.sha256()
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 24), b""):
                    h.update(chunk)
            out[str(p.relative_to(root))] = dict(sha256=h.hexdigest(), bytes=p.stat().st_size)
    return out


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def main():
    dirty = git("status", "--porcelain", "--", "src", "scripts", "tests")
    if dirty:
        raise SystemExit("refusing to run the join from uncommitted code:\n" + dirty)
    commit = git("rev-parse", "HEAD")
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dout = INTERIM / "confirmatory_join" / run; eout = ROOT / "experiments/confirmatory_join" / run
    if dout.exists() or eout.exists():
        raise SystemExit("output directory exists; the join never overwrites")
    dout.mkdir(parents=True); eout.mkdir(parents=True)

    raw_before = sha256_tree(RAW)
    interim_inputs = ["combine_results", "combine_tracking", "player_play", "games", "players", "phase3_play_features"]
    interim_before = sha256_tree_subset([INTERIM / f"{n}.parquet" for n in interim_inputs])

    # ---------------- inputs ----------------
    cr = pl.read_parquet(INTERIM / "combine_results.parquet")
    players = pl.read_parquet(INTERIM / "players.parquet")
    pp_all = pl.read_parquet(INTERIM / "player_play.parquet").join(pl.read_parquet(INTERIM / "games.parquet").select("game_id", "season", "season_type"), on="game_id")
    pred = cd.predictor_table(forty_fits(), cr)
    d, play_log = cd.outcome_table()

    rep = dict(run=run, code_commit=commit, play_exclusions=play_log)
    # ---------------- identity / matching (nfl_id exact key) ----------------
    reg_ids = pp_all.filter(pl.col("season_type") == "REG")["nfl_id"].unique()
    any_ids = pp_all["nfl_id"].unique()
    rep["identity"] = dict(
        combine_rows=cr.height, combine_unique_ids=cr["nfl_id"].n_unique(),
        players_rows=players.height, players_unique_ids=players["nfl_id"].n_unique(),
        predictor_rows=pred.height, predictor_unique_ids=pred["nfl_id"].n_unique(),
        combine_ids_with_multiple_positions=int(cr.group_by("nfl_id").agg(pl.col("combine_position").n_unique()).filter(pl.col("combine_position") > 1).height),
        combine_ids_with_multiple_draft_years=int(cr.group_by("nfl_id").agg(pl.col("draft_year").n_unique()).filter(pl.col("draft_year") > 1).height),
        combine_ids_not_in_players=int(cr.join(players, on="nfl_id", how="anti").height),
        game_ids_without_combine_row_any_season_type=int(pl.DataFrame({"nfl_id": any_ids}).join(cr, on="nfl_id", how="anti").height),
        game_ids_without_combine_row_REG=int(pl.DataFrame({"nfl_id": reg_ids}).join(cr, on="nfl_id", how="anti").height),
        player_play_duplicate_keys=cd.key_duplicates(pp_all),
        analysis_table_duplicate_keys=cd.key_duplicates(d),
        plays_before_draft_year=int(d.filter(pl.col("season") < pl.col("draft_year")).height),
        nonREG_rows_in_analysis_table=int(d.filter(pl.col("season_type") != "REG").height),
    )
    # by position: combine participants, valid tracked 40, any REG row, matched (both)
    m = (cr.select("nfl_id", pl.col("combine_position").alias("pos"))
         .join(pred.select("nfl_id", "valid_tracked_40", pl.col("forty").is_not_null().alias("has_forty")), on="nfl_id")
         .with_columns(pl.col("nfl_id").is_in(reg_ids.implode()).alias("has_REG_game_rows"),
                       pl.col("nfl_id").is_in(any_ids.implode()).alias("has_any_game_rows")))
    rep["matching_by_position"] = (m.group_by("pos").agg(
        pl.len().alias("combine_participants"), pl.col("valid_tracked_40").sum().alias("valid_tracked_40"),
        pl.col("has_forty").sum().alias("official_40"), pl.col("has_any_game_rows").sum().alias("any_game_rows"),
        pl.col("has_REG_game_rows").sum().alias("REG_game_rows"),
        (pl.col("has_REG_game_rows") & pl.col("valid_tracked_40")).sum().alias("matched_REG_and_valid_40"),
        (~pl.col("has_REG_game_rows")).sum().alias("unmatched_no_REG_rows"),
        (pl.col("has_REG_game_rows") & ~pl.col("valid_tracked_40")).sum().alias("REG_rows_but_no_valid_40"),
    ).sort("pos").to_dicts())

    # ---------------- the join (one per registered analysis frame) ----------------
    rep["frames"] = {}; manifest = {}
    standard = cd.standardisation_check(pred); rep["predictor_standardisation"] = standard.to_dicts()
    pred.write_parquet(dout / "predictors.parquet")
    for pos in cd.CONTRASTS:
        fr, el = cd.h1_eligible(d, pred, pos)
        j = cd.join_predictors(fr, pred)
        cols = cd.analysis_columns(pos)
        j = j.select(cols + [c for c in cd.PRED_COLS if c != "nfl_id"])
        j.write_parquet(dout / f"h1_{pos}.parquet")
        el.write_parquet(dout / f"eligibility_h1_{pos}.parquet")
        sens = {str(t): int(cd.h1_eligible(d, pred, pos, t)[1]["elig_all"].sum()) for t in (50, 200)}
        rep["frames"][f"h1_{pos}"] = dict(
            eligible_all=int(el["elig_all"].sum()), eligible_h1=int(el["elig_h1"].sum()),
            registered_all=cd.REGISTERED_N["all"][pos], registered_h1=cd.REGISTERED_N["h1"][pos], threshold_sensitivity_all=sens,
            rows_before_join=fr.height, rows_after_join=j.height, players=j["nfl_id"].n_unique(),
            duplicate_play_keys=cd.key_duplicates(j), team_seasons=j.select("team_abbr", "season").unique().height,
            plays_by_context=j.group_by("ctx").len().sort("ctx").to_dicts(),
            season_coverage=j.group_by("season").agg(pl.len().alias("plays"), pl.col("nfl_id").n_unique().alias("players")).sort("season").to_dicts(),
            draft_class=j.group_by("draft_year").agg(pl.col("nfl_id").n_unique().alias("players")).sort("draft_year").to_dicts(),
            nfl_year=j.group_by("nfl_year").len().sort("nfl_year").to_dicts(),
            missing=cd.missingness(j, cols + ["x_peak", "x_peak_mean", "forty"]).to_dicts(),
            ineligible_reasons=dict(opp_below_100=int((el["opp"] < 100).sum()), no_valid_40=int((~el["valid_tracked_40"]).sum()),
                                    passes_all_but_ctx_below_20=int((el["elig_all"] & ~el["elig_h1"]).sum())))
    f2, e2 = cd.h2_eligible(d, pred)
    j2 = cd.join_predictors(f2, pred)
    cols2 = cd.analysis_columns("WR", h2=True)
    j2 = j2.select(cols2 + [c for c in cd.PRED_COLS if c != "nfl_id"])
    j2.write_parquet(dout / "h2_WR.parquet"); e2.write_parquet(dout / "eligibility_h2_WR.parquet")
    rep["frames"]["h2_WR"] = dict(
        eligible_h2=int(e2["elig_h2"].sum()), registered_h2=cd.REGISTERED_N["h2"]["WR"],
        rows_before_join=f2.height, rows_after_join=j2.height, players=j2["nfl_id"].n_unique(),
        duplicate_play_keys=cd.key_duplicates(j2), team_seasons=j2.select("team_abbr", "season").unique().height,
        plays_by_depth=j2.group_by("route_depth").len().sort("route_depth").to_dicts(),
        season_coverage=j2.group_by("season").agg(pl.len().alias("plays"), pl.col("nfl_id").n_unique().alias("players")).sort("season").to_dicts(),
        missing=cd.missingness(j2, cols2 + ["x_peak", "forty"]).to_dicts(),
        ineligible_reasons=dict(opp_below_100=int((e2["opp"] < 100).sum()), no_valid_40=int((~e2["valid_tracked_40"]).sum()),
                                deep_below_30=int((e2["deep"] < 30).sum()), short_below_20=int((e2["short"] < 20).sum())))

    # cross-frame: no player appears under two positions; predictor rows unique
    allp = pl.concat([pl.read_parquet(dout / f"h1_{p}.parquet").select("nfl_id", "pos").unique() for p in cd.CONTRASTS])
    rep["identity"]["players_in_more_than_one_position_frame"] = int(allp.group_by("nfl_id").len().filter(pl.col("len") > 1).height)

    # ---------------- integrity ----------------
    raw_after = sha256_tree(RAW)
    interim_after = sha256_tree_subset([INTERIM / f"{n}.parquet" for n in interim_inputs])
    rep["raw_unchanged"] = raw_before == raw_after
    rep["interim_inputs_unchanged"] = interim_before == interim_after
    rep["raw_files"] = {k: v["sha256"][:16] for k, v in raw_before.items()}
    for p in sorted(dout.glob("*.parquet")):
        manifest[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    rep["outputs"] = dict(dir=str(dout.relative_to(ROOT)), sha256=manifest)
    json.dump(rep, open(eout / "join_validation.json", "w"), indent=1, default=str)
    (ROOT / "experiments/confirmatory_join/LATEST").write_text(run)
    if not (rep["raw_unchanged"] and rep["interim_inputs_unchanged"]):
        raise SystemExit("INTEGRITY FAILURE: raw or interim inputs changed during the join")
    print(json.dumps({k: rep[k] for k in ("run", "code_commit", "raw_unchanged", "interim_inputs_unchanged")}, indent=1))
    print("->", eout / "join_validation.json")


def sha256_tree_subset(paths):
    out = {}
    for p in paths:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 24), b""):
                h.update(chunk)
        out[p.name] = h.hexdigest()
    return out


if __name__ == "__main__":
    main()
