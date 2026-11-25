"""Phase 15 B4: synthetic validation of arc speed / heading rate / curvature / radius / centripetal acceleration
under 10 Hz sampling, Combine coordinate precision and SG smoothing. Simulation only; no real-athlete data.

  python scripts/run_phase15_arc_synthetic.py dev       # seeds 101-103: decide whether to adopt the speed correction
  python scripts/run_phase15_arc_synthetic.py holdout   # seeds 2001-2003: final bias / SD (reads the dev decision)

Pre-stated adoption rule (applied on dev only): adopt the analytic SG speed correction for a quantity if, at window 7,
in every noise scenario, the corrected |median relative error| <= 0.02 and the corrected SD of the relative error is
<= 1.2 x the uncorrected SD. Otherwise report uncorrected estimates with the held-out error as a bound.
Truth = true values at the frames the detector selected (measurement error of the kinematics); a second truth
(constant-curvature part: true radius R and true speed there) adds the segmentation effect.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nfl_bdb.features.phase15_measures import ArcParams, arc_measures  # noqa: E402
from nfl_bdb.simulation.arc_synth import draw_arc_trial, sample_arc, simulate_arc  # noqa: E402

SEEDS = {"dev": [101, 102, 103], "holdout": [2001, 2002, 2003]}
N_PER_SEED = 300
SCEN = [("none", "gauss", 0.0), ("quant30", "quant30", 0.002), ("gauss002", "gauss", 0.002), ("gauss005", "gauss", 0.005)]
QTY = ["speed", "omega_deg", "curvature", "radius", "a_n"]


def run(stage):
    rows = []
    for seed in SEEDS[stage]:
        rng = np.random.default_rng(seed)
        for i in range(N_PER_SEED):
            tr = draw_arc_trial(rng); sim = simulate_arc(tr); phase = rng.uniform(0, 0.1)
            const = sim["const"]; R_true = tr.R; v_const = float(np.median(sim["speed"][const]))
            for si, (sn, kind, sig) in enumerate(SCEN):
                sm = sample_arc(sim, phase, kind, sig, np.random.default_rng([seed, i, si]))
                for w in (5, 7, 9):
                    for corr in (False, True):
                        m = arc_measures(sm["x"], sm["y"], ArcParams(window=w), correct=corr)
                        row = dict(stage=stage, seed=seed, trial=i, scenario=sn, window=w, corrected=corr, R=tr.R, v0=tr.v0, a_t=tr.a_t,
                                   ramp=tr.ramp, dtheta=tr.dtheta_deg, phase=phase, valid=bool(m.get("valid")), reason=m.get("reason"),
                                   side_ok=(m.get("side") == ("left" if tr.direction == 1 else "right")) if m.get("found") else None)
                        if m.get("valid"):
                            f = np.arange(m["start"], m["end"] + 1)
                            truth = dict(speed=np.median(sm["speed"][f]), omega_deg=np.degrees(np.median(sm["omega"][f])),
                                         curvature=np.median(sm["kappa"][f]), a_n=np.median(sm["a_n"][f]))
                            truth["radius"] = 1.0 / truth["curvature"] if truth["curvature"] > 0 else np.nan
                            for q in QTY:
                                row[f"err_{q}"] = m[q] / truth[q] - 1
                            row["err_radius_vs_R"] = m["radius"] / R_true - 1
                            row["err_speed_vs_const"] = m["speed"] / v_const - 1
                            row["err_a_n_vs_const"] = m["a_n"] / (v_const ** 2 / R_true) - 1
                        rows.append(row)
    return pl.DataFrame(rows, infer_schema_length=None)


def summarise(D):
    cols = [c for c in D.columns if c.startswith("err_")]
    return (D.group_by("scenario", "window", "corrected").agg(pl.col("valid").mean().alias("valid_rate"), pl.col("side_ok").mean().alias("side_correct"),
            *[pl.col(c).drop_nans().median().alias(f"{c}_median") for c in cols], *[pl.col(c).drop_nans().std().alias(f"{c}_sd") for c in cols],
            *[pl.col(c).drop_nans().abs().quantile(0.9).alias(f"{c}_abs_p90") for c in cols]).sort("scenario", "window", "corrected"))


def main():
    stage = sys.argv[1]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "experiments" / "phase15" / f"arc_{stage}_{run_id}"; out.mkdir(parents=True)
    D = run(stage); D.write_parquet(out / "rows.parquet")
    S = summarise(D); S.write_csv(out / "summary.csv")
    # error by geometry (window 7, quant30)
    g = D.filter((pl.col("window") == 7) & (pl.col("scenario") == "quant30"))
    by = []
    for fac, bins in (("R", [3.0, 4.0]), ("ramp", [0.2, 0.3]), ("dtheta", [90, 120]), ("v0", [3.67, 4.33]), ("phase", [0.033, 0.067])):
        x = g.with_columns(pl.col(fac).cut(bins).alias("bin"))
        for (b, c), h in x.group_by("bin", "corrected", maintain_order=True):
            by.append(dict(factor=fac, bin=str(b), corrected=c, n=h.height, **{f"{q}_median": float(h[f"err_{q}"].drop_nans().median()) for q in ("speed", "curvature", "radius", "a_n")},
                           **{f"{q}_sd": float(h[f"err_{q}"].drop_nans().std()) for q in ("speed", "curvature", "radius", "a_n")}))
    pl.DataFrame(by).write_csv(out / "error_by_geometry.csv")
    decision = {}
    if stage == "dev":
        for q in QTY:
            ok = True
            for sn, _, _ in SCEN:
                u = S.filter((pl.col("scenario") == sn) & (pl.col("window") == 7) & ~pl.col("corrected")).row(0, named=True)
                c = S.filter((pl.col("scenario") == sn) & (pl.col("window") == 7) & pl.col("corrected")).row(0, named=True)
                if abs(c[f"err_{q}_median"]) > 0.02 or c[f"err_{q}_sd"] > 1.2 * u[f"err_{q}_sd"]:
                    ok = False
            decision[q] = "adopt_correction" if ok else "report_uncorrected_with_bound"
        json.dump(dict(stage=stage, run=run_id, rule=__doc__.split("Pre-stated adoption rule")[1].split("Truth")[0].strip(), decision=decision),
                  open(ROOT / "configs" / "phase15_arc_correction_decision.json", "w"), indent=1)
    json.dump(dict(stage=stage, run=run_id, seeds=SEEDS[stage], n_per_seed=N_PER_SEED, scenarios=SCEN, decision=decision), open(out / "meta.json", "w"), indent=1)
    (ROOT / "experiments" / "phase15" / f"LATEST_arc_{stage}").write_text(out.name)
    print("done", out, decision)


if __name__ == "__main__":
    main()
