"""Phase 13 synthetic method validation (no real-athlete data, no outcomes).

  python scripts/run_phase13_synthetic.py dev       # development seeds 101-103: E3 smoothing choice only
  python scripts/run_phase13_synthetic.py holdout   # held-out seeds 2001-2003: final evaluation

The holdout stage reads its E3 smoothing parameter and the pre-specified selection criteria from
configs/phase13_selection_protocol.json, written and committed after the dev stage and before holdout.
Outputs (aggregate only; synthetic) in experiments/phase13_ct_accel/<stage>_<run>/.
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from multiprocessing import get_context
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DEV_SEEDS = [101, 102, 103]
HOLDOUT_SEEDS = [2001, 2002, 2003]
LAM_GRID = [None, 1e-5, 3e-5, 1e-4, 3e-4, 1e-3]
GEN = dict(A0_mean=9.5, A0_cv=0.08, V_mean=9.0, V_cv=0.03, sway_max=0.15, step_max=0.4)
# noise scenarios: (name, kind, sigma, step_max)
SCEN_10HZ = [("ideal", "gauss", 0.0, 0.0), ("gauss0", "gauss", 0.0, 0.4), ("gauss0025", "gauss", 0.0025, 0.4),
             ("gauss005", "gauss", 0.005, 0.4), ("gauss01", "gauss", 0.01, 0.4), ("gauss02", "gauss", 0.02, 0.4),
             ("gauss03", "gauss", 0.03, 0.4), ("quant30", "quant30", 0.002, 0.4),
             ("quant30_nostep", "quant30", 0.002, 0.0), ("quant30_step08", "quant30", 0.002, 0.8)]
CALIBRATED = ["quant30", "gauss005"]
HIGH_FS = [20.0, 50.0]
HIGH_FS_SCEN = ["ideal", "gauss0", "gauss005"]


def _work(args):
    """One athlete: two trials, every scenario. Returns list of row dicts."""
    seed, ai, lams, B_scen, B = args
    from nfl_bdb.features.exit_accel_candidates import e1_e2, e3
    from nfl_bdb.simulation.shuttle_synth import Athlete, draw_trial, sample, simulate
    rng = np.random.default_rng([seed, ai])
    ath = Athlete(float(rng.normal(GEN["A0_mean"], GEN["A0_mean"] * GEN["A0_cv"])),
                  float(rng.normal(GEN["V_mean"], GEN["V_mean"] * GEN["V_cv"])))
    rows = []
    for trial in (0, 1):
        sims = {}
        for si, (sname, kind, sig, step) in enumerate(SCEN_10HZ):
            key = step
            if key not in sims:
                trng = np.random.default_rng([seed, ai, trial, 7])          # same trial geometry across scenarios
                tp = draw_trial(trng, GEN["sway_max"], step)
                sims[key] = (tp, simulate(ath, tp))
            tp, sim = sims[key]
            tr = sim["truth"]
            prng = np.random.default_rng([seed, ai, trial, 11])
            phase = prng.uniform(0, 0.1)
            for fs in [10.0] + (HIGH_FS if sname in HIGH_FS_SCEN else []):
                srng = np.random.default_rng([seed, ai, trial, int(fs), si])
                sm = sample(sim, fs, phase % (1.0 / fs), kind, sig, srng)
                r = e1_e2(sm["x"], sm["y"], sm["s"], fs)
                base = dict(seed=seed, athlete=ai, trial=trial, scenario=sname, fs=fs, phase=phase % (1.0 / fs),
                            T_turn=tp.T_turn, W=tp.W, A0=ath.A0, V=ath.V, **{k: tr[k] for k in ("theta_05", "theta_27", "t_exit", "t_min", "v_min", "v_exit")},
                            e1=r["e1"], e1_lo=r["e1_lo"], e1_hi=r["e1_hi"], e2=r["e2"], e2_lo=r["e2_lo"], e2_hi=r["e2_hi"],
                            e1_exit_err=r["e1_exit"] + sm["t0"] - tr["t_exit"], e2_exit_err=r["e2_exit"] + sm["t0"] - tr["t_exit"],
                            e12_reason=r["reason"])
                for lam in lams:
                    b = B if (sname in B_scen and fs == 10.0) else 0
                    q = e3(sm["x"], sm["y"], sm["s"], fs, lam=lam, B=b, rng=np.random.default_rng([seed, ai, trial, 99]), pre=r)
                    rows.append(dict(base, lam=("gcv" if lam is None else lam), e3=q["e3"], e3_lo=q["e3_lo"], e3_hi=q["e3_hi"],
                                     e3_exit_err=q["e3_exit"] + sm["t0"] - tr["t_exit"] if not np.isnan(q["e3_exit"]) else np.nan,
                                     e3_reason=q["e3_reason"]))
    return rows


def simulate_set(seeds, n_ath, lams, B_scen, B):
    jobs = [(s, a, lams, B_scen, B) for s in seeds for a in range(n_ath)]
    rows = []
    with ProcessPoolExecutor(max_workers=4, mp_context=get_context("spawn")) as ex:
        for r in ex.map(_work, jobs, chunksize=4):
            rows += r
    return rows


def metrics(df, est, truth, lo=None, hi=None):
    import polars as pl
    d = df.with_columns((pl.col(est) - pl.col(truth)).alias("_err"))
    ok = d.filter(pl.col(est).is_not_nan())
    n_all = d.height; n_ok = ok.height
    out = dict(n=n_all, failure_rate=1 - n_ok / n_all if n_all else np.nan)
    if n_ok < 10:
        return out
    e = ok["_err"].to_numpy(); tru = ok[truth].to_numpy(); es = ok[est].to_numpy()
    var_t = tru.var(); var_e = e.var()
    from scipy.stats import spearmanr
    out.update(bias=float(e.mean()), mae=float(np.abs(e).mean()), rmse=float(np.sqrt((e ** 2).mean())), sd_true=float(np.sqrt(var_t)),
               sd_err=float(np.sqrt(var_e)), R_meas=float(var_t / (var_t + var_e)), spearman_trial=float(spearmanr(tru, es).statistic))
    if lo is not None:
        c = ok.filter(pl.col(lo).is_not_nan())
        if c.height >= 10:
            out["coverage95"] = float(((c[lo] <= c[truth]) & (c[truth] <= c[hi])).mean())
            out["ci_width_median"] = float((c[hi] - c[lo]).median())
    # athlete level: two trials
    from nfl_bdb.evaluation.repeatability import two_attempt_stats
    w = ok.group_by("seed", "athlete").agg(pl.col(est).sort_by("trial"), pl.col("A0").first(), pl.col(truth).mean().alias("_tm")).filter(pl.col(est).list.len() == 2)
    if w.height >= 10:
        a = np.array([v[0] for v in w[est].to_list()]); b = np.array([v[1] for v in w[est].to_list()])
        st = two_attempt_stats(a, b)
        out.update(n_athletes=w.height, synth_icc31=st["icc31"], synth_icc21=st["icc21"], synth_te=st["te"],
                   spearman_athlete_A0=float(spearmanr((a + b) / 2, w["A0"]).statistic),
                   spearman_athlete_truth=float(spearmanr((a + b) / 2, w["_tm"]).statistic))
    return out


def summarise(rows, lam_sel=None):
    import polars as pl
    D = pl.DataFrame(rows, infer_schema_length=None).with_columns(pl.col("lam").cast(pl.Utf8))
    out = []
    for (sc, fs, lam), g in D.group_by("scenario", "fs", "lam", maintain_order=True):
        if lam_sel is not None and lam != lam_sel:
            continue
        for name, est, truth, lo, hi in (("E1", "e1", "theta_05", "e1_lo", "e1_hi"), ("E2", "e2", "theta_05", "e2_lo", "e2_hi"),
                                        ("E3", "e3", "theta_27", "e3_lo", "e3_hi")):
            if name != "E3" and lam != D["lam"][0]:
                continue                     # E1/E2 do not depend on lam: report once
            out.append(dict(scenario=sc, fs=fs, estimator=name, lam=lam if name == "E3" else "", **metrics(g, est, truth, lo, hi)))
    return D, pl.DataFrame(out, infer_schema_length=None)


def by_factor(D, lam, factor, bins):
    import polars as pl
    d = D.filter((pl.col("scenario") == "quant30") & (pl.col("fs") == 10.0) & (pl.col("lam") == lam))
    d = d.with_columns(pl.col(factor).cut(bins).alias("_bin"))
    rows = []
    for (b,), g in d.group_by(["_bin"], maintain_order=True):
        for name, est, truth in (("E1", "e1", "theta_05"), ("E2", "e2", "theta_05"), ("E3", "e3", "theta_27")):
            e = (g[est] - g[truth]).drop_nans().to_numpy()
            rows.append(dict(factor=factor, bin=str(b), estimator=name, n=len(e), bias=float(e.mean()) if len(e) else np.nan,
                             rmse=float(np.sqrt((e ** 2).mean())) if len(e) else np.nan))
    return rows


def main():
    import polars as pl
    stage = sys.argv[1]
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "experiments" / "phase13_ct_accel" / f"{stage}_{run}"; out.mkdir(parents=True)
    t0 = time.time()
    if stage == "dev":
        rows = simulate_set(DEV_SEEDS, 100, LAM_GRID, [], 0)
        D, S = summarise(rows)
        S.write_csv(out / "summary.csv")
        cal = S.filter((pl.col("estimator") == "E3") & pl.col("scenario").is_in(CALIBRATED) & (pl.col("fs") == 10.0))
        choice = cal.group_by("lam").agg(pl.col("rmse").mean().alias("rmse_cal")).sort("rmse_cal")
        choice.write_csv(out / "e3_lambda_choice.csv")
        json.dump(dict(stage=stage, seeds=DEV_SEEDS, n_athletes_per_seed=100, gen=GEN, lam_grid=[str(x) for x in LAM_GRID],
                       rule="E3 lambda = argmin mean RMSE vs theta_27 over calibrated scenarios (quant30, gauss005) at 10 Hz",
                       chosen=choice.row(0, named=True), seconds=round(time.time() - t0)), open(out / "dev.json", "w"), indent=1)
    elif stage == "holdout":
        proto = json.load(open(ROOT / "configs" / "phase13_selection_protocol.json"))
        lam = proto["e3_lambda"]; lam_v = None if lam == "gcv" else float(lam)
        rows = simulate_set(HOLDOUT_SEEDS, 200, [lam_v], CALIBRATED, proto["bootstrap_B"])
        D, S = summarise(rows)
        S.write_csv(out / "summary.csv")
        lam_s = D["lam"][0]
        F = pl.DataFrame(by_factor(D, lam_s, "phase", [0.02, 0.04, 0.06, 0.08]) + by_factor(D, lam_s, "T_turn", [0.25, 0.35]) +
                         by_factor(D, lam_s, "W", [0.2, 0.35]))
        F.write_csv(out / "error_by_factor.csv")
        # pre-specified decision
        dec = {}
        for est in ("E1", "E2", "E3"):
            s = S.filter((pl.col("estimator") == est) & (pl.col("fs") == 10.0))
            g = {r["scenario"]: r for r in s.iter_rows(named=True)}
            req = all(g[c]["R_meas"] >= proto["criteria"]["R_meas_min"] and abs(g[c]["bias"]) <= proto["criteria"]["abs_bias_max"]
                      and g[c]["failure_rate"] <= proto["criteria"]["failure_max"] for c in CALIBRATED)
            cov = all(proto["criteria"]["coverage_range"][0] <= g[c].get("coverage95", np.nan) <= proto["criteria"]["coverage_range"][1] for c in CALIBRATED)
            rob = g["gauss02"]["R_meas"] >= proto["criteria"]["R_meas_min_at_2x_noise"]
            dec[est] = dict(required_pass=bool(req), coverage_pass=bool(cov), robustness_pass=bool(rob),
                            R_meas_calibrated=[g[c]["R_meas"] for c in CALIBRATED], bias_calibrated=[g[c]["bias"] for c in CALIBRATED],
                            failure_calibrated=[g[c]["failure_rate"] for c in CALIBRATED],
                            coverage_calibrated=[g[c].get("coverage95") for c in CALIBRATED], R_meas_gauss02=g["gauss02"]["R_meas"])
        passing = [e for e in dec if dec[e]["required_pass"]]
        selected = max(passing, key=lambda e: np.mean(dec[e]["R_meas_calibrated"])) if passing else None
        json.dump(dict(stage=stage, seeds=HOLDOUT_SEEDS, n_athletes_per_seed=200, gen=GEN, protocol=proto, decision=dec,
                       selected=selected, stage_E_pass=selected is not None, seconds=round(time.time() - t0)),
                  open(out / "holdout.json", "w"), indent=1, default=float)
    D.write_parquet(out / "rows.parquet")
    (ROOT / "experiments" / "phase13_ct_accel" / f"LATEST_{stage}").write_text(out.name)
    print(f"done {stage} in {time.time() - t0:.0f}s -> {out}")


if __name__ == "__main__":
    main()
