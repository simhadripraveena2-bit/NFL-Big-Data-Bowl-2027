"""Phase 11.1: construct audit of C re-acceleration (combine data ONLY; measurement audit, no outcomes).

Reads only data/interim/combine_tracking.parquet (three-cone PLAYER rows) and combine_results.parquet.
No NFL game table (player_play, plays, games, tracking) and no confirmatory-join file is opened.
The Stage 1 detector and feature definition (turn_recovery.TurnParams defaults) are reused unchanged;
candidate A is asserted to equal the Stage 1 ``reacc`` value for every turn.

Outputs (git-ignored):
  data/interim/phase11_1_c_reacc/<run>/c_turns.parquet          one row per template-valid attempt x config
  experiments/phase11_1_c_reacc/<run>/config.json, summary.json and aggregate tables

Usage: python scripts/run_c_reacc_construct_audit.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl
from scipy.stats import chi2_contingency, mannwhitneyu, spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nfl_bdb.evaluation.repeatability import boot_two_attempt, centre_by_group, two_attempt_stats  # noqa: E402
from nfl_bdb.features.turn_reacc_audit import audit_turn  # noqa: E402
from nfl_bdb.features.turn_recovery import TurnParams, detect_turns, params_dict, with_  # noqa: E402

INTERIM = ROOT / "data" / "interim"
SEED = 1111
B_REF, B_SENS = 2000, 500
REF = TurnParams()
CONFIGS = {"reference": REF, "window=5": with_(REF, window=5), "window=9": with_(REF, window=9),
           "window=11": with_(REF, window=11), "speed_source=provided": with_(REF, speed_source="provided"),
           "speed_source=provided_sg": with_(REF, speed_source="provided_sg")}
COVARIATES = ["v_min", "v_entry", "retention", "duration", "chord_deg", "cum_heading_deg", "v_exit",
              "frames_min_to_exit", "a_frac_inside", "a_mean_abs_omega", "a_normal_share"]
TURN_DIAG = ["a_mean_abs_omega", "a_share_turning", "a_heading_change", "a_normal_share",
             "b_mean_abs_omega", "b_share_turning", "b_heading_change", "b_normal_share"]
COMBINE = ["three_cone", "short_shuttle", "forty", "ten_yd_split"]


def extract(attempts, name, p):
    rows = []
    for at in attempts:
        r = detect_turns(at["x"], at["y"], at["s"], p)
        if not (r["ok"] and r["template_ok"]):
            continue
        turns = r["turns"]; labels = [t["label"] for t in turns]; n = len(at["x"])
        j = labels.index("C"); t = turns[j]
        nxt = turns[j + 1]["start"] if j + 1 < len(turns) else n
        au = audit_turn(r["kin"]["speed"], t, nxt, n, p, omega_deg=r["kin"]["omega_deg"])
        a_stage1 = t["reacc"]
        assert (np.isnan(a_stage1) and np.isnan(au["cand_a"])) or abs(a_stage1 - au["cand_a"]) < 1e-9, "candidate A != Stage 1"
        b2 = "B2" in labels
        status = "B2_detected" if b2 else ("B2_absorbed" if t["chord_deg"] < 135 else "B2_not_detected_C_ge135")
        rows.append(dict(config=name, event_id=at["event_id"], nfl_id=at["nfl_id"], order=at["order"], n_frames=n,
                         b2_status=status, b2_detected=b2, truncated_end=r["flags"]["truncated_end"],
                         v_min=t["v_min"], v_entry=t["v_entry"], retention=t["retention"], duration=t["duration"],
                         chord_deg=t["chord_deg"], cum_heading_deg=t["cum_heading_deg"], **au))
    return rows


def pairs(df, col):
    d = df.filter(pl.col(col).is_not_nan() & pl.col(col).is_not_null()).sort("nfl_id", "order")
    g = d.group_by("nfl_id", maintain_order=True).head(2).group_by("nfl_id", maintain_order=True).agg(pl.col(col), pl.col("pos").first())
    g = g.filter(pl.col(col).list.len() == 2)
    a = np.array([v[0] for v in g[col].to_list()]); b = np.array([v[1] for v in g[col].to_list()])
    return a, b, np.array(g["pos"].to_list()), g["nfl_id"].to_list()


def rel(df, col, B, seed=SEED):
    a, b, pos, _ = pairs(df, col)
    out = dict(n_pairs=len(a))
    if len(a) < 8:
        return out
    st = two_attempt_stats(a, b); ci = boot_two_attempt(a, b, None, B=B, seed=seed)
    ac, bc = centre_by_group(a, b, pos); stc = two_attempt_stats(ac, bc)
    cic = boot_two_attempt(a, b, pos, stats=("icc31",), B=B, seed=seed)
    out.update(icc31=st["icc31"], icc31_lo=ci["icc31"][0], icc31_hi=ci["icc31"][1],
               icc21=st["icc21"], icc21_lo=ci["icc21"][0], icc21_hi=ci["icc21"][1],
               spearman=st["spearman"], spearman_lo=ci["spearman"][0], spearman_hi=ci["spearman"][1],
               te=st["te"], te_pct=st["te_pct"], mean_diff=st["mean_diff"],
               icc31_within_pos=stc["icc31"], icc31_within_pos_lo=cic["icc31"][0], icc31_within_pos_hi=cic["icc31"][1])
    return out


def describe(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) == 0:
        return dict(n=0)
    q = np.percentile(x, [5, 25, 50, 75, 95])
    return dict(n=int(len(x)), mean=float(x.mean()), sd=float(x.std(ddof=1)), p05=q[0], p25=q[1], median=q[2], p75=q[3], p95=q[4])


def wpos_spearman(df, a, b):
    d = df.select("pos", a, b).drop_nulls().filter(pl.col(a).is_not_nan() & pl.col(b).is_not_nan())
    if d.height < 15:
        return np.nan, np.nan, d.height
    d = d.with_columns(pl.col(a).rank().alias("_a"), pl.col(b).rank().alias("_b"))
    d = d.with_columns((pl.col("_a") - pl.col("_a").mean().over("pos")).alias("_a"), (pl.col("_b") - pl.col("_b").mean().over("pos")).alias("_b"))
    return float(spearmanr(d[a], d[b]).statistic), float(np.corrcoef(d["_a"], d["_b"])[0, 1]), d.height


def residualise(df, y, x):
    """Attempt-level OLS residual of y on x + position dummies (pooled)."""
    d = df.filter(pl.col(y).is_not_nan() & pl.col(x).is_not_nan())
    P = sorted(d["pos"].unique().to_list())
    X = np.column_stack([np.ones(d.height), d[x].to_numpy()] + [(d["pos"] == p).cast(int).to_numpy() for p in P[1:]])
    beta, *_ = np.linalg.lstsq(X, d[y].to_numpy(), rcond=None)
    r2 = 1 - np.var(d[y].to_numpy() - X @ beta) / np.var(d[y].to_numpy())
    return d.with_columns(pl.Series(f"{y}_res_{x}", d[y].to_numpy() - X @ beta)), float(beta[1]), float(r2)


def main():
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dout = INTERIM / "phase11_1_c_reacc" / run; eout = ROOT / "experiments" / "phase11_1_c_reacc" / run
    dout.mkdir(parents=True); eout.mkdir(parents=True)
    t0 = time.time()
    ct = pl.read_parquet(INTERIM / "combine_tracking.parquet").filter(
        (pl.col("drill_type") == "THREE_CONE_DRILL") & (pl.col("entity_type") == "PLAYER")).sort("event_id", "time")
    cr = pl.read_parquet(INTERIM / "combine_results.parquet").select(
        "nfl_id", pl.col("combine_position").alias("pos"), "draft_year", *COMBINE)
    meta = ct.group_by("event_id", "nfl_id", "attempt").agg(pl.col("time").min().alias("t0")).sort("nfl_id", "t0")
    meta = meta.with_columns(pl.int_range(pl.len()).over("nfl_id").alias("order"))
    om = {r["event_id"]: r for r in meta.iter_rows(named=True)}
    attempts = [dict(event_id=eid, nfl_id=int(om[eid]["nfl_id"]), order=int(om[eid]["order"]), raw_attempt=om[eid]["attempt"],
                     x=g["x"].to_numpy(), y=g["y"].to_numpy(), s=g["s"].to_numpy())
                for (eid,), g in ct.group_by(["event_id"], maintain_order=True)]
    rows = []
    for name, p in CONFIGS.items():
        rows += extract(attempts, name, p)
    D = pl.DataFrame(rows, infer_schema_length=None).join(cr.select("nfl_id", "pos"), on="nfl_id", how="left")
    D.write_parquet(dout / "c_turns.parquet")
    R = D.filter(pl.col("config") == "reference")
    summary = dict(run=run)

    # ---------- Task A: window audit (reference) ----------
    def audit_block(df):
        cats = {k: int(v) for k, v in df.group_by("a_category").len().iter_rows()}
        return dict(attempts=df.height, athletes=int(df["nfl_id"].n_unique()), a_categories=cats,
                    a_frac_inside=describe(df["a_frac_inside"]), a_n_frames=describe(df["a_n_frames"]),
                    frames_min_to_exit=describe(df["frames_min_to_exit"]),
                    min_to_exit_hist={int(k): int(v) for k, v in df.group_by("frames_min_to_exit").len().sort("frames_min_to_exit").iter_rows()},
                    duration=describe(df["duration"]), chord=describe(df["chord_deg"]),
                    turning={k: describe(df[k]) for k in TURN_DIAG},
                    b_reasons={k or "usable": int(v) for k, v in df.group_by("b_reason").len().iter_rows()})
    summary["window_audit"] = {"all": audit_block(R), **{s: audit_block(R.filter(pl.col("b2_status") == s)) for s in sorted(R["b2_status"].unique())}}
    summary["window_audit_by_config"] = {c: dict(a_categories={k: int(v) for k, v in D.filter(pl.col("config") == c).group_by("a_category").len().iter_rows()},
                                                 median_frac_inside=float(D.filter(pl.col("config") == c)["a_frac_inside"].median()),
                                                 b2_status={k: int(v) for k, v in D.filter(pl.col("config") == c).group_by("b2_status").len().iter_rows()})
                                         for c in CONFIGS}
    # athlete consistency of B2 status across the two attempts
    st = R.sort("nfl_id", "order").group_by("nfl_id", maintain_order=True).head(2).group_by("nfl_id").agg(pl.col("b2_detected")).filter(pl.col("b2_detected").list.len() == 2)
    summary["b2_status_pairs"] = {"both_detected": int(sum(all(v) for v in st["b2_detected"])), "both_not": int(sum(not any(v) for v in st["b2_detected"])),
                                  "mixed": int(sum(any(v) and not all(v) for v in st["b2_detected"]))}

    # ---------- Task B: candidates ----------
    cand_rows = []
    for c in CONFIGS:
        df = D.filter(pl.col("config") == c)
        B = B_REF if c == "reference" else B_SENS
        common = df.filter(pl.col("cand_a").is_not_nan() & pl.col("cand_b").is_not_nan())
        for cand in ("cand_a", "cand_b"):
            for sample, sub in (("own", df), ("common", common)):
                u = sub.filter(pl.col(cand).is_not_nan())
                k = u.group_by("nfl_id").len()
                cand_rows.append(dict(config=c, candidate=cand, sample=sample, attempts=u.height, athletes=int(u["nfl_id"].n_unique()),
                                      athletes_2plus=int(k.filter(pl.col("len") >= 2).height), **{f"d_{kk}": vv for kk, vv in describe(u[cand]).items()},
                                      **rel(u, cand, B)))
        if c == "reference":
            for s in sorted(df["b2_status"].unique()):
                sub = df.filter(pl.col("b2_status") == s)
                for cand in ("cand_a", "cand_b"):
                    u = sub.filter(pl.col(cand).is_not_nan())
                    cand_rows.append(dict(config=c, candidate=cand, sample=f"status={s}", attempts=u.height, athletes=int(u["nfl_id"].n_unique()),
                                          athletes_2plus=int(u.group_by("nfl_id").len().filter(pl.col("len") >= 2).height),
                                          **{f"d_{kk}": vv for kk, vv in describe(u[cand]).items()}, **rel(u, cand, B)))
            # pairs with B2 detected in both / in neither attempt (status of the pair)
            first2 = df.sort("nfl_id", "order").group_by("nfl_id", maintain_order=True).head(2)
            ps = first2.group_by("nfl_id").agg(pl.col("b2_detected").all().alias("all"), (~pl.col("b2_detected")).all().alias("none"))
            for lab, ids in (("pair_both_B2", ps.filter(pl.col("all"))["nfl_id"]), ("pair_neither_B2", ps.filter(pl.col("none"))["nfl_id"])):
                sub = first2.filter(pl.col("nfl_id").is_in(ids.implode()))
                for cand in ("cand_a", "cand_b"):
                    u = sub.filter(pl.col(cand).is_not_nan())
                    cand_rows.append(dict(config=c, candidate=cand, sample=lab, attempts=u.height, athletes=int(u["nfl_id"].n_unique()),
                                          athletes_2plus=int(u.group_by("nfl_id").len().filter(pl.col("len") >= 2).height), **rel(u, cand, B)))
    CAND = pl.DataFrame(cand_rows, infer_schema_length=None); CAND.write_parquet(eout / "candidates.parquet")
    # rank agreement with reference, per candidate
    sens = []
    for c in CONFIGS:
        for cand in ("cand_a", "cand_b"):
            pm = lambda df: df.filter(pl.col(cand).is_not_nan()).group_by("nfl_id").agg(pl.col(cand).mean())  # noqa: E731
            j = pm(R).join(pm(D.filter(pl.col("config") == c)), on="nfl_id", suffix="_c")
            sens.append(dict(config=c, candidate=cand, n=j.height, rank_vs_ref=float(spearmanr(j[cand], j[f"{cand}_c"]).statistic)))
    SENS = pl.DataFrame(sens); SENS.write_parquet(eout / "sensitivity_rank.parquet")
    ab = R.filter(pl.col("cand_a").is_not_nan() & pl.col("cand_b").is_not_nan())
    summary["a_vs_b_attempt_spearman"] = dict(n=ab.height, rho=float(spearmanr(ab["cand_a"], ab["cand_b"]).statistic),
                                              within_pos=wpos_spearman(ab, "cand_a", "cand_b")[1])
    for s in sorted(ab["b2_status"].unique()):
        x = ab.filter(pl.col("b2_status") == s)
        summary["a_vs_b_attempt_spearman"][s] = dict(n=x.height, rho=float(spearmanr(x["cand_a"], x["cand_b"]).statistic) if x.height > 5 else None)

    # ---------- Task C: speed and turn-shape dependence (reference) ----------
    dep = []
    for cand in ("cand_a", "cand_b"):
        for cov in COVARIATES:
            rho, rw, n = wpos_spearman(R, cand, cov)
            # within-athlete differences on the same first-two usable attempts
            d = R.filter(pl.col(cand).is_not_nan() & pl.col(cov).is_not_nan()).sort("nfl_id", "order")
            g = d.group_by("nfl_id", maintain_order=True).head(2).group_by("nfl_id").agg(pl.col(cand), pl.col(cov)).filter(pl.col(cand).list.len() == 2)
            dc = np.array([v[1] - v[0] for v in g[cand].to_list()]); dv = np.array([v[1] - v[0] for v in g[cov].to_list()])
            dep.append(dict(candidate=cand, covariate=cov, n_attempts=n, rho_attempt=rho, rho_attempt_within_pos=rw,
                            n_diff=len(dc), rho_within_athlete_diff=float(spearmanr(dc, dv).statistic) if len(dc) > 5 else np.nan))
    DEP = pl.DataFrame(dep); DEP.write_parquet(eout / "dependence.parquet")
    # does a repeatable speed-change component remain after removing the start speed?
    resid = []
    for cand, x in (("cand_a", "v_min"), ("cand_a", "a_frac_inside"), ("cand_b", "v_exit"), ("cand_b", "v_min"), ("cand_a", "retention"), ("cand_b", "retention"),
                    ("cand_a", "a_normal_share"), ("cand_b", "b_normal_share")):
        dd, beta, r2 = residualise(R, cand, x)
        resid.append(dict(candidate=cand, adjusted_for=x, beta=beta, r2_with_position=r2, **rel(dd, f"{cand}_res_{x}", B_REF)))
    RES = pl.DataFrame(resid, infer_schema_length=None); RES.write_parquet(eout / "residual_reliability.parquet")
    summary["covariate_reliability"] = {cov: rel(R, cov, B_SENS) for cov in ("v_exit", "v_min", "frames_min_to_exit", "a_frac_inside", "a_mean_abs_omega", "a_normal_share", "b_normal_share")}

    # ---------- Task D: repeat-attempt selection ----------
    valid_k = R.group_by("nfl_id").len().rename({"len": "k_valid"})
    raw_k = meta.group_by("nfl_id").len().rename({"len": "k_raw"})
    first = R.sort("nfl_id", "order").group_by("nfl_id", maintain_order=True).first().select(
        "nfl_id", pl.col("order").alias("first_valid_order"), *[pl.col(c).alias(f"first_{c}") for c in ("cand_a", "cand_b", "v_entry", "v_min", "retention", "duration", "b2_detected", "a_frac_inside")])
    ath = valid_k.join(raw_k, on="nfl_id").join(cr, on="nfl_id", how="left").join(first, on="nfl_id", how="left").with_columns(
        (pl.col("k_valid") >= 2).alias("repeater"))
    ath.write_parquet(dout / "athlete_selection.parquet")
    sel = dict(n_repeaters=int(ath["repeater"].sum()), n_single=int((~ath["repeater"]).sum()),
               single_with_extra_raw_attempts=int(ath.filter(~pl.col("repeater") & (pl.col("k_raw") >= 2)).height),
               first_valid_not_first_recorded=int(ath.filter(pl.col("first_valid_order") > 0).height))
    tab = ath.group_by("pos", "repeater").len().pivot(index="pos", on="repeater", values="len").fill_null(0).sort("pos")
    sel["position_table"] = tab.to_dicts()
    m = tab.select(pl.exclude("pos")).to_numpy()
    sel["position_chi2_p"] = float(chi2_contingency(m)[1])
    sel["draft_year_table"] = ath.group_by("draft_year", "repeater").len().sort("draft_year").to_dicts()
    cmp_rows = []
    ath_z = ath
    for v in COMBINE + [f"first_{c}" for c in ("cand_a", "cand_b", "v_entry", "v_min", "retention", "duration", "a_frac_inside")]:
        ath_z = ath_z.with_columns(pl.col(v).fill_nan(None))
        ath_z = ath_z.with_columns(((pl.col(v) - pl.col(v).mean().over("pos")) / pl.col(v).std().over("pos")).alias(f"{v}_z"))
    for v in COMBINE + [f"first_{c}" for c in ("cand_a", "cand_b", "v_entry", "v_min", "retention", "duration", "a_frac_inside")]:
        r_ = ath_z.filter(pl.col("repeater")); s_ = ath_z.filter(~pl.col("repeater"))
        rv, sv = r_[v].drop_nulls().drop_nans().to_numpy(), s_[v].drop_nulls().drop_nans().to_numpy()
        rz, sz = r_[f"{v}_z"].drop_nulls().drop_nans().to_numpy(), s_[f"{v}_z"].drop_nulls().drop_nans().to_numpy()
        cmp_rows.append(dict(variable=v, n_rep=len(rv), n_single=len(sv),
                             missing_rep=float(1 - len(rv) / r_.height), missing_single=float(1 - len(sv) / s_.height),
                             median_rep=float(np.median(rv)) if len(rv) else np.nan, median_single=float(np.median(sv)) if len(sv) else np.nan,
                             mwu_p=float(mannwhitneyu(rv, sv).pvalue) if len(rv) > 3 and len(sv) > 3 else np.nan,
                             mean_within_pos_z_rep=float(rz.mean()) if len(rz) else np.nan, mean_within_pos_z_single=float(sz.mean()) if len(sz) else np.nan,
                             mwu_p_within_pos=float(mannwhitneyu(rz, sz).pvalue) if len(rz) > 3 and len(sz) > 3 else np.nan))
    SEL = pl.DataFrame(cmp_rows); SEL.write_parquet(eout / "selection_comparison.parquet")
    sel["b2_first_attempt_detected_share"] = {"repeaters": float(ath.filter(pl.col("repeater"))["first_b2_detected"].mean()),
                                              "single": float(ath.filter(~pl.col("repeater"))["first_b2_detected"].mean())}
    summary["selection"] = sel

    json.dump(dict(run=run, reference=params_dict(REF), configs={k: params_dict(v) for k, v in CONFIGS.items()}, seed=SEED,
                   B_ref=B_REF, B_sens=B_SENS, inputs=["data/interim/combine_tracking.parquet", "data/interim/combine_results.parquet"]),
              open(eout / "config.json", "w"), indent=1)
    summary.update(seconds=round(time.time() - t0, 1), candidates=CAND.to_dicts(), sensitivity_rank=SENS.to_dicts(),
                   dependence=DEP.to_dicts(), residual_reliability=RES.to_dicts(), selection_comparison=SEL.to_dicts())
    json.dump(summary, open(eout / "summary.json", "w"), indent=1, default=float)
    (ROOT / "experiments" / "phase11_1_c_reacc" / "LATEST").write_text(run)
    print(f"done in {time.time() - t0:.0f}s -> {eout}")


if __name__ == "__main__":
    main()
