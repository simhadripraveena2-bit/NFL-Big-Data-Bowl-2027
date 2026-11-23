"""Collect the registered results used by the Big Data Bowl writeup into one provenance-tagged JSON.

Phase 9B. This script only READS existing registered run outputs (experiments/<stage>/<run>/...).
It fits no model and computes no new association. Display transforms only:
  * yards -> inches (x 36) for H2 coefficients;
  * Wald 95 % intervals rho +/- 1.96 SE from the Wald standard errors already stored by the secondary run
    (registered check output; the confirmatory contrasts keep their registered bootstrap intervals);
  * percentages (x 100).

Output: paper/registered_results.json (aggregate numbers only; no player-level or play-level data).
Usage: python scripts/build_registered_results.py
"""
from __future__ import annotations

import json
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments"
OUT = ROOT / "paper" / "registered_results.json"

RUNS = {
    "h1_wr": "h1_wr_confirmatory/20261121T223645Z/h1_wr_result.json",
    "h1_wr_robustness": "h1_wr_robustness/20261121T233918Z/robustness.json",
    "h2": "h2_estimation/20261122T012339Z/h2_result.json",
    "secondary": "secondary/20261122T015315Z/secondary_result.json",
    "dl_audit": "secondary/20261122T015315Z/dl_role_weight_diagnostics.json",
    "join": "confirmatory_join/20261121T135032Z/join_validation.json",
    "forty_reliability": "forty_reliability/20261121T134306Z/reliability.parquet",
    "phase3": "phase3_screening/20261121T010253Z",
}


def j(key):
    return json.loads((EXP / RUNS[key]).read_text())


def wald(rho, se):
    return [max(-1.0, rho - 1.96 * se), min(1.0, rho + 1.96 * se)]


