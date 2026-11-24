"""Phase 12: short-shuttle straight-exit acceleration, MEASUREMENT FEASIBILITY ONLY (combine data only).

Inputs: data/interim/combine_tracking.parquet (SHORT_SHUTTLE PLAYER rows), combine_results.parquet, and for
the Task E comparison the git-ignored Phase 11.1 combine-only table
data/interim/phase11_1_c_reacc/<PH111_RUN>/c_turns.parquet (three-cone late-loop speed gain).
No NFL game table, outcome table or confirmatory-join file is opened.

The straightness threshold (15 deg) was fixed from trajectory geometry before any repeatability statistic
was computed: it is the ~99th percentile of the deviation from the drill axis of mid-leg frames
(|u| >= 3 yd/s), median 2.7 deg, 95th 9.7 deg (logged in summary.json under "geometry").

Outputs (git-ignored):
  data/interim/phase12_shuttle_accel/<run>/{attempts,reversals,player_features,athletes}.parquet
  experiments/phase12_shuttle_accel/<run>/config.json, summary.json, aggregate tables
Usage: python scripts/run_shuttle_accel_feasibility.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl
from scipy.stats import fisher_exact, mannwhitneyu, spearmanr, chi2_contingency

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nfl_bdb.evaluation.repeatability import boot_two_attempt, centre_by_group, two_attempt_stats  # noqa: E402
from nfl_bdb.features.shuttle_accel import ShuttleParams, analyse_attempt, deviation_deg, params_dict, with_  # noqa: E402

INTERIM = ROOT / "data" / "interim"
PH111_RUN = "20261124T142408Z"
SEED = 1111
B_REF, B_SENS = 2000, 500
REF = ShuttleParams()
SENS = {"window": [5, 9, 11], "speed_source": ["provided", "provided_sg"], "straight_deg": [10.0, 20.0],
        "start_offset": [1, 2, 3]}
COMBINE = ["short_shuttle", "three_cone", "forty", "ten_yd_split"]
REV_COLS = ["v_entry", "v_min", "v_start", "turn_duration", "heading_change_deg", "gap_min_to_window", "approach_frames",
            "window_max_dev_deg", "window_max_abs_omega", "window_heading_change_deg", "window_straightness",
            "window_lateral_range", "window_normal_share", "leg_peak_in_window", "accel"]


def configs():
    c = {"reference": REF}
    for k, vs in SENS.items():
        for v in vs:
            c[f"{k}={v}"] = with_(REF, **{k: v})
    return c


def describe(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 2:
        return dict(n=int(len(x)))
    q = np.percentile(x, [5, 25, 50, 75, 95])
    return dict(n=int(len(x)), mean=float(x.mean()), sd=float(x.std(ddof=1)), p05=q[0], p25=q[1], median=q[2], p75=q[3], p95=q[4])


def pairs(df, col):
    d = df.filter(pl.col(col).is_not_null() & pl.col(col).is_not_nan()).sort("nfl_id", "order")
    g = d.group_by("nfl_id", maintain_order=True).head(2).group_by("nfl_id", maintain_order=True).agg(pl.col(col), pl.col("pos").first())
    g = g.filter(pl.col(col).list.len() == 2)
    return (np.array([v[0] for v in g[col].to_list()]), np.array([v[1] for v in g[col].to_list()]),
            np.array(g["pos"].to_list()), g["nfl_id"].to_list())


def rel(df, col, B):
    a, b, pos, _ = pairs(df, col)
    out = dict(n_pairs=int(len(a)))
    if len(a) < 8:
        return out
    st = two_attempt_stats(a, b); ci = boot_two_attempt(a, b, None, B=B, seed=SEED)
    ac, bc = centre_by_group(a, b, pos); stc = two_attempt_stats(ac, bc)
    cic = boot_two_attempt(a, b, pos, stats=("icc31",), B=B, seed=SEED)
    out.update(icc31=st["icc31"], icc31_lo=ci["icc31"][0], icc31_hi=ci["icc31"][1], icc21=st["icc21"], icc21_lo=ci["icc21"][0],
               icc21_hi=ci["icc21"][1], spearman=st["spearman"], spearman_lo=ci["spearman"][0], spearman_hi=ci["spearman"][1],
               te=st["te"], te_pct=st["te_pct"], mean_diff=st["mean_diff"], icc31_within_pos=stc["icc31"],
               icc31_within_pos_lo=cic["icc31"][0], icc31_within_pos_hi=cic["icc31"][1])
    for p_ in sorted(set(pos)):
        m = pos == p_
        out[f"n_pairs_{p_}"] = int(m.sum())
        if m.sum() >= 8:
            out[f"icc31_{p_}"] = two_attempt_stats(a[m], b[m])["icc31"]
    return out


def wpos(df, a, b):
    d = df.select("pos", a, b).drop_nulls().filter(pl.col(a).is_not_nan() & pl.col(b).is_not_nan())
    if d.height < 15:
        return dict(n=d.height)
    d = d.with_columns(pl.col(a).rank().alias("_a"), pl.col(b).rank().alias("_b"))
    d = d.with_columns((pl.col("_a") - pl.col("_a").mean().over("pos")).alias("_a"), (pl.col("_b") - pl.col("_b").mean().over("pos")).alias("_b"))
    rng = np.random.default_rng(SEED); x, y = d[a].to_numpy(), d[b].to_numpy(); bs = []
    for _ in range(1000):
        j = rng.integers(0, len(x), len(x)); bs.append(spearmanr(x[j], y[j]).statistic)
    return dict(n=d.height, rho=float(spearmanr(x, y).statistic), lo=float(np.nanpercentile(bs, 2.5)), hi=float(np.nanpercentile(bs, 97.5)),
                rho_within_pos=float(np.corrcoef(d["_a"], d["_b"])[0, 1]))


def within_athlete(df, y, x):
    d = df.filter(pl.col(y).is_not_nan() & pl.col(x).is_not_null()).with_columns(pl.col(x).cast(pl.Float64)).filter(pl.col(x).is_not_nan()).sort("nfl_id", "order")
    g = d.group_by("nfl_id", maintain_order=True).head(2).group_by("nfl_id").agg(pl.col(y), pl.col(x)).filter(pl.col(y).list.len() == 2)
    dy = np.array([v[1] - v[0] for v in g[y].to_list()]); dx = np.array([v[1] - v[0] for v in g[x].to_list()])
    return dict(n=len(dy), rho=float(spearmanr(dy, dx).statistic) if len(dy) > 5 and np.std(dx) > 0 else np.nan)


def residual_rel(df, y, x, B):
    d = df.filter(pl.col(y).is_not_nan() & pl.col(x).is_not_nan())
    P = sorted(d["pos"].unique().to_list())
    X = np.column_stack([np.ones(d.height), d[x].to_numpy()] + [(d["pos"] == p_).cast(int).to_numpy() for p_ in P[1:]])
    beta, *_ = np.linalg.lstsq(X, d[y].to_numpy(), rcond=None); res = d[y].to_numpy() - X @ beta
    r2 = 1 - res.var() / d[y].to_numpy().var()
    return dict(adjusted_for=x, beta=float(beta[1]), r2_with_position=float(r2), **rel(d.with_columns(pl.Series("_res", res)), "_res", B))


def main():
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dout = INTERIM / "phase12_shuttle_accel" / run; eout = ROOT / "experiments" / "phase12_shuttle_accel" / run
    dout.mkdir(parents=True); eout.mkdir(parents=True); t0 = time.time()
    ct = pl.read_parquet(INTERIM / "combine_tracking.parquet").filter(
        (pl.col("drill_type") == "SHORT_SHUTTLE") & (pl.col("entity_type") == "PLAYER")).sort("event_id", "time")
    cr = pl.read_parquet(INTERIM / "combine_results.parquet").select("nfl_id", pl.col("combine_position").alias("pos"), "draft_year", *COMBINE)
    pos_map = dict(cr.select("nfl_id", "pos").iter_rows())

    # ---------------- Task A: raw inventory ----------------
    ev = ct.group_by("event_id", maintain_order=True).agg(
        pl.col("nfl_id").first(), pl.col("attempt").first(), pl.col("time").min().alias("t0"), pl.len().alias("n_frames"),
        pl.col("time").diff().dt.total_milliseconds().drop_nulls().alias("dt_ms"),
        (pl.col("x").max() - pl.col("x").min()).alias("x_range"), (pl.col("y").max() - pl.col("y").min()).alias("y_range"),
        pl.col("s").max().alias("s_max"), pl.col("s").first().alias("s_first"), pl.col("s").last().alias("s_last"))
    ev = ev.sort("nfl_id", "t0").with_columns(pl.int_range(pl.len()).over("nfl_id").alias("order"))
    dts = np.concatenate([np.asarray(v, float) for v in ev["dt_ms"].to_list() if len(v)])
    k_raw = ev.group_by("nfl_id").agg(pl.len().alias("k"))
    geometry_dev = []
    cfgs = configs(); A, R = [], []
    for (eid,), g in ct.group_by(["event_id"], maintain_order=True):
        meta = ev.filter(pl.col("event_id") == eid).row(0, named=True)
        x, y, s = g["x"].to_numpy(), g["y"].to_numpy(), g["s"].to_numpy()
        pl_len = float(np.hypot(np.diff(x), np.diff(y)).sum())
        for name, p in cfgs.items():
            r = analyse_attempt(x, y, s, p)
            base = dict(config=name, event_id=eid, nfl_id=int(meta["nfl_id"]), order=int(meta["order"]))
            row = dict(**base, ok=r["ok"], reason=r["reason"], n_reversals=r["n_reversals"], path_length=pl_len, **r["flags"])
            if r["ok"] and name == "reference":
                k = r["kin"]
                row["speed_abs_diff_median"] = float(np.median(np.abs(k["speed_pos"] - s)))
                for d in (1, -1):
                    dv = deviation_deg(k["vx"], k["vy"], k["u"], d); geometry_dev += list(dv[d * k["u"] >= 3.0])
            A.append(row)
            for rv in r["reversals"][:2]:
                R.append(dict(**base, turn="R1" if rv["index"] == 0 else "R2", valid=rv["valid"], reason=rv["reason"],
                              **{c: rv.get(c, np.nan) for c in REV_COLS}, window_overlaps_turn=rv.get("window_overlaps_turn", None),
                              approach_from_start=rv["approach_from_start"]))
    A = pl.DataFrame(A, infer_schema_length=None); R = pl.DataFrame(R, infer_schema_length=None).join(cr.select("nfl_id", "pos"), on="nfl_id", how="left")
    R = R.with_columns(pl.col("leg_peak_in_window").cast(pl.Float64))
    A.write_parquet(dout / "attempts.parquet"); R.write_parquet(dout / "reversals.parquet")
    Ar = A.filter(pl.col("config") == "reference"); Rr = R.filter(pl.col("config") == "reference")
    summary = dict(run=run)
    summary["geometry"] = dict(mid_leg_dev_percentiles={str(q): float(v) for q, v in zip((50, 90, 95, 99, 99.5), np.percentile(geometry_dev, [50, 90, 95, 99, 99.5]))},
                               n_frames=len(geometry_dev))
    r1v = Rr.filter((pl.col("turn") == "R1") & pl.col("valid")); r2v = Rr.filter((pl.col("turn") == "R2") & pl.col("valid"))
    def kdist(df):
        return {str(a): int(b) for a, b in df.group_by("nfl_id").agg(pl.len().alias("k")).group_by("k").agg(pl.len().alias("c")).sort("k").iter_rows()}
    summary["audit"] = dict(
        attempts=ev.height, athletes=int(ev["nfl_id"].n_unique()), attempts_per_athlete=kdist(ev),
        athletes_repeated_raw=int(k_raw.filter(pl.col("k") >= 2).height),
        raw_attempt_index=dict(ev.group_by("attempt").agg(pl.len().alias("c")).sort("attempt").iter_rows()),
        duplicate_player_attempt=int(ev.group_by("nfl_id", "attempt").agg(pl.len().alias("c")).filter(pl.col("c") > 1).height),
        dt_ms_values={str(int(a)): int(b) for a, b in zip(*np.unique(dts, return_counts=True))},
        n_frames=describe(ev["n_frames"]), x_range=describe(ev["x_range"]), y_range=describe(ev["y_range"]),
        path_length=describe(Ar["path_length"]), s_max_over_12_5=int((ev["s_max"] > 12.5).sum()),
        too_short=int((~Ar["ok"]).sum()), n_reversals=dict(Ar.group_by("n_reversals").agg(pl.len().alias("c")).sort("n_reversals").iter_rows()),
        start_moving=int(Ar["start_moving"].fill_null(False).sum()), end_moving=int(Ar["end_moving"].fill_null(False).sum()),
        speed_pos_vs_provided_median_abs=describe(Ar["speed_abs_diff_median"]),
        R1_visible=int(Rr.filter(pl.col("turn") == "R1").height), R2_visible=int(Rr.filter(pl.col("turn") == "R2").height),
        R1_reasons={(k or "VALID"): int(v) for k, v in Rr.filter(pl.col("turn") == "R1").group_by("reason").agg(pl.len().alias("c")).iter_rows()},
        R2_reasons={(k or "VALID"): int(v) for k, v in Rr.filter(pl.col("turn") == "R2").group_by("reason").agg(pl.len().alias("c")).iter_rows()},
        R1_valid=dict(attempts=r1v.height, athletes=int(r1v["nfl_id"].n_unique()), per_athlete=kdist(r1v)),
        R2_valid=dict(attempts=r2v.height, athletes=int(r2v["nfl_id"].n_unique()), per_athlete=kdist(r2v)),
        R1_approach_from_recording_start=int(Rr.filter(pl.col("turn") == "R1")["approach_from_start"].sum()),
    )
    pos_tab = {}
    for p_ in sorted(cr["pos"].drop_nulls().unique()):
        ids = cr.filter(pl.col("pos") == p_)["nfl_id"].implode()
        pos_tab[p_] = dict(attempts=int(ev.filter(pl.col("nfl_id").is_in(ids)).height), athletes=int(ev.filter(pl.col("nfl_id").is_in(ids))["nfl_id"].n_unique()),
                           R1_valid_athletes=int(r1v.filter(pl.col("nfl_id").is_in(ids))["nfl_id"].n_unique()),
                           R1_two_valid=int(r1v.filter(pl.col("nfl_id").is_in(ids)).group_by("nfl_id").len().filter(pl.col("len") >= 2).height))
    summary["audit"]["by_position"] = {k: v for k, v in pos_tab.items() if v["attempts"]}
    vath = r1v.select("nfl_id").unique().join(cr, on="nfl_id", how="left")
    summary["audit"]["R1_valid_athletes_with"] = {c: int(vath[c].is_not_null().sum()) for c in COMBINE}

    # ---------------- Task B: window checks (reference) ----------------
    summary["window_checks"] = {t: {c: describe(Rr.filter((pl.col("turn") == t) & pl.col("valid"))[c]) for c in REV_COLS}
                                for t in ("R1", "R2")}
    summary["window_checks"]["overlap_with_turn_any"] = int(Rr.filter(pl.col("valid"))["window_overlaps_turn"].fill_null(False).sum())

    # ---------------- Task C: reliability + sensitivity ----------------
    rel_rows, rank_rows = [], []
    for name in cfgs:
        Rc = R.filter(pl.col("config") == name)
        for t in ("R1", "R2"):
            v = Rc.filter((pl.col("turn") == t) & pl.col("valid"))
            row = dict(config=name, turn=t, attempts=v.height, athletes=int(v["nfl_id"].n_unique()),
                       athletes_2plus=int(v.group_by("nfl_id").len().filter(pl.col("len") >= 2).height),
                       **{f"d_{k}": x for k, x in describe(v["accel"]).items()}, **rel(v, "accel", B_REF if name == "reference" else B_SENS))
            rel_rows.append(row)
            pm = lambda df: df.group_by("nfl_id").agg(pl.col("accel").mean())  # noqa: E731
            j = pm(Rr.filter((pl.col("turn") == t) & pl.col("valid"))).join(pm(v), on="nfl_id", suffix="_c")
            rank_rows.append(dict(config=name, turn=t, n=j.height, rank_vs_ref=float(spearmanr(j["accel"], j["accel_c"]).statistic)))
    REL = pl.DataFrame(rel_rows, infer_schema_length=None); REL.write_parquet(eout / "reliability.parquet")
    RANK = pl.DataFrame(rank_rows); RANK.write_parquet(eout / "sensitivity_rank.parquet")
    # first-two vs all-attempts, aggregation agreement
    v1 = Rr.filter((pl.col("turn") == "R1") & pl.col("valid"))
    P = v1.group_by("nfl_id").agg(pl.len().alias("n_valid"), pl.col("accel").mean().alias("accel_mean"), pl.col("accel").median().alias("accel_median"),
                                  pl.col("accel").max().alias("accel_best"), pl.col("accel").sort_by("order").first().alias("accel_first"),
                                  *[pl.col(c).mean().alias(f"{c}_mean") for c in ("v_entry", "v_min", "v_start", "turn_duration", "heading_change_deg", "gap_min_to_window")])
    v2 = Rr.filter((pl.col("turn") == "R2") & pl.col("valid")).group_by("nfl_id").agg(pl.col("accel").mean().alias("r2_accel_mean"))
    P = P.join(v2, on="nfl_id", how="left").join(cr, on="nfl_id", how="left")
    sub = P.filter(pl.col("n_valid") >= 2)
    summary["aggregation_agreement"] = {f"{a}~{b}": float(spearmanr(sub[f"accel_{a}"], sub[f"accel_{b}"]).statistic)
                                        for a, b in (("mean", "median"), ("mean", "first"), ("mean", "best"), ("first", "best"))} if sub.height > 5 else {}

    # ---------------- Task D: construct checks ----------------
    con = []
    for cov in ("v_entry", "v_min", "v_start", "turn_duration", "heading_change_deg", "gap_min_to_window", "window_normal_share", "window_max_dev_deg"):
        w = wpos(v1, "accel", cov); wa = within_athlete(v1, "accel", cov)
        con.append(dict(level="attempt", covariate=cov, n=w["n"], rho=w.get("rho"), lo=w.get("lo"), hi=w.get("hi"),
                        rho_within_pos=w.get("rho_within_pos"), n_diff=wa["n"], rho_within_athlete_diff=wa["rho"]))
    for cov in COMBINE + ["r2_accel_mean"]:
        w = wpos(P, "accel_mean", cov)
        con.append(dict(level="player_mean", covariate=cov, n=w["n"], rho=w.get("rho"), lo=w.get("lo"), hi=w.get("hi"), rho_within_pos=w.get("rho_within_pos")))
    CON = pl.DataFrame(con, infer_schema_length=None); CON.write_parquet(eout / "construct.parquet")
    summary["residual_reliability"] = [residual_rel(v1, "accel", x, B_REF) for x in ("v_start", "v_entry", "v_min", "gap_min_to_window")]
    summary["covariate_reliability"] = {c: rel(v1, c, B_SENS) for c in ("v_start", "v_entry", "v_min", "turn_duration", "gap_min_to_window")}
    # variance explained by official measures + position (player means)
    r2 = []
    for cols in ([], ["short_shuttle"], ["forty"], ["ten_yd_split"], ["short_shuttle", "forty", "ten_yd_split"]):
        d = P.select("accel_mean", "pos", *cols).drop_nulls()
        Pp = sorted(d["pos"].unique().to_list())
        X = np.column_stack([np.ones(d.height)] + [(d["pos"] == q).cast(int).to_numpy() for q in Pp[1:]] + [d[c].to_numpy() for c in cols])
        y_ = d["accel_mean"].to_numpy(); beta, *_ = np.linalg.lstsq(X, y_, rcond=None); res = y_ - X @ beta
        rr = 1 - res.var() / y_.var(); kk = X.shape[1] - 1
        r2.append(dict(model="position" + "".join(f"+{c}" for c in cols), n=d.height, r2=float(rr), adj_r2=float(1 - (1 - rr) * (d.height - 1) / (d.height - kk - 1))))
    summary["conventional_r2"] = r2

    # ---------------- Task E: comparison with three-cone late-loop speed gain ----------------
    tc_path = INTERIM / "phase11_1_c_reacc" / PH111_RUN / "c_turns.parquet"
    tc = pl.read_parquet(tc_path).filter(pl.col("config") == "reference")
    tcp = tc.group_by("nfl_id").agg(pl.col("cand_a").mean().alias("tc_late_loop_gain"), pl.len().alias("tc_n"))
    both = P.join(tcp, on="nfl_id", how="inner")
    summary["three_cone_comparison"] = dict(
        athletes_both=both.height, athletes_both_two_attempts=int(both.filter((pl.col("n_valid") >= 2) & (pl.col("tc_n") >= 2)).height),
        player_mean_association=wpos(both, "accel_mean", "tc_late_loop_gain"),
        three_cone_window=dict(mean_abs_omega=describe(tc["a_mean_abs_omega"]), heading_change=describe(tc["a_heading_change"]),
                               normal_share=describe(tc["a_normal_share"])),
        three_cone_level=describe(tc["cand_a"]))

    # ---------------- repeat-attempt selection ----------------
    ath = P.with_columns((pl.col("n_valid") >= 2).alias("repeater"))
    sel = dict(n_repeaters=int(ath["repeater"].sum()), n_single=int((~ath["repeater"]).sum()))
    tab = ath.group_by("pos", "repeater").len().pivot(index="pos", on="repeater", values="len").fill_null(0).sort("pos")
    sel["position_table"] = tab.to_dicts(); sel["position_chi2_p"] = float(chi2_contingency(tab.select(pl.exclude("pos")).to_numpy())[1])
    rows = []
    first = v1.sort("nfl_id", "order").group_by("nfl_id", maintain_order=True).first().select(
        "nfl_id", *[pl.col(c).alias(f"first_{c}") for c in ("accel", "v_entry", "v_min", "v_start", "turn_duration")])
    ath = ath.join(first, on="nfl_id", how="left")
    for v in COMBINE + [f"first_{c}" for c in ("accel", "v_entry", "v_min", "v_start", "turn_duration")]:
        az = ath.with_columns(pl.col(v).fill_nan(None)).with_columns(((pl.col(v) - pl.col(v).mean().over("pos")) / pl.col(v).std().over("pos")).alias("_z"))
        a_, b_ = az.filter(pl.col("repeater")), az.filter(~pl.col("repeater"))
        ra, sa = a_[v].drop_nulls().to_numpy(), b_[v].drop_nulls().to_numpy(); rz, sz = a_["_z"].drop_nulls().to_numpy(), b_["_z"].drop_nulls().to_numpy()
        rows.append(dict(variable=v, n_rep=len(ra), n_single=len(sa), missing_rep=float(1 - len(ra) / a_.height), missing_single=float(1 - len(sa) / b_.height),
                         median_rep=float(np.median(ra)), median_single=float(np.median(sa)), mwu_p=float(mannwhitneyu(ra, sa).pvalue),
                         z_rep=float(rz.mean()), z_single=float(sz.mean()), mwu_p_within_pos=float(mannwhitneyu(rz, sz).pvalue)))
    SEL = pl.DataFrame(rows); SEL.write_parquet(eout / "selection.parquet")
    tc_rep = set(tc.group_by("nfl_id").len().filter(pl.col("len") >= 2)["nfl_id"].to_list())
    sh_rep = set(ath.filter(pl.col("repeater"))["nfl_id"].to_list())
    sel["overlap_with_three_cone_repeaters"] = len(tc_rep & sh_rep)
    # do raw repeaters differ in first-attempt validity? (reason for re-running is unrecorded)
    sel["raw_repeaters_first_attempt_R1_valid"] = float(Rr.filter((pl.col("turn") == "R1") & (pl.col("order") == 0) & pl.col("nfl_id").is_in(
        k_raw.filter(pl.col("k") >= 2)["nfl_id"].implode()))["valid"].mean())
    sel["single_raw_first_attempt_R1_valid"] = float(Rr.filter((pl.col("turn") == "R1") & (pl.col("order") == 0) & pl.col("nfl_id").is_in(
        k_raw.filter(pl.col("k") == 1)["nfl_id"].implode()))["valid"].mean())
    summary["selection"] = sel
    P.write_parquet(dout / "player_features.parquet"); ath.write_parquet(dout / "athletes.parquet")

    json.dump(dict(run=run, reference=params_dict(REF), sensitivity=SENS, seed=SEED, B_ref=B_REF, B_sens=B_SENS, phase11_1_run=PH111_RUN,
                   inputs=["data/interim/combine_tracking.parquet", "data/interim/combine_results.parquet", str(tc_path.relative_to(ROOT))]),
              open(eout / "config.json", "w"), indent=1)
    summary.update(seconds=round(time.time() - t0, 1), reliability=REL.to_dicts(), sensitivity_rank=RANK.to_dicts(),
                   construct=CON.to_dicts(), selection_table=SEL.to_dicts())
    json.dump(summary, open(eout / "summary.json", "w"), indent=1, default=float)
    (ROOT / "experiments" / "phase12_shuttle_accel" / "LATEST").write_text(run)
    print(f"done in {time.time() - t0:.0f}s -> {eout}")


if __name__ == "__main__":
    main()
