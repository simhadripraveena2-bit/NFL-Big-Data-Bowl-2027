"""Phase 16 B: synthetic validation of route-launch onset and launch acceleration (simulation only).

  python scripts/run_phase16_launch_synthetic.py dev
  python scripts/run_phase16_launch_synthetic.py holdout

Athletes A0 ~ N(8.0, 8% CV), V ~ N(9.0, 3% CV); 10 trials ("routes") per athlete with independent effort, force
ramp, step oscillation, sway, recording offset and sampling phase. Criteria: configs/phase16_protocol.json.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nfl_bdb.features.launch import launch  # noqa: E402
from nfl_bdb.simulation.start_synth import draw_start_trial, sample_start, simulate_start  # noqa: E402

SEEDS = {"dev": [101, 102, 103], "holdout": [2001, 2002, 2003]}
N_ATH = 60
N_TRIALS = 10
SCEN = [("none", "gauss", 0.0, 0.4), ("quant30", "quant30", 0.002, 0.4), ("gauss002", "gauss", 0.002, 0.4),
        ("gauss005", "gauss", 0.005, 0.4), ("gauss01", "gauss", 0.01, 0.4), ("quant30_nostep", "quant30", 0.002, 0.0),
        ("quant30_step08", "quant30", 0.002, 0.8)]
CAL = ["quant30", "gauss005"]


def run(stage):
    rows = []
    for seed in SEEDS[stage]:
        rng = np.random.default_rng(seed)
        for a in range(N_ATH):
            A0 = rng.normal(8.0, 0.64); V = rng.normal(9.0, 0.27)
            for k in range(N_TRIALS):
                trng = np.random.default_rng([seed, a, k])
                for si, (sn, kind, sig, step) in enumerate(SCEN):
                    tr = draw_start_trial(np.random.default_rng([seed, a, k, 1]), A0, V, step_max=step)
                    sim = simulate_start(tr)
                    phase = np.random.default_rng([seed, a, k, 2]).uniform(0, 0.1)
                    for w in (5, 7, 9):
                        sm = sample_start(sim, phase, kind, sig, np.random.default_rng([seed, a, k, si, w]))
                        L = launch(sm["x"], sm["y"], window=w)
                        tt = sim["truth"]
                        row = dict(seed=seed, athlete=a, trial=k, scenario=sn, window=w, phase=phase, rec_offset=tr.rec_offset,
                                   ramp=tr.ramp, step_amp=tr.step_amp, A0=A0, A_eff=tt["A_eff"], truth_trend=tt["launch_p95_trend"],
                                   truth_inst=tt["launch_p95_inst"], valid=L["valid"], reason=L["reason"])
                        if L["valid"]:
                            row.update(est=L["p95"], est_mean=L["mean_at"], onset_err=sm["ts"][0] + L["onset_time"] - tt["t_onset"],
                                       onset_err_interp=sm["ts"][0] + L["onset_time_interp"] - tt["t_onset"])
                        rows.append(row)
    return pl.DataFrame(rows, infer_schema_length=None)


def summarise(D):
    out = []
    for (sn, w), g in D.group_by("scenario", "window", maintain_order=True):
        v = g.filter(pl.col("valid"))
        # trials whose recording started after the onset are expected rejections, reported separately
        late = g.filter(pl.col("rec_offset") <= 0.0)
        e = (v["est"] / v["truth_trend"] - 1).to_numpy(); err = (v["est"] - v["truth_trend"]).to_numpy(); tru = v["truth_trend"].to_numpy()
        res = err - err.mean()
        ath = v.group_by("seed", "athlete").agg(pl.col("est").mean(), pl.col("A0").first(), pl.len().alias("k")).filter(pl.col("k") >= 5)
        out.append(dict(scenario=sn, window=w, n=g.height, failure_rate=float(1 - g["valid"].mean()),
                        failure_rate_recording_before_onset=float(1 - g.filter(pl.col("rec_offset") > 0.15)["valid"].mean()),
                        late_start_rejected=float(1 - late["valid"].mean()) if late.height else None,
                        onset_err_median=float(v["onset_err"].median()), onset_err_sd=float(v["onset_err"].std()),
                        onset_err_abs_p90=float(v["onset_err"].abs().quantile(0.9)),
                        onset_err_interp_median=float(v["onset_err_interp"].median()),
                        rel_bias_trend=float(np.median(e)), rel_sd_trend=float(np.std(e)), rmse_trend=float(np.sqrt(np.mean(err ** 2))),
                        reliability_trend=float(tru.var() / (tru.var() + res.var())),
                        spearman_trial_trend=float(spearmanr(v["est"], v["truth_trend"]).statistic),
                        rel_bias_inst=float(np.median(v["est"] / v["truth_inst"] - 1)),
                        spearman_trial_inst=float(spearmanr(v["est"], v["truth_inst"]).statistic),
                        spearman_trial_A_eff=float(spearmanr(v["est"], v["A_eff"]).statistic),
                        spearman_athlete_A0=float(spearmanr(ath["est"], ath["A0"]).statistic), n_athletes=ath.height))
    return pl.DataFrame(out)


def by_factor(D):
    g = D.filter((pl.col("scenario") == "quant30") & (pl.col("window") == 7) & pl.col("valid"))
    rows = []
    for fac, bins in (("phase", [0.025, 0.05, 0.075]), ("ramp", [0.18, 0.27]), ("step_amp", [0.13, 0.27]), ("rec_offset", [0.1, 0.3])):
        x = g.with_columns(pl.col(fac).cut(bins).alias("bin"))
        for (b,), h in x.group_by(["bin"], maintain_order=True):
            e = (h["est"] / h["truth_trend"] - 1).to_numpy()
            rows.append(dict(factor=fac, bin=str(b), n=h.height, rel_bias=float(np.median(e)), rel_sd=float(np.std(e)),
                             onset_err_median=float(h["onset_err"].median()), onset_err_sd=float(h["onset_err"].std())))
    return pl.DataFrame(rows)


def main():
    stage = sys.argv[1]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "experiments" / "phase16" / f"synthetic_{stage}_{run_id}"; out.mkdir(parents=True)
    D = run(stage); D.write_parquet(out / "rows.parquet")
    S = summarise(D); S.write_csv(out / "summary.csv"); by_factor(D).write_csv(out / "error_by_factor.csv")
    res = {}
    if stage == "holdout":
        P = json.load(open(ROOT / "configs" / "phase16_protocol.json"))["synthetic_acceptance"]["criteria_holdout"]
        for sn in CAL:
            r = S.filter((pl.col("scenario") == sn) & (pl.col("window") == 7)).row(0, named=True)
            res[sn] = dict(onset=abs(r["onset_err_median"]) <= P["onset_error_abs_median_s_max"],
                           bias=abs(r["rel_bias_trend"]) <= P["launch_rel_bias_abs_max"],
                           reliability=r["reliability_trend"] >= P["launch_measurement_reliability_min"],
                           athlete_rank=r["spearman_athlete_A0"] >= P["spearman_vs_true_athlete_A0_min"],
                           failure=r["failure_rate_recording_before_onset"] <= P["failure_rate_max"], values=r)
        res["pass"] = all(all(v for k, v in res[sn].items() if k != "values") for sn in CAL)
    json.dump(dict(stage=stage, run=run_id, seeds=SEEDS[stage], n_athletes=N_ATH, n_trials=N_TRIALS, decision=res), open(out / "meta.json", "w"), indent=1, default=float)
    (ROOT / "experiments" / "phase16" / f"LATEST_synthetic_{stage}").write_text(out.name)
    print("done", out, {k: v for k, v in res.items() if k == "pass"})


if __name__ == "__main__":
    main()
