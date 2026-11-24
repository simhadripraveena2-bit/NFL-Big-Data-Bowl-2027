"""Phase 11 (measurement feasibility ONLY): speed retention and recovery around turns in the NFL Combine
three-cone drill.

Reads only combine data (combine_tracking three-cone rows, combine_results, the combine-only tracked-40
predictor table) plus a per-player COUNT of regular-season player_play rows (coverage audit only).
No game outcome is read, joined or modelled. No registered analysis or result is touched.

Outputs (all git-ignored):
  data/interim/phase11_turn_recovery/<run>/turns.parquet           every detected turn, every configuration
  data/interim/phase11_turn_recovery/<run>/attempts.parquet        attempt-level status / flags, every configuration
  data/interim/phase11_turn_recovery/<run>/player_features.parquet player-level summaries (reference configuration)
  experiments/phase11_turn_recovery/<run>/config.json, summary.json and aggregate tables (*.parquet)

Usage: python scripts/run_turn_recovery_feasibility.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nfl_bdb.evaluation.repeatability import (boot_two_attempt, centre_by_group, icc1_unbalanced,  # noqa: E402
                                              two_attempt_stats)
from nfl_bdb.features.turn_recovery import TurnParams, detect_turns, params_dict, with_  # noqa: E402

INTERIM = ROOT / "data" / "interim"
JOIN_RUN = "20261121T135032Z"          # combine-only predictor table (tracked 40 peak speed) of the registered join
SEED = 1111
B_REF, B_SENS = 2000, 500
REF = TurnParams()
SENSITIVITY = {
    "window": [5, 9, 11],
    "speed_source": ["provided", "provided_sg"],
    "omega_min_deg": [45.0, 90.0],
    "v_stop": [0.75, 1.5],
    "entry_window": [1.0, 1.5, 3.0],
    "recovery_frac": [0.85, 0.95],
    "reacc_window": [0.3, 0.8],
}
LABELS = ["R1", "R2", "B1", "C", "B2"]
METRICS = ["v_entry", "v_min", "retention", "recovery_time", "reacc", "duration", "chord_deg", "cum_heading_deg"]
PRIMARY = ["C_retention", "C_recovery_time", "C_reacc", "R2_recovery_time", "R2_reacc"]
SECONDARY = ["C_v_entry", "C_v_min", "C_duration", "R1_retention", "R1_recovery_time", "R2_retention", "R2_v_min"]
CONVENTIONAL = ["three_cone", "short_shuttle", "forty", "ten_yd_split", "x_peak"]


def configurations():
    cfgs = {"reference": REF}
    for k, vals in SENSITIVITY.items():
        for v in vals:
            cfgs[f"{k}={v}"] = with_(REF, **{k: v})
    return cfgs


def run_config(name, p, attempts):
    a_rows, t_rows = [], []
    for at in attempts:
        r = detect_turns(at["x"], at["y"], at["s"], p)
        base = dict(config=name, event_id=at["event_id"], nfl_id=at["nfl_id"], order=at["order"], n_frames=len(at["x"]))
        a_rows.append({**base, "ok": r["ok"], "reason": r.get("reason", ""), "template_ok": r["template_ok"],
                       "n_turns": len(r["turns"]), "truncated_start": r["flags"].get("truncated_start", False),
                       "truncated_end": r["flags"].get("truncated_end", False)})
        for j, t in enumerate(r["turns"]):
            t_rows.append({**base, "turn_index": j, "label": t["label"], "template_ok": r["template_ok"],
                           **{m: t[m] for m in METRICS}, "near_stop": t["near_stop"],
                           "recovery_censored": t["recovery_censored"], "reacc_frames": t["reacc_frames"],
                           "entry_at_window_edge": t["entry_at_window_edge"]})
    return a_rows, t_rows


def wide_features(turns: pl.DataFrame) -> pl.DataFrame:
    """One row per (config, attempt) with <label>_<metric> columns, template-matched attempts only.
    Censored recoveries are missing (not imputed)."""
    t = turns.filter(pl.col("template_ok") & pl.col("label").is_not_null()).with_columns(
        pl.when(pl.col("recovery_censored")).then(None).otherwise(pl.col("recovery_time")).alias("recovery_time"))
    long = t.unpivot(index=["config", "event_id", "nfl_id", "order", "label"], on=METRICS, variable_name="metric")
    long = long.with_columns((pl.col("label") + "_" + pl.col("metric")).alias("feature"))
    return long.pivot(index=["config", "event_id", "nfl_id", "order"], on="feature", values="value")


def reliability(W: pl.DataFrame, feats, pos_map, B, seed):
    rows = []
    for f in feats:
        if f not in W.columns:
            continue
        d = W.select("nfl_id", "order", f).drop_nulls().sort("nfl_id", "order")
        first2 = d.group_by("nfl_id", maintain_order=True).head(2)
        pairs = first2.group_by("nfl_id", maintain_order=True).agg(pl.col(f)).filter(pl.col(f).list.len() == 2)
        n = pairs.height
        allv = [np.array(v) for v in d.group_by("nfl_id").agg(pl.col(f))[f].to_list()]
        base = dict(feature=f, n_pairs=n, icc1_all=icc1_unbalanced(allv)["icc1"])
        if n < 8:
            rows.append(base); continue
        a = np.array([v[0] for v in pairs[f].to_list()]); b = np.array([v[1] for v in pairs[f].to_list()])
        g = np.array([pos_map.get(i, "NA") for i in pairs["nfl_id"].to_list()])
        st = two_attempt_stats(a, b)
        ci = boot_two_attempt(a, b, None, B=B, seed=seed)
        ac, bc = centre_by_group(a, b, g)
        stc = two_attempt_stats(ac, bc)
        cic = boot_two_attempt(a, b, g, stats=("icc31", "spearman"), B=B, seed=seed)
        row = {**base, **{k: st[k] for k in ("icc31", "icc21", "spearman", "te", "te_pct", "mean_diff", "grand_mean", "sd_between")},
               "icc31_lo": ci["icc31"][0], "icc31_hi": ci["icc31"][1], "icc21_lo": ci["icc21"][0], "icc21_hi": ci["icc21"][1],
               "spearman_lo": ci["spearman"][0], "spearman_hi": ci["spearman"][1],
               "icc31_within_pos": stc["icc31"], "icc31_within_pos_lo": cic["icc31"][0], "icc31_within_pos_hi": cic["icc31"][1],
               "spearman_within_pos": stc["spearman"]}
        for pos in sorted(set(g)):
            m = g == pos
            if m.sum() >= 8:
                row[f"icc31_{pos}"] = two_attempt_stats(a[m], b[m])["icc31"]; row[f"n_{pos}"] = int(m.sum())
        rows.append(row)
    return pl.DataFrame(rows, infer_schema_length=None)


def player_summaries(W: pl.DataFrame, feats) -> pl.DataFrame:
    best_dir = {"retention": "max", "reacc": "max", "recovery_time": "min", "v_min": "max", "v_entry": "max", "duration": "min"}
    aggs = [pl.len().alias("n_valid_attempts")]
    for f in feats:
        if f not in W.columns:
            continue
        m = f.split("_", 1)[1]
        aggs += [pl.col(f).mean().alias(f"{f}__mean"), pl.col(f).median().alias(f"{f}__median"),
                 pl.col(f).sort_by("order").drop_nulls().first().alias(f"{f}__first"),
                 (pl.col(f).max() if best_dir.get(m, "max") == "max" else pl.col(f).min()).alias(f"{f}__best"),
                 pl.col(f).count().alias(f"{f}__n")]
    return W.group_by("nfl_id").agg(aggs)


def spearman_ci(x, y, B, seed):
    x = np.asarray(x, float); y = np.asarray(y, float); n = len(x)
    rho = float(spearmanr(x, y).statistic)
    rng = np.random.default_rng(seed); v = []
    for _ in range(B):
        j = rng.integers(0, n, n)
        if np.std(x[j]) > 0 and np.std(y[j]) > 0:
            v.append(spearmanr(x[j], y[j]).statistic)
    lo, hi = np.percentile(v, [2.5, 97.5])
    return rho, float(lo), float(hi)


def within_position_ranks(df: pl.DataFrame, col: str) -> pl.Series:
    """Rank-transform then remove position means (rank-based partial association for position)."""
    r = df[col].rank()
    tmp = df.select("pos").with_columns(r.alias("_r"))
    return (tmp["_r"] - tmp.group_by("pos").agg(pl.col("_r").mean().alias("_m")).join(tmp, on="pos")["_m"]) if False else \
        tmp.with_columns((pl.col("_r") - pl.col("_r").mean().over("pos")).alias("_c"))["_c"]


def main():
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dout = INTERIM / "phase11_turn_recovery" / run; eout = ROOT / "experiments" / "phase11_turn_recovery" / run
    dout.mkdir(parents=True); eout.mkdir(parents=True)
    t0 = time.time()
    ct = pl.read_parquet(INTERIM / "combine_tracking.parquet").filter(
        (pl.col("drill_type") == "THREE_CONE_DRILL") & (pl.col("entity_type") == "PLAYER")).sort("event_id", "time")
    cr = pl.read_parquet(INTERIM / "combine_results.parquet").select(
        "nfl_id", pl.col("combine_position").alias("pos"), "draft_year", *[c for c in CONVENTIONAL if c != "x_peak"])
    pred = pl.read_parquet(INTERIM / "confirmatory_join" / JOIN_RUN / "predictors.parquet").select("nfl_id", "x_peak", "valid_tracked_40")
    games = pl.read_parquet(INTERIM / "games.parquet").select("game_id", "season_type")
    reg_players = (pl.read_parquet(INTERIM / "player_play.parquet", columns=["game_id", "nfl_id"]).join(games, on="game_id")
                   .filter(pl.col("season_type") == "REG").group_by("nfl_id").agg(pl.len().alias("reg_player_play_rows")))
    pos_map = dict(cr.select("nfl_id", "pos").iter_rows())

    # attempts in chronological order within player
    meta = ct.group_by("event_id", "nfl_id", "attempt").agg(pl.col("time").min().alias("t0"), pl.len().alias("n")).sort("nfl_id", "t0")
    meta = meta.with_columns(pl.int_range(pl.len()).over("nfl_id").alias("order"))
    attempts = []
    for (eid,), g in ct.group_by(["event_id"], maintain_order=True):
        m = meta.filter(pl.col("event_id") == eid).row(0, named=True)
        attempts.append(dict(event_id=eid, nfl_id=int(m["nfl_id"]), order=int(m["order"]),
                             x=g["x"].to_numpy(), y=g["y"].to_numpy(), s=g["s"].to_numpy()))
    cfgs = configurations()
    A, T = [], []
    for name, p in cfgs.items():
        a, t = run_config(name, p, attempts); A += a; T += t
    A = pl.DataFrame(A, infer_schema_length=None); T = pl.DataFrame(T, infer_schema_length=None)
    A.write_parquet(dout / "attempts.parquet"); T.write_parquet(dout / "turns.parquet")
    W_all = wide_features(T)
    feats = PRIMARY + SECONDARY

    # ---------------- A. audit (reference configuration) ----------------
    Aref = A.filter(pl.col("config") == "reference")
    valid = Aref.filter(pl.col("ok") & pl.col("template_ok"))
    per_player_raw = Aref.group_by("nfl_id").agg(pl.len().alias("k"))
    per_player_valid = valid.group_by("nfl_id").agg(pl.len().alias("k"))
    players = Aref.select("nfl_id").unique().join(cr, on="nfl_id", how="left").join(pred, on="nfl_id", how="left").join(reg_players, on="nfl_id", how="left")
    vplayers = players.filter(pl.col("nfl_id").is_in(valid["nfl_id"].unique().implode()))

    def dist(df):
        return {str(k): int(v) for k, v in df.group_by("k").agg(pl.len().alias("c")).sort("k").iter_rows()}

    audit = dict(
        attempts=Aref.height, athletes=int(Aref["nfl_id"].n_unique()),
        attempts_per_athlete_raw=dist(per_player_raw), attempts_per_athlete_valid=dist(per_player_valid),
        valid_attempts=valid.height, athletes_with_valid=int(valid["nfl_id"].n_unique()),
        athletes_with_2plus_valid=int(per_player_valid.filter(pl.col("k") >= 2).height),
        failures={**{f"not_ok:{r}": int(c) for r, c in Aref.filter(~pl.col("ok")).group_by("reason").agg(pl.len()).iter_rows()},
                  "ok_but_non_template": int(Aref.filter(pl.col("ok") & ~pl.col("template_ok")).height)},
        truncated_start_share_valid=float(valid["truncated_start"].mean()),
        by_position={p: dict(attempts=int(Aref.join(cr.select("nfl_id", "pos"), on="nfl_id").filter(pl.col("pos") == p).height),
                             athletes=int(players.filter(pl.col("pos") == p).height),
                             athletes_valid=int(vplayers.filter(pl.col("pos") == p).height),
                             athletes_2plus_valid=int(per_player_valid.filter(pl.col("k") >= 2).join(cr.select("nfl_id", "pos"), on="nfl_id").filter(pl.col("pos") == p).height))
                     for p in sorted(players["pos"].drop_nulls().unique().to_list())},
        valid_athletes_with=dict(
            official_three_cone=int(vplayers["three_cone"].is_not_null().sum()),
            official_short_shuttle=int(vplayers["short_shuttle"].is_not_null().sum()),
            official_forty=int(vplayers["forty"].is_not_null().sum()),
            official_ten_yd_split=int(vplayers["ten_yd_split"].is_not_null().sum()),
            valid_tracked_40=int(vplayers["valid_tracked_40"].fill_null(False).sum()),
            any_REG_player_play_rows=int(vplayers["reg_player_play_rows"].is_not_null().sum()),
            REG_rows_ge_100=int((vplayers["reg_player_play_rows"].fill_null(0) >= 100).sum())),
    )

    # ---------------- turn-level descriptives (reference) ----------------
    Tref = T.filter((pl.col("config") == "reference") & pl.col("template_ok"))
    turn_desc = (Tref.group_by("label").agg(
        pl.len().alias("n"), *[pl.col(m).median().alias(f"{m}_median") for m in METRICS],
        *[pl.col(m).quantile(0.1).alias(f"{m}_p10") for m in ("v_entry", "v_min", "retention", "recovery_time", "reacc")],
        *[pl.col(m).quantile(0.9).alias(f"{m}_p90") for m in ("v_entry", "v_min", "retention", "recovery_time", "reacc")],
        pl.col("recovery_censored").mean().alias("censored_share"), pl.col("near_stop").mean().alias("near_stop_share"),
        pl.col("entry_at_window_edge").mean().alias("entry_edge_share"), (pl.col("reacc_frames") < 3).mean().alias("reacc_short_share"))
        .sort("label"))

    # ---------------- D. reliability (reference + sensitivity) ----------------
    Wref = W_all.filter(pl.col("config") == "reference")
    rel_ref = reliability(Wref, feats, pos_map, B_REF, SEED).with_columns(pl.lit("reference").alias("config"))
    rel_sens = [rel_ref]
    for name in cfgs:
        if name == "reference":
            continue
        rel_sens.append(reliability(W_all.filter(pl.col("config") == name), PRIMARY, pos_map, B_SENS, SEED).with_columns(pl.lit(name).alias("config")))
    REL = pl.concat(rel_sens, how="diagonal_relaxed")
    REL.write_parquet(eout / "reliability.parquet")

    # sensitivity: template rate and rank agreement of player means vs reference
    sens_rows = []
    Pref = player_summaries(Wref, PRIMARY)
    for name in cfgs:
        Ac = A.filter(pl.col("config") == name)
        Wc = W_all.filter(pl.col("config") == name)
        Pc = player_summaries(Wc, PRIMARY)
        row = dict(config=name, template_rate=float((Ac["ok"] & Ac["template_ok"]).mean()))
        for f in PRIMARY:
            j = Pref.select("nfl_id", pl.col(f"{f}__mean").alias("r")).join(Pc.select("nfl_id", pl.col(f"{f}__mean").alias("c")), on="nfl_id").drop_nulls()
            row[f"rank_vs_ref_{f}"] = float(spearmanr(j["r"], j["c"]).statistic) if j.height > 5 else np.nan
            row[f"median_{f}"] = float(Wc[f].median()) if f in Wc.columns else np.nan
        sens_rows.append(row)
    SENS = pl.DataFrame(sens_rows, infer_schema_length=None)
    SENS.write_parquet(eout / "sensitivity.parquet")

    # ---------------- C. player-level summaries (reference) + aggregation comparison ----------------
    P = player_summaries(Wref, feats).join(players, on="nfl_id", how="left")
    P.write_parquet(dout / "player_features.parquet")
    agg_rows = []
    for f in PRIMARY:
        cols = [f"{f}__{s}" for s in ("mean", "median", "first", "best")]
        sub = P.filter(pl.col(f"{f}__n") >= 2).select(cols).drop_nulls()
        for i, c1 in enumerate(cols):
            for c2 in cols[i + 1:]:
                agg_rows.append(dict(feature=f, a=c1.split("__")[1], b=c2.split("__")[1], n=sub.height,
                                     spearman=float(spearmanr(sub[c1], sub[c2]).statistic) if sub.height > 5 else np.nan))
    AGG = pl.DataFrame(agg_rows); AGG.write_parquet(eout / "aggregation_agreement.parquet")

    # ---------------- E. conventional measures (descriptive) ----------------
    comp_rows = []
    for f in feats:
        col = f"{f}__mean"
        for c in CONVENTIONAL:
            d = P.select("nfl_id", "pos", col, c).drop_nulls()
            if d.height < 15:
                continue
            rho, lo, hi = spearman_ci(d[col], d[c], 1000, SEED)
            wx = within_position_ranks(d, col); wy = within_position_ranks(d, c)
            comp_rows.append(dict(feature=f, measure=c, n=d.height, spearman=rho, lo=lo, hi=hi,
                                  spearman_within_pos=float(np.corrcoef(wx, wy)[0, 1])))
    COMP = pl.DataFrame(comp_rows); COMP.write_parquet(eout / "conventional_comparison.parquet")
    # variance explained by position + official 40 + official 3-cone (OLS, players with all)
    r2_rows = []
    for f in feats:
        d = P.select(f"{f}__mean", "pos", "forty", "three_cone", "x_peak").drop_nulls()
        if d.height < 20:
            continue
        y = d[f"{f}__mean"].to_numpy()
        for name, cols in [("position", []), ("position+forty", ["forty"]), ("position+three_cone", ["three_cone"]),
                           ("position+forty+three_cone", ["forty", "three_cone"]), ("position+forty+three_cone+x_peak", ["forty", "three_cone", "x_peak"])]:
            X = np.column_stack([np.ones(len(y))] + [(d["pos"] == p).cast(int).to_numpy() for p in sorted(d["pos"].unique().to_list())[1:]]
                                + [d[c].to_numpy() for c in cols])
            beta, *_ = np.linalg.lstsq(X, y, rcond=None); res = y - X @ beta
            r2 = 1 - res.var() / y.var(); k = X.shape[1] - 1
            r2_rows.append(dict(feature=f, model=name, n=len(y), r2=float(r2), adj_r2=float(1 - (1 - r2) * (len(y) - 1) / (len(y) - k - 1))))
    R2 = pl.DataFrame(r2_rows); R2.write_parquet(eout / "conventional_r2.parquet")
    # inter-feature correlations (player means)
    inter = []
    for i, f1 in enumerate(feats):
        for f2 in feats[i + 1:]:
            d = P.select(f"{f1}__mean", f"{f2}__mean").drop_nulls()
            if d.height > 15:
                inter.append(dict(a=f1, b=f2, n=d.height, spearman=float(spearmanr(d[:, 0], d[:, 1]).statistic)))
    INTER = pl.DataFrame(inter); INTER.write_parquet(eout / "feature_intercorrelation.parquet")
    turn_desc.write_parquet(eout / "turn_descriptives.parquet")

    json.dump(dict(run=run, reference=params_dict(REF), sensitivity=SENSITIVITY, seed=SEED, B_ref=B_REF, B_sens=B_SENS,
                   join_run_for_x_peak=JOIN_RUN, primary=PRIMARY, secondary=SECONDARY,
                   outputs_data=str(dout.relative_to(ROOT)), outputs_experiment=str(eout.relative_to(ROOT))),
              open(eout / "config.json", "w"), indent=1)
    summary = dict(run=run, seconds=round(time.time() - t0, 1), audit=audit,
                   turn_descriptives=turn_desc.to_dicts(), reliability_reference=rel_ref.to_dicts(),
                   sensitivity=SENS.to_dicts(), aggregation=AGG.to_dicts(), conventional=COMP.to_dicts(),
                   conventional_r2=R2.to_dicts(), intercorrelation=INTER.to_dicts())
    json.dump(summary, open(eout / "summary.json", "w"), indent=1, default=float)
    (ROOT / "experiments" / "phase11_turn_recovery" / "LATEST").write_text(run)
    print(f"done in {time.time() - t0:.0f}s -> {eout}")


if __name__ == "__main__":
    main()