def main():
    h1, h2, sec, dl, jv = j("h1_wr"), j("h2"), j("secondary"), j("dl_audit"), j("join")
    p3 = EXP / RUNS["phase3"]
    res: dict = {"_about": "Registered results for the NFL Big Data Bowl 2027 writeup. Aggregates only. "
                           "Every block names its source run file. Built by scripts/build_registered_results.py.",
                 "_sources": {k: f"experiments/{v}" for k, v in RUNS.items()}}

    # ---- sample sizes (join validation) --------------------------------------------------------------
    res["samples"] = {
        "source": RUNS["join"], "join_run": jv["run"], "code_commit": jv["code_commit"],
        "matching_by_position": jv["matching_by_position"],
        "analysis": {"H1-WR": {"players": h1["sample"]["players"], "plays": h1["sample"]["plays"],
                               "deep_plays": h1["sample"]["by_context"][0]["plays"],
                               "short_plays": h1["sample"]["by_context"][1]["plays"]},
                     "H2-WR": {"players": h2["sample"]["players"], "deep_plays": h2["sample"]["plays_deep"],
                               "short_plays": h2["sample"]["plays_short"]},
                     **{f"H1-{p}": {"players": sec["wald"][f"{p}_full"]["players"], "plays": sec["wald"][f"{p}_full"]["plays"]}
                        for p in ("DB", "DL", "OL", "TE")}},
    }

    # ---- H1-WR primary --------------------------------------------------------------------------------
    pr = h1["primary"]
    res["h1_wr"] = {
        "source": RUNS["h1_wr"], "run": h1["run"], "code_commit": h1["code_commit"], "seed": h1["seed"], "B": h1["B"],
        "decision": h1["decision"], "delta": pr["delta"], "rho_deep": pr["rho_deep"], "rho_short": pr["rho_short"],
        "ci95": pr["ci95_percentile"], "ci90": pr["ci90_percentile"], "se_boot": pr["se_boot"], "p": pr["p_two_sided"],
        "season_forward_delta_2025": pr["season_forward"]["delta_2025"], "sesoi": h1["sesoi"],
    }

    # ---- per-context rho with Wald intervals (registered secondary-run check output) ----------------------
    rows = []
    for key, pos in [("WR_full", "WR"), ("TE_full", "TE"), ("DB3_full", "DB"), ("DL_full", "DL"), ("OL_full", "OL")]:
        w = sec["wald"][key]
        for c, r, s in zip(w["contexts"], w["rho"], w["se"]):
            rows.append(dict(pos=pos, ctx=c, rho=r, se=s, ci95_wald=wald(r, s), players=w["players"]))
    res["rho_by_context"] = {"source": RUNS["secondary"] + " :: wald", "interval": "Wald 95 % (rho +/- 1.96 SE), clipped to [-1, 1]",
                             "rows": rows}

    # ---- registered contrasts (bootstrap) --------------------------------------------------------------
    fam = sec["family"]
    res["contrasts"] = {
        "source": RUNS["secondary"] + " :: family / tests / h5a",
        "H1-WR": {"estimate": pr["delta"], "ci95": pr["ci95_percentile"], "decision": h1["decision"], "family": "primary"},
        "H1-DB": {**{k: fam["H1-DB"][k] for k in ("estimate", "ci95", "p_unadjusted", "p_holm", "decision")}, "family": "Holm secondary"},
        "H1-DL(a)": {**{k: fam["H1-DL(a)"][k] for k in ("estimate", "ci95", "ci90", "p_unadjusted", "p_holm", "decision")}, "family": "Holm secondary"},
        "H1-DL(b)": {**{k: fam["H1-DL(b)"][k] for k in ("estimate", "ci95", "p_unadjusted", "p_holm", "decision")}, "family": "Holm secondary"},
        "H5(b)": {**{k: fam["H5(b)"][k] for k in ("estimate", "ci95", "p_unadjusted", "p_holm", "decision")}, "family": "Holm secondary"},
        "H5(a) OL": {"estimate": sec["h5a"]["delta"], "ci95": sec["h5a"]["ci95"], "decision": "UNINFORMATIVE (estimation)", "family": "estimation"},
    }

    # ---- H2 ---------------------------------------------------------------------------------------------
    rb = h2["reml_bootstrap"]
    res["h2"] = {
        "source": RUNS["h2"], "code_commit": h2["code_commit"], "B": h2["B"], "status": "secondary, estimation-focused (D4, before any association)",
        "label": "INCONCLUSIVE",
        "beta_P_yd_per_sd": h2["deep"]["beta_P"], "beta_P_ci95_yd": rb["deep_beta_P"]["ci95"], "beta_P_ci90_yd": rb["deep_beta_P"]["ci90"],
        "beta_P_in_per_sd": h2["deep"]["beta_P"] * 36, "beta_P_ci95_in": [v * 36 for v in rb["deep_beta_P"]["ci95"]],
        "short_beta_P_yd": h2["short"]["beta_P"], "short_beta_P_ci95_yd": rb["short_beta_P"]["ci95"],
        "short_beta_P_in": h2["short"]["beta_P"] * 36, "short_beta_P_ci95_in": [v * 36 for v in rb["short_beta_P"]["ci95"]],
        "contrast_N3": h2["contrast_N3"], "partial_observed": h2["deep"]["partial"],
        "cv_frozen": h2["cv_frozen"], "season_forward": h2["season_forward"],
        "reliability_deep_level": h2["reliability_deep_level"], "between_player_sd_yd": h2["deep"]["s2b"] ** 0.5,
        "eiv_tipping_RF": h2["eiv_tipping_RF"], "p_boot_reml": h2["p_boot_reml"],
    }

    # ---- DL(b) audit -------------------------------------------------------------------------------------
    res["dl_b"] = {
        "source": RUNS["dl_audit"] + " + " + RUNS["secondary"] + " :: dl_b",
        "registered": {k: fam["H1-DL(b)"][k] for k in ("estimate", "ci95", "p_unadjusted", "p_holm", "decision")},
        "base_pooled": sec["dl_b"]["base_pooled"], "adjusted_pooled": sec["dl_b"]["adjusted_pooled"],
        "variants": [dict(label=v["label"], pooled=v["pooled"], pooled_se=v["pooled_se"],
                          ci95_wald=wald(v["pooled"], v["pooled_se"])) for v in dl["variants"]],
        "within_role": {r: dict(pooled=v["pooled"], pooled_se=v["pooled_se"], ci95_wald=wald(v["pooled"], v["pooled_se"]))
                        for r, v in dl["within_role"].items()},
        "role_means": dl["role_means"], "corr_eligible": dl["corr_eligible"],
        "interval_note": "Variant intervals are Wald (descriptive audit); only the registered pooled-minus-adjusted test is inferential.",
    }

    # ---- combine measurement (outcome-blind) ------------------------------------------------------------
    rel = pl.read_parquet(EXP / RUNS["forty_reliability"]).filter(pl.col("measure").str.starts_with("vpeak"))
    ps = pl.read_parquet(p3 / "predictor_structure.parquet")
    fx = ps.filter((pl.col("a") == "peak_speed") & (pl.col("b") == "forty"))
    tn = ps.filter((pl.col("a") == "peak_speed") & (pl.col("b") == "ten_yd_split"))
    wt = ps.filter((pl.col("a") == "peak_speed") & (pl.col("b") == "combine_weight"))
    res["combine_measurement"] = {
        "source": RUNS["forty_reliability"] + " ; " + RUNS["phase3"] + "/predictor_structure.parquet",
        "reliability": [dict(pos=r["pos"], n=r["n"], icc_single=r["icc31"], icc_single_ci95=[r["icc31_lo"], r["icc31_hi"]],
                             best_of_2=r["icc31_best_of_2_sb"]) for r in rel.iter_rows(named=True)],
        "vs_forty": [dict(pos=r["pos"], n=r["n"], pearson=r["pearson"], unique_var=r["unique_var_a"]) for r in fx.iter_rows(named=True)],
        "vs_ten_yd_split": [dict(pos=r["pos"], n=r["n"], spearman=r["spearman"]) for r in tn.iter_rows(named=True)],
        "vs_weight": [dict(pos=r["pos"], n=r["n"], spearman=r["spearman"]) for r in wt.iter_rows(named=True)],
    }

    # ---- speed demand + outcome reliability (outcome-blind) --------------------------------------------------
    sd = pl.read_parquet(p3 / "speed_demand.parquet")
    res["speed_demand"] = {"source": RUNS["phase3"] + "/speed_demand.parquet",
                           "definition": "share of a position-context's plays whose max speed is >= 90 % of the player's own top-5 mean",
                           "rows": sd.to_dicts()}
    orl = pl.read_parquet(p3 / "outcome_reliability.parquet")
    keep = ["separation_at_pass_forward", "separation_deep", "separation_short", "target_f", "vmax_prepass"]
    orl = orl.filter((pl.col("pos") == "WR") & pl.col("outcome").is_in(keep))
    res["outcome_reliability_wr"] = {"source": RUNS["phase3"] + "/outcome_reliability.parquet",
                                     "rows": orl.select("outcome", "kind", "players_eligible", "split_half_sb", "sb_lo", "sb_hi", "season_rho").to_dicts()}
    # ---- reproducibility targets for the public notebook (counts and combine-only checksums) -------------
    pred = pl.read_parquet(ROOT / "data/interim/confirmatory_join" / jv["run"] / "predictors.parquet")
    psum = (pred.filter(pl.col("valid_tracked_40")).group_by("pos")
            .agg(pl.len().alias("n_valid"), pl.col("x_peak").mean().alias("x_peak_mean"), pl.col("x_peak").sum().alias("x_peak_sum"))
            .sort("pos").to_dicts())
    res["repro_targets"] = {
        "source": RUNS["join"] + " + data/interim/confirmatory_join/<run>/predictors.parquet (combine-only summary)",
        "play_exclusions": jv["play_exclusions"], "identity": jv["identity"],
        "matching_by_position": jv["matching_by_position"],
        "frames": {k: {kk: v[kk] for kk in ("eligible_all", "eligible_h1", "eligible_h2", "rows_after_join", "players",
                                            "plays_by_context", "plays_by_depth") if kk in v}
                   for k, v in jv["frames"].items()},
        "predictor_summary": psum, "predictor_rows": pred.height,
        "tracked_40_attempts": json.loads((EXP / "forty_reliability/20261121T134306Z/summary.json").read_text()),
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    print("wrote", OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
