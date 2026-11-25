"""Phase 15 Part B: DL pass-rush drill arc bend (measurement only; combine data only).

Side audit of repeated attempts, geometric arc, speed-separated bend measures (speed with the adopted analytic SG
correction; heading rate / curvature / radius / a_n uncorrected, per configs/phase15_arc_correction_decision.json),
common-speed-band curvature (band fixed from the pooled arc-frame speed distribution before any agreement statistic),
bilateral consistency, sensitivity. No NFL game data.

Usage: python scripts/run_phase15_dl_arc.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl
from scipy.stats import pearsonr, spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nfl_bdb.evaluation.repeatability import boot_two_attempt, centre_by_group, two_attempt_stats  # noqa: E402
from nfl_bdb.features.phase15_measures import ArcParams, arc_measures, arc_segment, sg_speed_gain  # noqa: E402

INTERIM = ROOT / "data" / "interim"
SEED = 1516
B = 2000
MEAS = ["speed_corr", "omega_deg", "curvature", "radius", "a_n", "band_curvature", "heading_deg"]
VARIANTS = {"reference": ArcParams(), "window=5": ArcParams(window=5), "window=9": ArcParams(window=9),
            "omega_arc=20": ArcParams(omega_arc_deg=20.0), "omega_arc=30": ArcParams(omega_arc_deg=30.0),
            "merge_gap=1": ArcParams(merge_gap=1), "merge_gap=3": ArcParams(merge_gap=3)}


def measure(x, y, p, band):
    u = arc_measures(x, y, p, band=band, correct=False)
    if u.get("valid"):
        c = arc_measures(x, y, p, band=band, correct=True)
        u["speed_corr"] = c["speed"]
        if band is not None:   # band defined on corrected speed: recompute membership with corrected speed
            seg = arc_segment(x, y, p); k = seg["kin"]; f = seg["frames"]
            v = k["speed"][f] / sg_speed_gain(np.abs(k["omega"][f]), p.window); w = np.abs(k["omega"][f])
            m = (v >= band[0]) & (v <= band[1])
            u["band_frames"] = int(m.sum()); u["band_curvature"] = float(np.median((w / k["speed"][f])[m])) if m.sum() >= 3 else np.nan
    return u


def bilateral(df, meas, label):
    """df: one row per athlete with <meas>_left, <meas>_right, draft_year, weight_group."""
    out = []
    for m in meas:
        d = df.select("nfl_id", "draft_year", "weight_group", f"{m}_left", f"{m}_right").drop_nulls()
        d = d.filter(pl.col(f"{m}_left").is_not_nan() & pl.col(f"{m}_right").is_not_nan())
        if d.height < 10:
            out.append(dict(sample=label, measure=m, n=d.height)); continue
        L, R = d[f"{m}_left"].to_numpy(), d[f"{m}_right"].to_numpy()
        st = two_attempt_stats(L, R); ci = boot_two_attempt(L, R, None, stats=("icc31", "icc21"), B=B, seed=SEED)
        yr = d["draft_year"].to_numpy()
        Ly, Ry = centre_by_group(L, R, yr); sty = two_attempt_stats(Ly, Ry)
        ciy = boot_two_attempt(L, R, yr, stats=("icc31",), B=B, seed=SEED)
        rng = np.random.default_rng(SEED); n = len(L)
        bd = [np.mean((L - R)[j]) for j in (rng.integers(0, n, n) for _ in range(B))]
        asym = (L - R) / ((L + R) / 2)
        out.append(dict(sample=label, measure=m, n=n, left_mean=float(L.mean()), left_sd=float(L.std(ddof=1)), right_mean=float(R.mean()),
                        right_sd=float(R.std(ddof=1)), mean_diff_LminusR=float(np.mean(L - R)), mean_diff_lo=float(np.percentile(bd, 2.5)),
                        mean_diff_hi=float(np.percentile(bd, 97.5)), abs_diff_median=float(np.median(np.abs(L - R))),
                        asym_median=float(np.median(asym)), asym_iqr_lo=float(np.percentile(asym, 25)), asym_iqr_hi=float(np.percentile(asym, 75)),
                        abs_asym_median=float(np.median(np.abs(asym))), pearson=float(pearsonr(L, R).statistic), spearman=float(spearmanr(L, R).statistic),
                        icc31=st["icc31"], icc31_lo=ci["icc31"][0], icc31_hi=ci["icc31"][1], icc21=st["icc21"], icc21_lo=ci["icc21"][0], icc21_hi=ci["icc21"][1],
                        icc31_year_centred=sty["icc31"], icc31_year_centred_lo=ciy["icc31"][0], icc31_year_centred_hi=ciy["icc31"][1],
                        sb_bilateral_if_parallel=float(2 * st["icc31"] / (1 + st["icc31"])) if st["icc31"] > -1 else np.nan,
                        te=st["te"], te_pct=st["te_pct"]))
    return out


def main():
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dout = INTERIM / "phase15" / run; eout = ROOT / "experiments" / "phase15" / f"dl_{run}"
    dout.mkdir(parents=True, exist_ok=True); eout.mkdir(parents=True); t0 = time.time()
    ct = pl.read_parquet(INTERIM / "combine_tracking.parquet").filter(
        (pl.col("drill_type") == "SKILL_DRILLS_DL") & (pl.col("drill_name") == "PASS_RUSH_DRILL") & (pl.col("entity_type") == "PLAYER")).sort("event_id", "time")
    cr = pl.read_parquet(INTERIM / "combine_results.parquet").select("nfl_id", "combine_position", "combine_weight")
    med_w = cr.filter(pl.col("combine_position") == "DL")["combine_weight"].median()
    cr = cr.with_columns(pl.when(pl.col("combine_weight") >= med_w).then(pl.lit("heavier")).otherwise(pl.lit("lighter")).alias("weight_group"))
    atts = [(eid, g) for (eid,), g in ct.group_by(["event_id"], maintain_order=True)]

    # step 1: common speed band from pooled valid-arc frames (reference parameters, corrected speed)
    pooled = []
    for _, g in atts:
        seg = arc_segment(g["x"].to_numpy(), g["y"].to_numpy(), ArcParams())
        if seg.get("valid"):
            k = seg["kin"]; f = seg["frames"]
            pooled += list(k["speed"][f] / sg_speed_gain(np.abs(k["omega"][f]), 7))
    band = tuple(float(q) for q in np.percentile(pooled, [25, 75]))
    json.dump(dict(band=band, rule="interquartile range of pooled corrected speeds over all valid-arc frames (reference parameters)", n_frames=len(pooled)),
              open(eout / "speed_band.json", "w"), indent=1)

    rows = []
    for eid, g in atts:
        x, y = g["x"].to_numpy(), g["y"].to_numpy()
        base = dict(event_id=eid, nfl_id=int(g["nfl_id"][0]), draft_year=int(g["draft_year"][0]), attempt=int(g["attempt"][0]), t0=g["time"][0], n_frames=len(x))
        for name, p in VARIANTS.items():
            m = measure(x, y, p, band)
            rows.append(dict(base, variant=name, **{k: m.get(k) for k in ("found", "valid", "reason", "start", "end", "n_frames", "side", "truncated", "band_frames",
                                                                          "v_min_arc", "v_max_arc")}, **{k: m.get(k, np.nan) for k in MEAS}))
    A = (pl.DataFrame(rows, infer_schema_length=None).rename({"n_frames": "arc_frames"}).join(cr, on="nfl_id", how="left")
         .sort("nfl_id", "variant", "t0").with_columns(pl.int_range(pl.len()).over("nfl_id", "variant").alias("order")))
    A.write_parquet(dout / "dl_arc_attempts.parquet")
    R0 = A.filter(pl.col("variant") == "reference")
    summ = dict(run=run, band=band, weight_median=float(med_w))

    # B1: what are attempts 1 and 2?
    pairs = R0.filter(pl.col("order") < 2).group_by("nfl_id").agg(pl.col("side").sort_by("order"), pl.col("valid").sort_by("order"), pl.len().alias("k"),
                                                                  pl.col("draft_year").first())
    two = pairs.filter(pl.col("k") == 2)
    def ptype(s):
        if s[0] is None or s[1] is None:
            return "side_unknown"
        return "left_right" if s[0] != s[1] else f"same_side_{s[0]}"
    two = two.with_columns(pl.col("side").map_elements(ptype, return_dtype=pl.Utf8).alias("pair_type"))
    summ["attempt_audit"] = dict(
        attempts=R0.height, athletes=int(R0["nfl_id"].n_unique()), attempts_per_athlete={str(k): int(v) for k, v in R0.group_by("nfl_id").agg(pl.len().alias("k")).group_by("k").agg(pl.len().alias("c")).sort("k").iter_rows()},
        valid=int(R0["valid"].sum()), invalid_reasons={str(k): int(v) for k, v in R0.filter(~pl.col("valid")).group_by("reason").len().iter_rows()},
        sides_all={str(k): int(v) for k, v in R0.group_by("side").len().iter_rows()},
        sides_valid={str(k): int(v) for k, v in R0.filter(pl.col("valid")).group_by("side").len().iter_rows()},
        pair_types={str(k): int(v) for k, v in two.group_by("pair_type").len().iter_rows()},
        pair_types_by_year={str(y): {str(k): int(v) for k, v in two.filter(pl.col("draft_year") == y).group_by("pair_type").len().iter_rows()} for y in (2023, 2024, 2025)},
        first_attempt_side={str(k): int(v) for k, v in R0.filter(pl.col("order") == 0).group_by("side").len().iter_rows()},
        attempt_index_vs_side={f"{a}|{s}": int(v) for a, s, v in R0.group_by("attempt", "side").len().sort("attempt", "side").iter_rows()})

    # B2/B3 descriptives (valid, reference)
    V = R0.filter(pl.col("valid"))
    desc = []
    for side in ("left", "right", None):
        d = V if side is None else V.filter(pl.col("side") == side)
        for m in MEAS + ["arc_frames"]:
            x = d[m].drop_nulls().drop_nans().to_numpy().astype(float)
            desc.append(dict(side=side or "both", measure=m, n=len(x), mean=float(x.mean()), sd=float(x.std(ddof=1)),
                             p05=float(np.percentile(x, 5)), median=float(np.median(x)), p95=float(np.percentile(x, 95))))
    pl.DataFrame(desc).write_csv(eout / "dl_arc_descriptives.csv")
    summ["band_coverage"] = dict(valid_attempts=V.height, with_ge3_band_frames=int((V["band_frames"].fill_null(0) >= 3).sum()),
                                 arc_speed_range_covers_band=int(((V["v_min_arc"] <= band[0]) & (V["v_max_arc"] >= band[1])).sum()))
    # speed-curvature coupling across attempts (descriptive)
    summ["coupling"] = {f"{a}~{b}": float(spearmanr(V[a].to_numpy(), V[b].to_numpy(), nan_policy="omit").statistic)
                        for a, b in (("speed_corr", "curvature"), ("speed_corr", "a_n"), ("curvature", "a_n"), ("radius", "a_n"), ("heading_deg", "curvature"))}

    # B5 bilateral: first valid attempt per side
    bil_rows = []
    for name in VARIANTS:
        Vv = A.filter((pl.col("variant") == name) & pl.col("valid"))
        fs = Vv.sort("nfl_id", "order").group_by("nfl_id", "side", maintain_order=True).first()
        wide = fs.pivot(index=["nfl_id", "draft_year", "weight_group"], on="side", values=MEAS)
        wide = wide.rename({c: c.replace("_left", "_left").replace("_right", "_right") for c in wide.columns})
        if name == "reference":
            wide.write_parquet(dout / "dl_bilateral_wide.parquet")
            bil_rows += bilateral(wide, MEAS, "all")
            for yr in (2023, 2024, 2025):
                bil_rows += bilateral(wide.filter(pl.col("draft_year") == yr), ["speed_corr", "curvature", "a_n", "radius"], f"year={yr}")
            for wg in ("lighter", "heavier"):
                bil_rows += bilateral(wide.filter(pl.col("weight_group") == wg), ["speed_corr", "curvature", "a_n", "radius"], f"weight={wg}")
        else:
            bil_rows += bilateral(wide, ["speed_corr", "curvature", "a_n", "radius", "band_curvature"], f"variant={name}")
    pl.DataFrame(bil_rows, infer_schema_length=None).write_csv(eout / "dl_bilateral.csv")

    # genuine same-side repeats (test-retest), if any
    ss = R0.filter(pl.col("valid")).sort("nfl_id", "order").group_by("nfl_id", "side").agg(*[pl.col(m) for m in MEAS], pl.len().alias("k")).filter(pl.col("k") >= 2)
    tr = []
    for m in ["speed_corr", "curvature", "a_n", "radius"]:
        a = np.array([v[0] for v in ss[m].to_list()], float) if ss.height else np.array([])
        b = np.array([v[1] for v in ss[m].to_list()], float) if ss.height else np.array([])
        ok = ~(np.isnan(a) | np.isnan(b)) if len(a) else np.array([], bool)
        r = dict(measure=m, n_same_side_pairs=int(ok.sum()))
        if ok.sum() >= 10:
            st = two_attempt_stats(a[ok], b[ok]); r.update(icc31=st["icc31"], te_pct=st["te_pct"])
        tr.append(r)
    summ["same_side_repeats"] = tr
    summ["seconds"] = round(time.time() - t0)
    json.dump(dict(run=run, seed=SEED, B=B, variants={k: v.__dict__ for k, v in VARIANTS.items()}, measures=MEAS), open(eout / "dl_config.json", "w"), indent=1, default=str)
    json.dump(summ, open(eout / "dl_summary.json", "w"), indent=1, default=str)
    (ROOT / "experiments" / "phase15" / "LATEST_dl").write_text(f"dl_{run}")
    print(f"done in {time.time() - t0:.0f}s -> {eout}")


if __name__ == "__main__":
    main()
