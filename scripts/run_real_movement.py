"""Phase 2, Experiments 2 & 3: braking and lateral (turning) estimation from 10 Hz game tracking.
No performance outcomes are used; player_play supplies *context* only (play type, route type).

Outputs (experiments/real_movement/<run_id>/):
  frame_agreement.parquet     estimator agreement / implausibility per position x variant
  speed_bins.parquet          per position x variant x speed bin: quantiles of braking, a_n, curvature
  decomposition.parquet       provided |a| vs (a_t, a_n) during braking, by curvature class
  player_measures.parquet     long table: nfl_id x scope x variant x context x measure
  exposure_curve.parquet      measures on random play subsets (censoring of envelopes)
  combine_movement.parquet    per player braking / lateral envelopes in combine agility + skill drills
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")
from nfl_bdb.data.game_kinematics import heading_lateral, load_game_sequences, sg_kinematics, speed_derivatives  # noqa: E402
from nfl_bdb.data.io import load  # noqa: E402

CFG = dict(min_speed_brake=2.0, lat_speed=(3.0, 8.0), straight_kappa=0.05, turn_kappa=0.2,
           implausible_at=12.0, implausible_an=15.0, q=0.99, noise_levels=(0.01, 0.02), seed=7)
BREAK = ["IN", "OUT", "HITCH", "CORNER", "POST", "SLANT", "CROSS", "ANGLE", "WHEEL"]


def main():
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "experiments" / "real_movement" / run_id
    out.mkdir(parents=True, exist_ok=True)
    json.dump(CFG, open(out / "config.json", "w"), indent=1)
    t0 = time.time(); rng = np.random.default_rng(CFG["seed"])
    pos = load("combine_results", lazy=False).select("nfl_id", pl.col("combine_position").alias("pos"))
    pp = load("player_play", lazy=False).select("game_id", "play_id", "nfl_id", "pass_result", "route_ran")
    # global game-parity halves (alternate each player's games in date order across all seasons)
    games = load("games").filter(pl.col("season_type").is_in(["REG", "POST"])).select("game_id")
    pg = pl.concat([load(f"game_tracking_{y}").select("nfl_id", "game_id").unique().join(games, on="game_id").collect() for y in (2023, 2024, 2025)])
    halves = pg.unique().sort("nfl_id", "game_id").with_columns((pl.int_range(pl.len()).over("nfl_id") % 2).alias("half"))
    frame_dir = ROOT / "data" / "interim" / "real_movement_frames"; frame_dir.mkdir(parents=True, exist_ok=True)
    reps = {}
    for yr in (2023, 2024, 2025):
        df, rep = load_game_sequences(seasons=(yr,)); reps[yr] = rep
        df = df.with_columns((pl.col("seq") + yr * 10_000_000).alias("seq"))
        snap = df.filter(pl.col("event") == "ball_snap").group_by("seq").agg(pl.col("time").min().alias("t_snap"))
        df = df.join(snap, on="seq").sort("seq", "time")
        seq = df["seq"].to_numpy(); x = df["x"].to_numpy(); y = df["y"].to_numpy(); s = df["s"].to_numpy()
        cols = {}
        for w in (5, 7, 9):
            k = sg_kinematics(x, y, seq, w)
            cols[f"at_pos{w}"] = k["a_t"].astype(np.float32); cols[f"an_pos{w}"] = k["a_n"].astype(np.float32)
            if w == 7:
                cols["speed7"] = k["speed"].astype(np.float32); cols["kappa7"] = k["curvature"].astype(np.float32)
            del k
        d_diff, d_sg = speed_derivatives(s, seq, window=7)
        cols["at_sdiff"] = d_diff.astype(np.float32); cols["at_ssg7"] = d_sg.astype(np.float32)
        cols["an_dir"] = heading_lateral(s, df["dir"].to_numpy(), seq).astype(np.float32)
        for sig in CFG["noise_levels"]:
            k = sg_kinematics(x + rng.normal(0, sig, len(x)), y + rng.normal(0, sig, len(y)), seq, 7)
            cols[f"at_noise{sig}"] = k["a_t"].astype(np.float32); cols[f"an_noise{sig}"] = k["a_n"].astype(np.float32)
            del k
        df = (df.select("seq", "time", "t_snap", "nfl_id", "game_id", "play_id", "season", "x", "y", pl.col("a").cast(pl.Float32))
              .with_columns([pl.Series(kk, vv) for kk, vv in cols.items()]).filter(pl.col("time") >= pl.col("t_snap")))
        del cols, x, y, s, seq
        d5 = df.select("seq", "time", "x", "y").with_columns(pl.int_range(pl.len()).over("seq").alias("i")).filter(pl.col("i") % 2 == 0)
        k5 = sg_kinematics(d5["x"].to_numpy(), d5["y"].to_numpy(), d5["seq"].to_numpy(), 5, fs=5.0)
        d5 = d5.select("seq", "time").with_columns(pl.Series("at_5hz", k5["a_t"].astype(np.float32)), pl.Series("an_5hz", k5["a_n"].astype(np.float32)))
        df = (df.join(d5, on=["seq", "time"], how="left").drop("x", "y", "t_snap")
              .join(pos, on="nfl_id").join(pp, on=["game_id", "play_id", "nfl_id"], how="left")
              .with_columns(pl.when(pl.col("pass_result").is_null()).then(pl.lit("unknown"))
                            .when(pl.col("pass_result") == "").then(pl.lit("run")).otherwise(pl.lit("pass")).alias("play_type"),
                            pl.when(pl.col("route_ran") == "GO").then(pl.lit("vertical"))
                            .when(pl.col("route_ran").is_in(BREAK)).then(pl.lit("breaking"))
                            .when(pl.col("route_ran").is_in(["FLAT", "SCREEN"])).then(pl.lit("flat_screen"))
                            .otherwise(pl.lit(None)).alias("route_group"))
              .drop("pass_result", "route_ran").join(halves, on=["nfl_id", "game_id"]))
        df.write_parquet(frame_dir / f"season_{yr}.parquet")
        print("season", yr, df.height, "frames", round(time.time() - t0), "s", flush=True)
        del df, d5, k5
    json.dump(reps, open(out / "exclusions.json", "w"), indent=1, default=str)
    LF = pl.scan_parquet(str(frame_dir / "season_*.parquet"))
    df = LF.collect()   # reduced float32 frame table (post-snap only)
    print("combined frames", df.height, round(time.time() - t0), "s", flush=True)

    # ---------------- frame-level agreement & implausibility
    AT = ["at_pos5", "at_pos7", "at_pos9", "at_sdiff", "at_ssg7", "at_noise0.01", "at_noise0.02", "at_5hz"]
    AN = ["an_pos5", "an_pos7", "an_pos9", "an_dir", "an_noise0.01", "an_noise0.02", "an_5hz"]
    rows = []
    for p in df["pos"].unique().to_list():
        q = df.filter(pl.col("pos") == p)
        for c in AT:
            v = q[c].to_numpy(); ok = np.isfinite(v) & np.isfinite(q["at_pos7"].to_numpy())
            rows.append(dict(pos=p, variant=c, kind="a_t", n=int(ok.sum()),
                             corr_with_pos7=float(np.corrcoef(v[ok], q["at_pos7"].to_numpy()[ok])[0, 1]),
                             frac_implausible=float(np.mean(np.abs(v[ok]) > CFG["implausible_at"])),
                             p999_brake=float(np.quantile(-v[ok], 0.999)), p99_brake=float(np.quantile(-v[ok], 0.99))))
        for c in AN:
            v = q[c].to_numpy(); ok = np.isfinite(v) & np.isfinite(q["an_pos7"].to_numpy())
            rows.append(dict(pos=p, variant=c, kind="a_n", n=int(ok.sum()),
                             corr_with_pos7=float(np.corrcoef(v[ok], q["an_pos7"].to_numpy()[ok])[0, 1]),
                             frac_implausible=float(np.mean(v[ok] > CFG["implausible_an"])),
                             p999_brake=float(np.quantile(v[ok], 0.999)), p99_brake=float(np.quantile(v[ok], 0.99))))
    pl.DataFrame(rows).write_parquet(out / "frame_agreement.parquet")

    # ---------------- speed bins (pooled by position)
    sb = (df.filter(pl.col("speed7").is_finite())
          .with_columns((pl.col("speed7") * 2).floor().truediv(2).clip(0, 10).alias("v_bin"))
          .group_by("pos", "v_bin").agg(
              pl.len().alias("n"),
              *[(-pl.col(c)).quantile(qq).alias(f"brake_{c}_q{int(qq*1000)}") for c in ("at_pos7", "at_ssg7") for qq in (0.5, 0.9, 0.99, 0.999)],
              *[pl.col(c).quantile(qq).alias(f"{c}_q{int(qq*1000)}") for c in ("an_pos7", "an_dir", "kappa7") for qq in (0.5, 0.9, 0.99, 0.999)]))
    sb.sort("pos", "v_bin").write_parquet(out / "speed_bins.parquet")

    # ---------------- decomposition of provided |a| during braking
    dec = (df.filter(pl.col("at_pos7").is_finite() & (pl.col("at_pos7") < -3) & (pl.col("speed7") >= 2))
           .with_columns(pl.when(pl.col("kappa7") < CFG["straight_kappa"]).then(pl.lit("straight"))
                         .when(pl.col("kappa7") < CFG["turn_kappa"]).then(pl.lit("moderate")).otherwise(pl.lit("sharp")).alias("kclass"),
                         (pl.col("at_pos7") ** 2 + pl.col("an_pos7") ** 2).sqrt().alias("a_vec7"))
           .group_by("pos", "kclass").agg(pl.len().alias("n"), pl.col("a").median().alias("provided_a_median"),
                                         (-pl.col("at_pos7")).median().alias("braking_median"), pl.col("an_pos7").median().alias("an_median"),
                                         (pl.col("an_pos7") ** 2 / (pl.col("an_pos7") ** 2 + pl.col("at_pos7") ** 2)).median().alias("share_a2_from_turning"),
                                         pl.corr("a", "a_vec7").alias("corr_provided_a_vs_vec7")))
    dec.sort("pos", "kclass").write_parquet(out / "decomposition.parquet")

    # ---------------- player-level measures
    def measures(frame: pl.DataFrame, keys, at_c, an_c):
        brake_ok = pl.col(at_c).is_finite() & (pl.col("speed7") >= CFG["min_speed_brake"])
        lat_ok = pl.col(an_c).is_finite() & pl.col("speed7").is_between(*CFG["lat_speed"])
        return frame.group_by(keys).agg(
            pl.col("seq").n_unique().alias("n_plays"),
            (-pl.col(at_c)).filter(brake_ok).quantile(CFG["q"]).alias("D99"),
            (-pl.col(at_c)).filter(brake_ok).max().alias("Dmax"),
            (-pl.col(at_c)).filter(brake_ok & (pl.col("kappa7") < CFG["straight_kappa"])).quantile(CFG["q"]).alias("D99_straight"),
            (-pl.col(at_c)).filter(brake_ok & (pl.col("kappa7") >= CFG["turn_kappa"])).quantile(CFG["q"]).alias("D99_turn"),
            pl.col(an_c).filter(lat_ok).quantile(CFG["q"]).alias("C99"),
            pl.col(an_c).filter(lat_ok).max().alias("Cmax"),
            *[pl.col("kappa7").filter(pl.col("speed7").is_between(a, a + 2)).quantile(CFG["q"]).alias(f"kappa99_v{a}_{a+2}") for a in (2, 4, 6)])

    pm = []
    variants = [("pos7", "at_pos7", "an_pos7"), ("pos5", "at_pos5", "an_pos5"), ("pos9", "at_pos9", "an_pos9"),
                ("speed_sg7", "at_ssg7", "an_dir"), ("speed_diff", "at_sdiff", "an_dir"), ("noise0.01", "at_noise0.01", "an_noise0.01"),
                ("noise0.02", "at_noise0.02", "an_noise0.02"), ("5hz", "at_5hz", "an_5hz")]
    for vname, atc, anc in variants:
        for scope, keys in (("all", ["nfl_id"]), ("half", ["nfl_id", "half"]), ("season", ["nfl_id", "season"])):
            m = measures(df, keys, atc, anc).with_columns(pl.lit(vname).alias("variant"), pl.lit("all_plays").alias("context"))
            m = m.with_columns((pl.lit(scope + "_") + (pl.col(keys[1]).cast(pl.Utf8) if len(keys) > 1 else pl.lit(""))).alias("scope"))
            pm.append(m.drop([c for c in keys[1:]]))
        print("variant", vname, round(time.time() - t0), "s", flush=True)
    for ctx_col in ("play_type", "route_group"):
        for scope, keys in (("all", ["nfl_id", ctx_col]), ("half", ["nfl_id", ctx_col, "half"])):
            m = measures(df.filter(pl.col(ctx_col).is_not_null()), keys, "at_pos7", "an_pos7")
            m = m.with_columns(pl.lit("pos7").alias("variant"), (pl.lit(ctx_col + "=") + pl.col(ctx_col)).alias("context"),
                               (pl.lit(scope + "_") + (pl.col("half").cast(pl.Utf8) if scope == "half" else pl.lit(""))).alias("scope"))
            pm.append(m.drop([c for c in keys[1:]]))
    PM = pl.concat(pm, how="diagonal_relaxed").join(pos, on="nfl_id")
    PM.write_parquet(out / "player_measures.parquet")

    # ---------------- exposure subsampling (players with >= 300 plays)
    big = PM.filter((pl.col("scope") == "all_") & (pl.col("variant") == "pos7") & (pl.col("context") == "all_plays") & (pl.col("n_plays") >= 300))["nfl_id"].to_list()
    sub = df.filter(pl.col("nfl_id").is_in(big)).select("nfl_id", "seq", "speed7", "kappa7", "at_pos7", "an_pos7")
    rows = []
    for nid, gdf in sub.group_by("nfl_id"):
        plays = gdf["seq"].unique().to_numpy()
        for k in (10, 25, 50, 100, 200, len(plays)):
            for r in range(5 if k < len(plays) else 1):
                pick = rng.choice(plays, size=min(k, len(plays)), replace=False)
                q = measures(gdf.filter(pl.col("seq").is_in(pick)), ["nfl_id"], "at_pos7", "an_pos7")
                rows.append(dict(nfl_id=nid[0], k=int(k) if k < len(plays) else -1, rep=r, D99=q["D99"][0], C99=q["C99"][0], Dmax=q["Dmax"][0], n_total=len(plays)))
    pl.DataFrame(rows).join(pos, on="nfl_id").write_parquet(out / "exposure_curve.parquet")
    del df, sub
    print("player measures + exposure", round(time.time() - t0), "s", flush=True)

    # ---------------- combine movement (agility + skill drills), SG7
    ct = load("combine_tracking", lazy=False).filter(pl.col("entity_type") == "PLAYER").sort("event_id", "time")
    eid = ct["event_id"].to_numpy(); _, sq = np.unique(eid, return_inverse=True)
    k = sg_kinematics(ct["x"].to_numpy(), ct["y"].to_numpy(), sq, 7)
    ct = ct.with_columns(pl.Series("at7", k["a_t"]), pl.Series("an7", k["a_n"]), pl.Series("speed7", k["speed"]), pl.Series("kappa7", k["curvature"]))
    cm = ct.filter(pl.col("drill_type") != "FORTY_YARD_DASH").with_columns(
        pl.when(pl.col("drill_type").is_in(["THREE_CONE_DRILL", "SHORT_SHUTTLE"])).then(pl.lit("agility")).otherwise(pl.lit("skill")).alias("family"))
    cm = cm.group_by("nfl_id", "family").agg(
        (-pl.col("at7")).filter(pl.col("at7").is_finite() & (pl.col("speed7") >= 2)).quantile(0.99).alias("D99_combine"),
        (-pl.col("at7")).filter(pl.col("at7").is_finite() & (pl.col("speed7") >= 2)).max().alias("Dmax_combine"),
        pl.col("an7").filter(pl.col("an7").is_finite() & pl.col("speed7").is_between(3, 8)).quantile(0.99).alias("C99_combine"),
        pl.col("event_id").n_unique().alias("n_attempts"))
    cm.write_parquet(out / "combine_movement.parquet")
    (ROOT / "experiments" / "real_movement" / "LATEST").write_text(run_id)
    print("done", out, round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
