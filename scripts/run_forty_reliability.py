"""Approved deviation D3: combine-only 40-yard test-retest reliability.

Reads ONLY data/interim/combine_tracking.parquet and data/interim/combine_results.parquet.
No NFL game table (tracking, plays, player_play, games, career outcomes) is opened.

Outputs: experiments/forty_reliability/<run>/{attempts.parquet, reliability.parquet, validity.parquet, summary.json}
Usage:  python scripts/run_forty_reliability.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from nfl_bdb.features import forty_reliability as fr  # noqa: E402
from run_real_capacity import forty_fits  # noqa: E402  (combine-only mono-exponential fits: registered validity rule)

OUT = ROOT / "experiments/forty_reliability"
POS = ["WR", "TE", "DB", "DL", "OL"]
SEED = 4040


def main():
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); out = OUT / run; out.mkdir(parents=True, exist_ok=True)
    ct = pl.read_parquet(ROOT / "data/interim/combine_tracking.parquet").filter(
        (pl.col("entity_type") == "PLAYER") & (pl.col("drill_type") == "FORTY_YARD_DASH"))
    cr = pl.read_parquet(ROOT / "data/interim/combine_results.parquet").select("nfl_id", pl.col("combine_position").alias("pos"), "forty", "ten_yd_split")
    att = fr.forty_attempt_table(ct)
    fits = forty_fits().select("event_id", "nfl_id", "attempt", "r2")
    att = (att.join(fits, on=["event_id", "nfl_id", "attempt"], how="left").join(cr.select("nfl_id", "pos"), on="nfl_id", how="left")
           .with_columns(valid_peak=(pl.col("r2") > 0.95) & (pl.col("vpeak") <= fr.SPEED_SPIKE),
                         no_spike=pl.col("vpeak") <= fr.SPEED_SPIKE))
    att.write_parquet(out / "attempts.parquet")

    rows = []
    measures = {"vpeak (registered valid attempts)": ("vpeak", "valid_peak"), "t40": ("t40", "no_spike"),
                "t10": ("t10", "no_spike"), "fly_10_35": ("fly_10_35", "no_spike")}
    for mlabel, (col, flag) in measures.items():
        a = att.filter(pl.col(flag) & pl.col(col).is_not_null() & pl.col(col).is_not_nan()).sort("nfl_id", "attempt")
        first2 = a.group_by("nfl_id", maintain_order=True).head(2)
        pair = first2.group_by("nfl_id", "pos", maintain_order=True).agg(pl.col(col).alias("v")).filter(pl.col("v").list.len() == 2)
        for p in ["ALL"] + POS:
            q = pair if p == "ALL" else pair.filter(pl.col("pos") == p)
            if q.height < 10:
                continue
            A = np.array([v[0] for v in q["v"]]); Bv = np.array([v[1] for v in q["v"]])
            st = fr.icc(A, Bv)
            lo, hi = fr.boot_ci(A, Bv, "icc31", seed=SEED)
            rows.append(dict(measure=mlabel, pos=p, **st, icc31_lo=lo, icc31_hi=hi,
                             icc31_best_of_2_sb=fr.spearman_brown(st["icc31"])))
    rel = pl.DataFrame(rows); rel.write_parquet(out / "reliability.parquet")

    # concurrent validity: best tracked attempt vs official electronic times (combine results)
    best = (att.filter(pl.col("no_spike")).group_by("nfl_id", "pos")
            .agg(pl.col("t40").min().alias("t40_best"), pl.col("t10").min().alias("t10_best"), pl.len().alias("n_att"))
            .join(cr.select("nfl_id", "forty", "ten_yd_split"), on="nfl_id"))
    vrows = []
    for p in ["ALL"] + POS:
        q = best if p == "ALL" else best.filter(pl.col("pos") == p)
        for trk, off in (("t40_best", "forty"), ("t10_best", "ten_yd_split")):
            z = q.select(trk, off).drop_nulls().filter(pl.col(trk).is_not_nan())
            if z.height < 10:
                continue
            a, b = z[trk].to_numpy(), z[off].to_numpy()
            vrows.append(dict(pos=p, tracked=trk, official=off, n=z.height, r=float(np.corrcoef(a, b)[0, 1]),
                              mean_official_minus_tracked=float((b - a).mean()), sd_diff=float((b - a).std(ddof=1))))
    val = pl.DataFrame(vrows); val.write_parquet(out / "validity.parquet")

    # official 40 vs the registered predictor x (max over valid attempts) and the best flying split, within position.
    # Classical-error bound (independent errors): latent corr = r_obs / sqrt(R_F R_x) <= 1  =>  R_F >= r_obs^2 / R_x,
    # with R_x(registered x) approximated by the Spearman-Brown best-of-2 ICC of single-attempt peaks.
    px = (att.filter(pl.col("valid_peak")).group_by("nfl_id").agg(pl.col("vpeak").max().alias("x_peak"))
          .join(att.filter(pl.col("no_spike")).group_by("nfl_id").agg(pl.col("fly_10_35").min().alias("fly_best")), on="nfl_id", how="left")
          .join(cr, on="nfl_id"))
    brows = []
    for p in ["ALL"] + POS:
        q = (px if p == "ALL" else px.filter(pl.col("pos") == p)).drop_nulls(["x_peak", "forty"])
        rx = rel.filter((pl.col("pos") == p) & pl.col("measure").str.starts_with("vpeak"))["icc31_best_of_2_sb"][0]
        r_xf = float(np.corrcoef(q["x_peak"], -q["forty"])[0, 1])
        qf = q.drop_nulls("fly_best").filter(pl.col("fly_best").is_not_nan())
        brows.append(dict(pos=p, n=q.height, r_peak_vs_official40=r_xf, R_x_best_of_2=rx, R_F_lower_bound=r_xf ** 2 / rx,
                          r_fly_vs_official40=float(np.corrcoef(-qf["fly_best"], -qf["forty"])[0, 1])))
    bnd = pl.DataFrame(brows); bnd.write_parquet(out / "rf_bound.parquet")

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    json.dump(dict(run=run, code_commit=commit, seed=SEED, inputs=["combine_tracking", "combine_results"],
                   n_attempts=att.height, n_players=att["nfl_id"].n_unique(),
                   attempts_per_player=att.group_by("nfl_id").len()["len"].value_counts().sort("len").to_dicts()),
              open(out / "summary.json", "w"), indent=1)
    (OUT / "LATEST").write_text(run)
    pl.Config.set_tbl_rows(60); pl.Config.set_tbl_cols(20); pl.Config.set_tbl_width_chars(220)
    print(rel.with_columns(pl.col(pl.Float64).round(3))); print(val.with_columns(pl.col(pl.Float64).round(3))); print(bnd.with_columns(pl.col(pl.Float64).round(3))); print("->", out)


if __name__ == "__main__":
    main()
