"""Final pre-model audit (no model, no association, no second join).

Checks:
  1. frozen code: sha256 of every file in research_notes/code_freeze.json, and no git diff vs the freeze commit;
  2. join unchanged: sha256 of every join output vs the manifest written by the join; no extra / missing files;
     raw data sha256 (prefix) vs the values recorded at join time;
  3. registered rules re-derived independently of the stored outputs, WITHOUT re-joining:
       - predictors.parquet == predictor table recomputed from combine data alone;
       - eligibility tables == eligibility recomputed from the outcome side + the validity flag;
       - outcome part of every stored frame (keys, context, outcome, covariates) == outcome frame recomputed
         without predictors;
       - predictor columns of every stored frame == the player's row in predictors.parquet (lookup consistency);
       - identity checks (unique nfl_id, no cross-position players, no pre-draft or non-REG plays, no duplicates);
  4. final sample sizes vs the registration;
  5. inventory of experiment / interim outputs created after the join (to show no model output exists).
Writes experiments/pre_model_audit/<run>/audit.json. Never writes to data/.
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
from run_real_capacity import forty_fits  # noqa: E402

JOIN_RUN = "20261121T135032Z"
FREEZE_COMMIT = "955d94d4486175223d045af6a883e09ac519432d"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 24), b""):
            h.update(c)
    return h.hexdigest()


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def frames_equal(a: pl.DataFrame, b: pl.DataFrame, keys) -> bool:
    if a.columns != b.columns or a.height != b.height:
        return False
    return a.sort(keys).equals(b.sort(keys))


def main():
    res, ok = {}, True
    # 1. frozen code
    fz = json.loads((ROOT / "research_notes/code_freeze.json").read_text())
    changed = [f for f, h in fz["files"].items() if sha(ROOT / f) != h]
    diff = git("diff", "--name-only", FREEZE_COMMIT, "HEAD", "--", *fz["files"].keys())
    dirty = git("status", "--porcelain", "--", *fz["files"].keys())
    res["code"] = dict(frozen_files=len(fz["files"]), hash_mismatches=changed, diff_vs_freeze_commit=diff.splitlines(),
                       uncommitted=dirty.splitlines(), head=git("rev-parse", "HEAD"), freeze_commit=FREEZE_COMMIT)
    ok &= not changed and not diff and not dirty

    # 2. join outputs + raw
    jv = json.loads((ROOT / f"experiments/confirmatory_join/{JOIN_RUN}/join_validation.json").read_text())
    jdir = ROOT / jv["outputs"]["dir"]
    now = {p.name: sha(p) for p in sorted(jdir.iterdir()) if p.is_file()}
    res["join"] = dict(run=JOIN_RUN, join_code_commit=jv["code_commit"], files=len(now),
                       mismatched=[k for k in jv["outputs"]["sha256"] if now.get(k) != jv["outputs"]["sha256"][k]],
                       extra=[k for k in now if k not in jv["outputs"]["sha256"]], missing=[k for k in jv["outputs"]["sha256"] if k not in now],
                       other_join_runs=[p.name for p in (ROOT / "data/interim/confirmatory_join").iterdir() if p.name != JOIN_RUN])
    ok &= not (res["join"]["mismatched"] or res["join"]["extra"] or res["join"]["missing"] or res["join"]["other_join_runs"])
    ok &= jv["code_commit"] == FREEZE_COMMIT
    raw_now = {str(p.relative_to(ROOT / "data/raw")): sha(p)[:16] for p in sorted((ROOT / "data/raw").rglob("*")) if p.is_file()}
    res["raw"] = dict(files=len(raw_now), unchanged_since_join=raw_now == jv["raw_files"])
    ok &= res["raw"]["unchanged_since_join"]

    # 3. registered rules, re-derived without re-joining
    cr = pl.read_parquet(ROOT / "data/interim/combine_results.parquet")
    pred_re = cd.predictor_table(forty_fits(), cr)
    pred = pl.read_parquet(jdir / "predictors.parquet")
    rules = dict(predictors_equal_recomputed=frames_equal(pred, pred_re.select(pred.columns), ["nfl_id"]))
    d, log = cd.outcome_table()
    rules["play_exclusions_equal_join_log"] = log == jv["play_exclusions"]
    sizes = {}
    pcols = [c for c in cd.PRED_COLS if c != "nfl_id"]
    for pos in cd.CONTRASTS:
        fr, el = cd.h1_eligible(d, pred, pos)
        st = pl.read_parquet(jdir / f"h1_{pos}.parquet"); sel = pl.read_parquet(jdir / f"eligibility_h1_{pos}.parquet")
        cols = cd.analysis_columns(pos)
        rules[f"h1_{pos}_eligibility_equal"] = frames_equal(sel, el, ["nfl_id"])
        rules[f"h1_{pos}_outcome_part_equal"] = frames_equal(st.select(cols), fr.select(cols), ["game_id", "play_id", "nfl_id"])
        look = st.select(["nfl_id"] + pcols).unique().sort("nfl_id")
        rules[f"h1_{pos}_predictor_lookup_consistent"] = look.equals(pred.filter(pl.col("nfl_id").is_in(look["nfl_id"].implode())).select(["nfl_id"] + pcols).sort("nfl_id"))
        rules[f"h1_{pos}_no_duplicate_keys"] = cd.key_duplicates(st) == 0
        rules[f"h1_{pos}_one_position"] = bool((st["pos"] == pos).all())
        sizes[f"h1_{pos}"] = dict(eligible_all=int(el["elig_all"].sum()), registered_all=cd.REGISTERED_N["all"][pos],
                                  test=st["nfl_id"].n_unique(), registered_test=cd.REGISTERED_N["h1"][pos], plays=st.height)
    f2, e2 = cd.h2_eligible(d, pred)
    st2 = pl.read_parquet(jdir / "h2_WR.parquet"); cols2 = cd.analysis_columns("WR", h2=True)
    rules["h2_eligibility_equal"] = frames_equal(pl.read_parquet(jdir / "eligibility_h2_WR.parquet"), e2, ["nfl_id"])
    rules["h2_outcome_part_equal"] = frames_equal(st2.select(cols2), f2.select(cols2), ["game_id", "play_id", "nfl_id"])
    rules["h2_no_duplicate_keys"] = cd.key_duplicates(st2) == 0
    sizes["h2_WR"] = dict(test=st2["nfl_id"].n_unique(), registered_test=cd.REGISTERED_N["h2"]["WR"], plays=st2.height)
    rules["unique_nfl_id_combine_and_predictors"] = cr["nfl_id"].n_unique() == cr.height == pred.height == pred["nfl_id"].n_unique()
    rules["no_pre_draft_plays"] = d.filter(pl.col("season") < pl.col("draft_year")).height == 0
    rules["REG_only"] = bool((d["season_type"] == "REG").all())
    rules["no_nullified_plays"] = d.filter(pl.col("play_nullified_by_penalty") == "Y").height == 0
    rules["no_faulty_game_plays"] = d.filter((pl.col("game_id") == 2025101205) & pl.col("play_id").is_in([1289, 1314])).height == 0
    rules["no_speed_spikes"] = d.filter((pl.col("vmax_play") > 12.5) | (pl.col("vmax_prepass") > 12.5)).height == 0
    rules["valid_attempt_rule_no_spike_selected"] = bool(pred.filter(pl.col("x_peak") > 12.5).height == 0)
    res["rules"] = rules
    ok &= all(rules.values())
    res["sample_sizes"] = sizes
    ok &= all(v["test"] == v["registered_test"] for v in sizes.values()) and all(v.get("eligible_all", 0) == v.get("registered_all", 0) for v in sizes.values())

    # 5. outputs created after the join (to document that no model output exists)
    jt = datetime.strptime(JOIN_RUN, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).timestamp()
    res["files_created_after_join"] = sorted(str(p.relative_to(ROOT)) for base in ("experiments", "data/interim", "reports")
                                             for p in (ROOT / base).rglob("*") if p.is_file() and p.stat().st_mtime > jt)
    res["all_checks_passed"] = bool(ok)
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); out = ROOT / "experiments/pre_model_audit" / run
    out.mkdir(parents=True); json.dump(res, open(out / "audit.json", "w"), indent=1, default=str)
    print(json.dumps(res, indent=1, default=str)); print("->", out / "audit.json")


if __name__ == "__main__":
    main()
