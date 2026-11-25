"""Phase 14: position-specific Combine skill-drill screening (data and measurement feasibility only).

No predictive model, no combine-feature x outcome association. The game side is used only to COUNT
eligible regular-season plays per player (outcome populations); no outcome value is aggregated.

Outputs: data/interim/phase14_skill/<run>/ (player/attempt level, git-ignored) and
experiments/phase14_skill/<run>/ (aggregates, git-ignored).
Usage: python scripts/run_phase14_skill_screening.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl
from scipy.stats import mannwhitneyu, spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nfl_bdb.evaluation.repeatability import boot_two_attempt, centre_by_group, two_attempt_stats  # noqa: E402
from nfl_bdb.features.skill_drills import ALIASES, ball_phases, curve_metrics, descriptors, harmonise, kinematics  # noqa: E402

INTERIM = ROOT / "data" / "interim"
SEED = 1414
B = 1000
WINDOWS = (5, 7, 9)
DESC = ["duration", "path_length", "peak_speed", "mean_speed_moving", "total_heading_change_deg", "a_n_p95",
        "a_t_p95", "decel_p05", "extent_minor", "n_axis_reversals"]
COMBINE = ["forty", "ten_yd_split", "three_cone", "short_shuttle"]
POS_OF = {"SKILL_DRILLS_WR": "WR", "SKILL_DRILLS_TE": "TE", "SKILL_DRILLS_OL": "OL", "SKILL_DRILLS_DL": "DL",
          "SKILL_DRILLS_DB": "DB", "SKILL_DRILLS_LB": "DL"}


def describe(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 2:
        return dict(n=int(len(x)))
    q = np.percentile(x, [5, 50, 95])
    return dict(n=int(len(x)), mean=float(x.mean()), sd=float(x.std(ddof=1)), p05=q[0], median=q[1], p95=q[2])


def pair_rel(df, col, b=B):
    d = df.filter(pl.col(col).is_not_null() & pl.col(col).is_not_nan()).sort("nfl_id", "order")
    g = d.group_by("nfl_id", maintain_order=True).head(2).group_by("nfl_id", maintain_order=True).agg(pl.col(col), pl.col("draft_year").first()).filter(pl.col(col).list.len() == 2)
    out = dict(n_pairs=g.height)
    if g.height < 10:
        return out
    a = np.array([v[0] for v in g[col].to_list()]); c = np.array([v[1] for v in g[col].to_list()])
    if np.std(np.r_[a, c]) == 0:
        return out
    st = two_attempt_stats(a, c); ci = boot_two_attempt(a, c, None, B=b, seed=SEED)
    yr = np.array(g["draft_year"].to_list())
    if len(set(yr)) > 1:
        ay, cy = centre_by_group(a, c, yr); sty = two_attempt_stats(ay, cy)
        ciy = boot_two_attempt(a, c, yr, stats=("icc31",), B=b, seed=SEED)
        out.update(icc31_year_centred=sty["icc31"], icc31_year_centred_lo=ciy["icc31"][0], icc31_year_centred_hi=ciy["icc31"][1])
    out.update(icc31=st["icc31"], icc31_lo=ci["icc31"][0], icc31_hi=ci["icc31"][1], icc21=st["icc21"],
               spearman=st["spearman"], spearman_lo=ci["spearman"][0], spearman_hi=ci["spearman"][1],
               te=st["te"], te_pct=st["te_pct"], mean_diff=st["mean_diff"])
    return out


def main():
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dout = INTERIM / "phase14_skill" / run; eout = ROOT / "experiments" / "phase14_skill" / run
    dout.mkdir(parents=True); eout.mkdir(parents=True); t0 = time.time()
    ct = pl.read_parquet(INTERIM / "combine_tracking.parquet").filter(pl.col("drill_type").str.starts_with("SKILL")).sort("event_id", "time")
    cr = pl.read_parquet(INTERIM / "combine_results.parquet").select("nfl_id", pl.col("combine_position").alias("pos"), "draft_year", *COMBINE)
    ct = ct.with_columns(pl.struct("drill_type", "drill_name").map_elements(lambda r: harmonise(r["drill_type"], r["drill_name"]),
                                                                           return_dtype=pl.Utf8).alias("drill"))
    P = ct.filter(pl.col("entity_type") == "PLAYER"); Bl = ct.filter(pl.col("entity_type") == "BALL")
    summary = dict(run=run, aliases={f"{k[0]}/{k[1]}": v for k, v in ALIASES.items()})

    # ---------------- attempt table + descriptors ----------------
    rows = []
    for (eid,), g in P.group_by(["event_id"], maintain_order=True):
        dts = np.diff(g["time"].dt.epoch("ms").to_numpy())
        base = dict(event_id=eid, nfl_id=int(g["nfl_id"][0]), drill_type=g["drill_type"][0], drill_name=g["drill_name"][0],
                    drill=g["drill"][0], draft_year=int(g["draft_year"][0]), attempt=int(g["attempt"][0]), t0=g["time"][0],
                    n_gap_anomalies=int((dts != 100).sum()), max_gap_ms=int(dts.max()) if len(dts) else 0,
                    has_ball=False, s_over_12_5=int((g["s"] > 12.5).sum()))
        x, y = g["x"].to_numpy(), g["y"].to_numpy()
        for w in WINDOWS:
            dsc = descriptors(x, y, window=w)
            row = dict(base, window=w, **{k: dsc.get(k, np.nan) for k in ["ok", "n_frames"] + DESC +
                                          ["net_displacement", "extent_major", "start_speed", "end_speed", "signed_heading_change_deg"]})
            if g["drill"][0] in ("RUN_THE_HOOP_DRILL", "PASS_RUSH_DRILL", "BOX_DRILL"):
                row.update({f"curve_{k}": v for k, v in curve_metrics(x, y, window=w).items()})
            if g["drill"][0] == "GAUNTLET_DRILL":
                sp = kinematics(x, y, w)["speed"]; thr = 0.8 * sp.max(); on = np.flatnonzero(sp >= thr)
                seg = sp[on[0]:on[-1] + 1] if len(on) else sp[:0]
                row.update(gauntlet_steady_speed=float(np.median(seg)) if len(seg) >= 5 else np.nan,
                           gauntlet_speed_cv=float(seg.std() / seg.mean()) if len(seg) >= 5 else np.nan,
                           gauntlet_min_over_peak=float(seg.min() / sp.max()) if len(seg) >= 5 else np.nan,
                           gauntlet_steady_duration=len(seg) / 10.0)
            rows.append(row)
    A = pl.DataFrame(rows, infer_schema_length=None).join(cr.select("nfl_id", "pos"), on="nfl_id", how="left")
    A = A.sort("nfl_id", "drill_type", "drill", "t0").with_columns(pl.int_range(pl.len()).over("nfl_id", "drill_type", "drill", "window").alias("order"))
    ball_ev = set(Bl["event_id"].unique().to_list())
    A = A.with_columns(pl.col("event_id").is_in(list(ball_ev)).alias("has_ball"))
    A.write_parquet(dout / "attempts.parquet")
    A7 = A.filter(pl.col("window") == 7)

    # ---------------- Task A inventory ----------------
    inv = (A7.group_by("drill_type", "drill").agg(
        pl.col("drill_name").unique().sort().alias("names"), pl.col("draft_year").unique().sort().alias("years"),
        pl.len().alias("attempts"), pl.col("nfl_id").n_unique().alias("athletes"),
        pl.col("n_frames").median().alias("frames_median"), pl.col("n_frames").quantile(0.05).alias("frames_p05"),
        pl.col("n_frames").quantile(0.95).alias("frames_p95"), pl.col("duration").median().alias("duration_median"),
        (pl.col("start_speed") >= 1.0).mean().alias("start_moving_share"), (pl.col("end_speed") >= 1.0).mean().alias("end_moving_share"),
        (~pl.col("ok").fill_null(False)).sum().alias("too_short"), (pl.col("n_gap_anomalies") > 0).sum().alias("attempts_with_gap_anomaly"),
        pl.col("s_over_12_5").sum().alias("frames_s_over_12_5"), pl.col("has_ball").sum().alias("attempts_with_ball"),
        pl.col("pos").unique().sort().alias("positions"))
        .sort("drill_type", "drill"))
    per = A7.group_by("drill_type", "drill", "nfl_id").agg(pl.len().alias("k"))
    rep = per.group_by("drill_type", "drill").agg(*[(pl.col("k") == i).sum().alias(f"k{i}") for i in (1, 2, 3)], (pl.col("k") >= 4).sum().alias("k4plus"),
                                                  (pl.col("k") >= 2).sum().alias("athletes_2plus"))
    yrs = A7.group_by("drill_type", "drill", "draft_year").agg(pl.len().alias("n")).pivot(index=["drill_type", "drill"], on="draft_year", values="n").fill_null(0)
    yrs = yrs.rename({c: f"attempts_{c}" for c in yrs.columns if c not in ("drill_type", "drill")})
    INV = inv.join(rep, on=["drill_type", "drill"]).join(yrs, on=["drill_type", "drill"])
    INV.with_columns(pl.col("names").list.join("|"), pl.col("years").cast(pl.List(pl.Utf8)).list.join("|"),
                     pl.col("positions").list.join("|")).write_csv(eout / "inventory.csv")
    # position x draft-year per drill family
    PY = A7.group_by("drill_type", "pos", "draft_year").agg(pl.col("nfl_id").n_unique().alias("athletes")).sort("drill_type", "pos", "draft_year")
    PY.write_csv(eout / "position_year.csv")

    # alias geometry check (pre-stated rule: medians of duration, path length and both extents within 15%)
    alias_rows = []
    for (dtp, old), new in ALIASES.items():
        a = A7.filter((pl.col("drill_type") == dtp) & (pl.col("drill_name") == old)); b = A7.filter((pl.col("drill_type") == dtp) & (pl.col("drill_name") == new))
        r = dict(drill_type=dtp, alias=old, canonical=new, n_alias=a.height, n_canonical=b.height)
        ok = True
        for c in ("duration", "path_length", "extent_major", "extent_minor", "peak_speed"):
            ma, mb = a[c].median(), b[c].median(); r[f"{c}_alias"] = ma; r[f"{c}_canonical"] = mb
            r[f"{c}_ratio"] = ma / mb if mb else np.nan
            r[f"{c}_mwu_p"] = float(mannwhitneyu(a[c].drop_nans(), b[c].drop_nans()).pvalue)
            if c != "peak_speed" and abs(ma / mb - 1) > 0.15:
                ok = False
        r["verified"] = ok; alias_rows.append(r)
    ALI = pl.DataFrame(alias_rows); ALI.write_csv(eout / "alias_check.csv")
    # NOT merged: candidates that look related but are different tasks
    rel = []
    for dtp, names in (("SKILL_DRILLS_DL", ["SHORT_ZONE_BREAKS", "SHORT_ZONE_BREAK_FLAT_WHEEL", "SHORT_ZONE_BREAK_FORWARD", "SHORT_ZONE_BREAK_INSIDE"]),
                       ("SKILL_DRILLS_WR", ["POST_CORNER_ROUTE_LEFT", "POST_CORNER_ROUTE_RIGHT"])):
        for nm in names:
            d = A7.filter((pl.col("drill_type") == dtp) & (pl.col("drill_name") == nm))
            rel.append(dict(drill_type=dtp, drill_name=nm, attempts=d.height, years="|".join(map(str, sorted(d["draft_year"].unique().to_list()))),
                            duration=d["duration"].median(), path_length=d["path_length"].median(), extent_major=d["extent_major"].median(),
                            extent_minor=d["extent_minor"].median(), signed_heading_median=d["signed_heading_change_deg"].median()))
    pl.DataFrame(rel).write_csv(eout / "not_merged_check.csv")

    # ---------------- ball linkage + catch phase (Task A/B) ----------------
    J = P.join(Bl.select("event_id", "time", pl.col("x").alias("bx"), pl.col("y").alias("by")), on=["event_id", "time"]).sort("event_id", "time")
    bp = []
    for (eid,), g in J.group_by(["event_id"], maintain_order=True):
        r = ball_phases(g["x"].to_numpy(), g["y"].to_numpy(), g["bx"].to_numpy(), g["by"].to_numpy())
        bp.append(dict(event_id=eid, drill=g["drill"][0], drill_type=g["drill_type"][0], **r))
    BP = pl.DataFrame(bp, infer_schema_length=None)
    pe = P.group_by("event_id").agg(pl.len().alias("np"), pl.col("nfl_id").first().alias("pid"), pl.col("draft_year").first(), pl.col("drill_type").first())
    be = Bl.group_by("event_id").agg(pl.len().alias("nb"), pl.col("nfl_id").first().alias("bid"))
    link = pe.filter(pl.col("drill_type").is_in(["SKILL_DRILLS_WR", "SKILL_DRILLS_TE"])).join(be, on="event_id", how="left")
    summary["ball_linkage"] = dict(
        ball_years=sorted(Bl["draft_year"].unique().to_list()), ball_rows=Bl.height, ball_events=be.height,
        wrte_player_events_by_year={str(y): int(n) for y, n in link.group_by("draft_year").len().sort("draft_year").iter_rows()},
        wrte_2025_events_with_ball=int(link.filter((pl.col("draft_year") == 2025) & pl.col("nb").is_not_null()).height),
        wrte_2025_events=int(link.filter(pl.col("draft_year") == 2025).height),
        ball_events_without_player=int(be.join(pe, on="event_id", how="anti").height),
        ball_nfl_id_equals_player=float((link.drop_nulls("nb")["pid"] == link.drop_nulls("nb")["bid"]).mean()),
        ball_rows_with_matching_player_timestamp=int(J.height),
        catch_phase=dict(contact_found=float((BP["contact"] >= 0).mean()), flight_3plus=float((BP["n_flight"] >= 3).mean()),
                         held=float(BP["held"].mean()), jump_near_contact=float(BP["jump_near_contact"].mean()),
                         any_ball_jump=float((BP["n_ball_jumps"] > 0).mean()), identifiable=float(BP["identifiable"].mean()),
                         n=BP.height, flight_speed_median=float(BP["flight_speed_med"].drop_nans().median())))
    BP.group_by("drill").agg(pl.len().alias("attempts"), (pl.col("contact") >= 0).mean().alias("contact_found"),
                             (pl.col("n_flight") >= 3).mean().alias("flight_3plus"), pl.col("held").mean(), pl.col("jump_near_contact").mean(),
                             (pl.col("n_ball_jumps") > 0).mean().alias("any_jump"), pl.col("identifiable").mean(),
                             pl.col("identifiable").sum().alias("identifiable_n")).sort("drill").write_csv(eout / "ball_phase_by_drill.csv")

    # ---------------- Task C repeatability of generic descriptors (designed repeats) ----------------
    rel_rows = []
    for (dtp, drill), g in A.group_by("drill_type", "drill"):
        g7 = g.filter(pl.col("window") == 7)
        n2 = g7.group_by("nfl_id").len().filter(pl.col("len") >= 2).height
        if n2 < 15:
            continue
        first2 = g7.sort("nfl_id", "order").group_by("nfl_id", maintain_order=True).head(2)
        mirror = first2.group_by("nfl_id").agg(pl.col("signed_heading_change_deg").sign().n_unique().alias("u"), pl.len()).filter(pl.col("len") == 2)
        mir_share = float((mirror["u"] > 1).mean())
        for c in DESC:
            r7 = pair_rel(g7, c)
            row = dict(drill_type=dtp, drill=drill, descriptor=c, athletes_2plus=n2, mirrored_pair_share=mir_share, **r7)
            for w in (5, 9):
                gw = g.filter(pl.col("window") == w)
                row[f"icc31_w{w}"] = pair_rel(gw, c, b=1).get("icc31")   # point estimate only
                m = g7.select("event_id", pl.col(c).alias("a")).join(gw.select("event_id", pl.col(c).alias("b")), on="event_id").drop_nulls().filter(pl.col("a").is_not_nan() & pl.col("b").is_not_nan())
                row[f"rank_w{w}_vs_w7"] = float(spearmanr(m["a"], m["b"]).statistic) if m.height > 5 else np.nan
            rel_rows.append(row)
    REL = pl.DataFrame(rel_rows, infer_schema_length=None); REL.write_csv(eout / "repeatability_generic.csv")

    # ---------------- candidate-specific measures ----------------
    cand = {}
    hoop = A.filter((pl.col("drill") == "RUN_THE_HOOP_DRILL"))
    pr = A.filter((pl.col("drill") == "PASS_RUSH_DRILL") & (pl.col("drill_type") == "SKILL_DRILLS_DL"))
    gaunt = A.filter(pl.col("drill") == "GAUNTLET_DRILL")
    cand_rel = []
    for name, df, cols in (("DL_RUN_THE_HOOP", hoop, ["curve_all_a_n", "curve_all_speed", "curve_all_radius", "curve_left_a_n", "curve_right_a_n"]),
                           ("DL_PASS_RUSH_DRILL", pr, ["curve_all_a_n", "curve_all_speed", "curve_all_radius", "peak_speed", "a_t_p95"]),
                           *[(f"{p}_GAUNTLET", gaunt.filter(pl.col("drill_type") == f"SKILL_DRILLS_{p}"),
                              ["gauntlet_steady_speed", "gauntlet_speed_cv", "gauntlet_min_over_peak", "peak_speed"]) for p in ("WR", "TE", "DB")]):
        for w in WINDOWS:
            dw = df.filter(pl.col("window") == w)
            for c in cols:
                if c not in dw.columns:
                    continue
                r = pair_rel(dw, c, b=B if w == 7 else 200)
                cand_rel.append(dict(candidate=name, measure=c, window=w, attempts=dw.filter(pl.col(c).is_not_null() & pl.col(c).is_not_nan()).height,
                                     athletes=dw.filter(pl.col(c).is_not_null() & pl.col(c).is_not_nan())["nfl_id"].n_unique(), **r,
                                     dist=json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in describe(dw[c]).items()})))
    # hoop: within-attempt left vs right consistency (split-half, NOT test-retest), first attempt per athlete
    h7 = hoop.filter(pl.col("window") == 7).sort("nfl_id", "order").group_by("nfl_id", maintain_order=True).first()
    sh = h7.select("nfl_id", "pos", "curve_left_a_n", "curve_right_a_n", "curve_left_speed", "curve_right_speed").drop_nulls().filter(
        pl.col("curve_left_a_n").is_not_nan() & pl.col("curve_right_a_n").is_not_nan())
    if sh.height >= 10:
        for m in ("a_n", "speed"):
            a, c = sh[f"curve_left_{m}"].to_numpy(), sh[f"curve_right_{m}"].to_numpy()
            st = two_attempt_stats(a, c); ci = boot_two_attempt(a, c, None, B=B, seed=SEED)
            cand_rel.append(dict(candidate="DL_RUN_THE_HOOP", measure=f"left_vs_right_{m} (within-attempt split, not test-retest)", window=7,
                                 attempts=sh.height, athletes=sh.height, n_pairs=sh.height, icc31=st["icc31"], icc31_lo=ci["icc31"][0],
                                 icc31_hi=ci["icc31"][1], icc21=st["icc21"], spearman=st["spearman"], te=st["te"], te_pct=st["te_pct"],
                                 mean_diff=st["mean_diff"]))
    CR = pl.DataFrame(cand_rel, infer_schema_length=None); CR.write_csv(eout / "repeatability_candidates.csv")

    # redundancy with generic combine measures (player means, within the drill's position; descriptive only)
    red = []
    for name, df, cols in (("DL_RUN_THE_HOOP", hoop, ["curve_all_a_n", "curve_all_speed"]), ("DL_PASS_RUSH_DRILL", pr, ["curve_all_a_n", "peak_speed"]),
                           ("WR_GAUNTLET", gaunt.filter(pl.col("drill_type") == "SKILL_DRILLS_WR"), ["gauntlet_steady_speed", "gauntlet_speed_cv"]),
                           ("DB_GAUNTLET", gaunt.filter(pl.col("drill_type") == "SKILL_DRILLS_DB"), ["gauntlet_steady_speed", "gauntlet_speed_cv"])):
        pm = df.filter(pl.col("window") == 7).group_by("nfl_id").agg(*[pl.col(c).filter(pl.col(c).is_not_nan()).mean() for c in cols]).join(cr, on="nfl_id")
        for c in cols:
            for m in COMBINE:
                d = pm.select(c, m).drop_nulls().filter(pl.col(c).is_not_nan())
                if d.height >= 15:
                    red.append(dict(candidate=name, measure=c, combine=m, n=d.height, spearman=float(spearmanr(d[c], d[m]).statistic)))
    pl.DataFrame(red).write_csv(eout / "redundancy_generic.csv")

    # ---------------- cross-route consistency (WR, TE): generalisability across different route drills ----------------
    # NOT test-retest: each route is a different task. Values are z-scored within (route drill x draft year) so route
    # and year/layout differences cannot create agreement. Random split-halves of each athlete's routes; Spearman-Brown.
    route_rows = []
    rng = np.random.default_rng(SEED)
    for dtp, excl in (("SKILL_DRILLS_WR", {"GAUNTLET_DRILL"}), ("SKILL_DRILLS_TE", {"GAUNTLET_DRILL", "BLOCK_EXPLOSION"})):
        R0 = A7.filter((pl.col("drill_type") == dtp) & ~pl.col("drill").is_in(list(excl)) & (pl.col("order") == 0))
        for c in ("mean_speed_moving", "peak_speed", "a_n_p95", "decel_p05", "a_t_p95"):
            z = R0.with_columns(((pl.col(c) - pl.col(c).mean().over("drill", "draft_year")) / pl.col(c).std().over("drill", "draft_year")).alias("z"))
            z = z.filter(pl.col("z").is_not_nan() & pl.col("z").is_not_null())
            per_ath = z.group_by("nfl_id").agg(pl.col("z"), pl.len().alias("k")).filter(pl.col("k") >= 6)
            vals = [np.array(v) for v in per_ath["z"].to_list()]
            if len(vals) < 15:
                continue
            rs = []
            for _ in range(500):
                h1, h2 = [], []
                for v in vals:
                    perm = rng.permutation(len(v)); h = len(v) // 2
                    h1.append(v[perm[:h]].mean()); h2.append(v[perm[h:2 * h]].mean())
                r = spearmanr(h1, h2).statistic; rs.append(2 * r / (1 + r))
            comp = per_ath.with_columns(pl.col("z").list.mean().alias("composite")).join(cr, on="nfl_id")
            red_c = {m: float(spearmanr(*comp.select("composite", m).drop_nulls().to_numpy().T).statistic) for m in COMBINE
                     if comp.select("composite", m).drop_nulls().height >= 15}
            route_rows.append(dict(drill_type=dtp, measure=c, athletes=len(vals), routes_median=float(np.median([len(v) for v in vals])),
                                   split_half_sb_median=float(np.median(rs)), split_half_sb_p025=float(np.percentile(rs, 2.5)),
                                   split_half_sb_p975=float(np.percentile(rs, 97.5)), **{f"composite_vs_{k}": v for k, v in red_c.items()}))
            comp.select("nfl_id", "composite", "k").write_parquet(dout / f"route_composite_{dtp}_{c}.parquet")
    pl.DataFrame(route_rows, infer_schema_length=None).write_csv(eout / "cross_route_consistency.csv")

    # ---------------- Task D outcome-population counts (counts only) ----------------
    games = pl.read_parquet(INTERIM / "games.parquet").select("game_id", "season", "season_type")
    pp = pl.read_parquet(INTERIM / "player_play.parquet", columns=["game_id", "nfl_id", "pass_result", "route_ran", "separation_at_pass_forward",
                                                                  "target", "player_get_off", "pass_rushers_encountered", "coverage_assignment"])
    pp = pp.join(games, on="game_id").filter(pl.col("season_type") == "REG").join(cr.select("nfl_id", "pos"), on="nfl_id", how="inner")
    pp = pp.with_columns((pl.col("pass_result").fill_null("") != "").alias("is_pass"))
    elig = pl.concat([
        pp.filter(pl.col("pos").is_in(["WR", "TE"]) & pl.col("is_pass") & pl.col("route_ran").is_not_null()).group_by("nfl_id").agg(
            pl.len().alias("routes"), pl.col("separation_at_pass_forward").is_not_null().sum().alias("sep_routes"),
            pl.col("season").n_unique().alias("seasons")).with_columns(pl.lit("WR/TE: routes on REG pass plays; separation-defined routes").alias("population")),
        pp.filter((pl.col("pos") == "DL") & pl.col("is_pass") & pl.col("player_get_off").is_not_null()).group_by("nfl_id").agg(
            pl.len().alias("routes"), pl.len().alias("sep_routes"), pl.col("season").n_unique().alias("seasons")).with_columns(pl.lit("DL: REG pass-rush snaps (get-off defined)").alias("population")),
        pp.filter((pl.col("pos") == "OL") & pl.col("is_pass") & pl.col("pass_rushers_encountered").is_not_null()).group_by("nfl_id").agg(
            pl.len().alias("routes"), pl.len().alias("sep_routes"), pl.col("season").n_unique().alias("seasons")).with_columns(pl.lit("OL: REG pass-block snaps").alias("population")),
        pp.filter((pl.col("pos") == "DB") & pl.col("is_pass") & pl.col("coverage_assignment").is_not_null() & ~pl.col("coverage_assignment").is_in(["NO_ASSIGNMENT", "PREVENT"])).group_by("nfl_id").agg(
            pl.len().alias("routes"), pl.len().alias("sep_routes"), pl.col("season").n_unique().alias("seasons")).with_columns(pl.lit("DB: REG coverage snaps (deployment only; no attributable outcome)").alias("population")),
    ], how="diagonal_relaxed").rename({"routes": "eligible_plays", "sep_routes": "outcome_defined_plays"})
    elig.write_parquet(dout / "outcome_population_counts.parquet")
    oc = []
    for (dtp, drill), g in A7.group_by("drill_type", "drill"):
        ids = g.select("nfl_id", "pos").unique()
        j = ids.join(elig, on="nfl_id", how="left").join(cr.select("nfl_id", "draft_year"), on="nfl_id", how="left")
        oc.append(dict(drill_type=dtp, drill=drill, participants=ids.height, any_reg_eligible=int(j["eligible_plays"].is_not_null().sum()),
                       outcome_ge50=int((j["outcome_defined_plays"].fill_null(0) >= 50).sum()), outcome_ge100=int((j["outcome_defined_plays"].fill_null(0) >= 100).sum()),
                       ge100_draft_2023=int(((j["outcome_defined_plays"].fill_null(0) >= 100) & (j["draft_year"] == 2023)).sum()),
                       ge100_draft_2024=int(((j["outcome_defined_plays"].fill_null(0) >= 100) & (j["draft_year"] == 2024)).sum()),
                       ge100_draft_2025=int(((j["outcome_defined_plays"].fill_null(0) >= 100) & (j["draft_year"] == 2025)).sum()),
                       missing_any_reg=int(j["eligible_plays"].is_null().sum())))
    OC = pl.DataFrame(oc).sort("drill_type", "drill"); OC.write_csv(eout / "outcome_counts_by_drill.csv")
    pos_pop = elig.join(cr.select("nfl_id", "pos"), on="nfl_id").group_by("pos").agg(pl.len().alias("players_any"), (pl.col("outcome_defined_plays") >= 100).sum().alias("players_ge100"))
    pos_pop.write_csv(eout / "outcome_population_by_position.csv")

    summary.update(seconds=round(time.time() - t0), n_player_attempts=A7.height, n_ball_attempts=BP.height)
    json.dump(dict(run=run, seed=SEED, B=B, windows=WINDOWS, descriptors=DESC), open(eout / "config.json", "w"), indent=1)
    json.dump(summary, open(eout / "summary.json", "w"), indent=1, default=str)
    (ROOT / "experiments" / "phase14_skill" / "LATEST").write_text(run)
    print(f"done in {time.time() - t0:.0f}s -> {eout}")


if __name__ == "__main__":
    main()
