"""Phase 19 synthetic power study (simulation only; criteria in configs/phase19_feasibility_criteria.json).

Reads ONLY design information: per player x context x team-season play COUNTS of the registered H1-WR join
(columns nfl_id, ctx, team_abbr, season; never y), and the number of valid tracked-40 attempts per player.
No outcome value and no predictor-outcome association is read or computed.

Usage: python scripts/run_phase19_power.py
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
from nfl_bdb.simulation.game_speed_incremental import Design, composite_reliability, mde, simulate_cell  # noqa: E402

JOIN = ROOT / "data" / "interim" / "confirmatory_join" / "20261121T135032Z"
CFG = json.loads((ROOT / "configs" / "phase19_feasibility_criteria.json").read_text())


def build_design() -> Design:
    D = pl.read_parquet(JOIN / "h1_WR.parquet", columns=["nfl_id", "ctx", "team_abbr", "season"])   # design only
    D = D.with_columns(pl.concat_str([pl.col("team_abbr"), pl.col("season").cast(pl.Utf8)], separator="_").alias("ts"))
    ids = sorted(D["nfl_id"].unique().to_list()); tss = sorted(D["ts"].unique().to_list())
    pi = {k: i for i, k in enumerate(ids)}; ti = {k: i for i, k in enumerate(tss)}; ci = {"deep": 0, "short": 1}
    cnt = D.group_by("nfl_id", "ctx", "ts").agg(pl.len().alias("k"))
    W = np.zeros((2, len(ids), len(tss))); n = np.zeros((len(ids), 2))
    for nid, ctx, ts, k in cnt.iter_rows():
        W[ci[ctx], pi[nid], ti[ts]] += k; n[pi[nid], ci[ctx]] += k
    W /= n.T[:, :, None]
    pr = pl.read_parquet(JOIN / "predictors.parquet", columns=["nfl_id", "n_valid_attempts"]).filter(pl.col("nfl_id").is_in(ids))
    att = dict(pr.iter_rows())
    R_P = np.array([CFG["calibration_combine_only"]["R_P_best_of_2"] if att[i] >= 2 else CFG["calibration_combine_only"]["R_P_single_attempt"] for i in ids])
    return Design(n=n, W=W, R_P=R_P)


def main():
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "experiments" / "phase19" / run; out.mkdir(parents=True)
    g = CFG["grid"]; rng = np.random.default_rng(g["seed"]); r_obs = abs(CFG["calibration_combine_only"]["r_obs_peak_forty_within_57"])
    des = build_design()
    rel_team, rel_noteam = composite_reliability(des)
    meta = dict(run=run, players=des.P, plays=int(des.n.sum()), plays_deep=int(des.n[:, 0].sum()), plays_short=int(des.n[:, 1].sum()),
                team_seasons=int(des.W.shape[2]), R_P_mean=float(des.R_P.mean()), single_attempt_players=int((des.R_P < 0.9).sum()),
                composite_reliability_with_team=rel_team, composite_reliability_sampling_only=rel_noteam)
    print(meta, flush=True)
    rows = []; t0 = time.time()
    for R_F in g["R_F"]:
        for a in g["a_true_validity_of_40"]:
            for pi in (g["pi_true_partial_of_peak_given_true_40"] if R_F > 0.8 else [0.0]):
                rows.append(dict(block="main", **simulate_cell(des, a=a, pi=pi, R_F=R_F, r_obs=r_obs, reps=g["reps"], rng=rng)))
        print("R_F", R_F, "done", round(time.time() - t0), "s", flush=True)
    ns = g["n_scaling"]
    for n_p in ns["n"]:
        d2 = des if n_p == des.P else des.resample(n_p, rng)
        for pi in ns["pi"]:
            rows.append(dict(block="n_scaling", **simulate_cell(d2, a=ns["a"], pi=pi, R_F=ns["R_F"], r_obs=r_obs, reps=g["reps"], rng=rng, do_cv=False)))
    R = pl.DataFrame(rows, infer_schema_length=None)
    R.write_csv(out / "power_grid.csv")
    M = []
    for (R_F, a), gg in R.filter((pl.col("block") == "main") & (pl.col("R_F") > 0.8)).group_by("R_F", "a", maintain_order=True):
        gg = gg.sort("pi")
        M.append(dict(R_F=R_F, a=a, size_pi0=gg["power"][0], mde=mde(gg["pi"].to_list(), gg["power"].to_list()),
                      power_pi03=float(gg.filter(pl.col("pi") == 0.3)["power"][0]), min_coverage=float(gg["coverage_obs"].min())))
    pl.DataFrame(M).write_csv(out / "mde_summary.csv")
    json.dump(meta, open(out / "meta.json", "w"), indent=1)
    (ROOT / "experiments" / "phase19" / "LATEST").write_text(run)
    print("done", out, round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
