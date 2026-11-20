"""Phase 2, Experiment 4: CCMT execution cost on real combine 3-cone and short-shuttle attempts.
No performance outcomes are used. Capacities: A0/S0 from the athlete's own combine 40 (best attempt,
mono-exponential fit). Braking D and lateral C are NOT measurable from these drills without circularity,
so several external assumptions are compared (constant grid; position-level game envelopes; player-level
game envelopes). Outputs experiments/real_execution/<run_id>/attempts.parquet (long by variant).
"""
from __future__ import annotations

import json, sys, time, warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")
from nfl_bdb.data.io import load  # noqa: E402
from nfl_bdb.features.change_direction_cost import AthleteLimits, linear_sprint_time, real_drill_segment, segment_time  # noqa: E402


def main():
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "experiments" / "real_execution" / run_id; out.mkdir(parents=True, exist_ok=True)
    cap_run = (ROOT / "experiments/real_capacity/LATEST").read_text().strip()
    mov_run = (ROOT / "experiments/real_movement/LATEST").read_text().strip()
    F = pl.read_parquet(ROOT / f"experiments/real_capacity/{cap_run}/combine_forty_attempts.parquet").drop_nulls("S0")
    best = F.sort("vpeak", descending=True).group_by("nfl_id").first().select("nfl_id", "S0", "A0", "tau", pl.col("vpeak").alias("vpeak40"))
    PM = pl.read_parquet(ROOT / f"experiments/real_movement/{mov_run}/player_measures.parquet").filter(
        (pl.col("scope") == "all_") & (pl.col("variant") == "pos7") & (pl.col("context") == "all_plays"))
    pos_DC = PM.filter(pl.col("n_plays") >= 100).group_by("pos").agg(pl.col("D99").median().alias("D_pos"), pl.col("C99").median().alias("C_pos"))
    ply_DC = PM.filter(pl.col("n_plays") >= 100).select("nfl_id", pl.col("D99").alias("D_ply"), pl.col("C99").alias("C_ply"))
    cr = load("combine_results", lazy=False).select("nfl_id", pl.col("combine_position").alias("pos"), "forty", "ten_yd_split", "three_cone", "short_shuttle")
    info = best.join(cr, on="nfl_id").join(pos_DC, on="pos", how="left").join(ply_DC, on="nfl_id", how="left")
    ct = load("combine_tracking", lazy=False).filter((pl.col("entity_type") == "PLAYER") & pl.col("drill_type").is_in(["THREE_CONE_DRILL", "SHORT_SHUTTLE"])).sort("event_id", "time")
    grid = {f"grid_D{D}_C{C}": (D, C) for D in (5.0, 6.5, 8.0) for C in (5.0, 7.0, 9.0)}
    cfg = dict(windows=(5, 7, 9), onsets=("raw", "extrapolated"), grid=grid, D_C_sources=["grid", "position_game", "player_game"],
               capacity_run=cap_run, movement_run=mov_run)
    json.dump(cfg, open(out / "config.json", "w"), indent=1, default=str)
    rows = []; t0 = time.time()
    infod = {r["nfl_id"]: r for r in info.iter_rows(named=True)}
    for (eid, nid, drill, att), g in ct.group_by(["event_id", "nfl_id", "drill_type", "attempt"]):
        base = dict(event_id=eid, nfl_id=nid, drill=drill, attempt=int(att))
        a = infod.get(nid)
        if a is None:
            rows.append({**base, "status": "no 40 tracking"}); continue
        x, y, s = g["x"].to_numpy(), g["y"].to_numpy(), g["s"].to_numpy()
        for w in cfg["windows"]:
            for onset in cfg["onsets"]:
                for stops in (True, False):
                    if (w != 7 or onset != "raw") and not stops:
                        continue
                    seg = real_drill_segment(x, y, s, window=w, onset=onset, stops=stops)
                    if not seg["ok"]:
                        rows.append({**base, "status": seg["reason"], "window": w, "onset": onset}); continue
                    P, T, L = seg["path"], seg["T_obs"], seg["L"]
                    sprint = AthleteLimits(A0=a["A0"], S0=a["S0"], D=6.5, C=7.0)
                    T_lin = linear_sprint_time(L, sprint)
                    common = {**base, "status": "ok", "window": w, "onset": onset, "stops_modelled": stops, "pos": a["pos"],
                              "T_track": T, "L_path": L, "n_stops": seg["n_stops"], "T_lin": T_lin, "codd": T - T_lin, "codd_pct": 100 * (T - T_lin) / T_lin,
                              "S0": a["S0"], "A0": a["A0"], "forty": a["forty"], "ten_yd_split": a["ten_yd_split"],
                              "official": a["three_cone"] if drill == "THREE_CONE_DRILL" else a["short_shuttle"]}
                    lim_sets = dict(grid)
                    if w == 7 and onset == "raw" and stops:
                        if a["D_pos"] is not None: lim_sets["position_game"] = (a["D_pos"], a["C_pos"])
                        if a["D_ply"] is not None: lim_sets["player_game"] = (a["D_ply"], a["C_ply"])
                        lim_sets["no_lateral_D6.5"] = (6.5, None)
                    else:
                        lim_sets = {"grid_D6.5_C7.0": grid["grid_D6.5_C7.0"]}
                    for name, (D, C) in lim_sets.items():
                        lim = AthleteLimits(A0=a["A0"], S0=a["S0"], D=D, C=C if C else 7.0, lateral=C is not None)
                        Ts = segment_time(P, lim, 0.0)
                        rows.append({**common, "limits": name, "D": D, "C": C, "T_star": Ts, "E": T - Ts, "E_ratio": T / Ts})
    print("attempts processed", round(time.time() - t0), "s")
    pl.DataFrame(rows, infer_schema_length=None).write_parquet(out / "attempts.parquet")
    (ROOT / "experiments" / "real_execution" / "LATEST").write_text(run_id)
    print("done", out)


if __name__ == "__main__":
    main()
