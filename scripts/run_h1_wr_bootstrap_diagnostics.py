"""Part 3: why the registered percentile interval differs from the BCa interval (exploratory diagnostics; no refit
of the primary model, no change to the primary interval).

Inputs: the primary run's bootstrap / jackknife arrays, the robustness run's leave-one-team(-season)-out estimates,
and the Phase 4 warp-speed simulation (same bootstrap on the real WR design with synthetic outcomes).
Output: experiments/h1_wr_robustness/<LATEST>/bootstrap_diagnostics.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "experiments/h1_wr_confirmatory/20261121T223645Z"
ROB = ROOT / "experiments/h1_wr_robustness" / (ROOT / "experiments/h1_wr_robustness/LATEST").read_text().strip()
P4 = ROOT / "experiments/synthetic_validation/20261121T023847Z"


def bca_levels(z0, a, lev=0.95):
    zl, zu = stats.norm.ppf([(1 - lev) / 2, 1 - (1 - lev) / 2])
    return [float(stats.norm.cdf(z0 + (z0 + z) / (1 - a * (z0 + z)))) for z in (zl, zu)]


def main():
    r = json.load(open(PRIMARY / "h1_wr_result.json")); d = r["primary"]["delta"]
    b = np.load(PRIMARY / "bootstrap_delta.npy"); j = np.load(PRIMARY / "jackknife_delta.npy")
    n = len(j)
    z0 = float(stats.norm.ppf((b < d).mean()))
    infl = (n - 1) * (j.mean() - j)
    a = float(np.sum(infl ** 3) / (6 * np.sum(infl ** 2) ** 1.5))
    out = dict(distribution=dict(B=len(b), mean=float(b.mean()), median=float(np.median(b)), sd=float(b.std()), skewness=float(stats.skew(b)),
                                 excess_kurtosis=float(stats.kurtosis(b)), share_below_estimate=float((b < d).mean()),
                                 iqr_sd=float((np.percentile(b, 75) - np.percentile(b, 25)) / 1.349),
                                 tails=dict(lower_2_5_minus_est=float(np.percentile(b, 2.5) - d), upper_97_5_minus_est=float(np.percentile(b, 97.5) - d))),
               bca=dict(z0=z0, acceleration=a))
    decomp = {}
    for lab, zz, aa in (("full_bca", z0, a), ("bias_correction_only", z0, 0.0), ("acceleration_only", 0.0, a), ("percentile", 0.0, 0.0)):
        lv = bca_levels(zz, aa); decomp[lab] = dict(levels=lv, interval=[float(np.quantile(b, q)) for q in lv])
    out["bca"]["decomposition"] = decomp
    # jackknife influence (players anonymised by rank)
    order = np.argsort(-np.abs(infl))
    out["jackknife"] = dict(n=n, mean=float(j.mean()), sd_jackknife_se=float(np.sqrt((n - 1) / n * np.sum((j - j.mean()) ** 2))),
                            range=[float(j.min()), float(j.max())], max_abs_change=float(np.max(np.abs(j - d))),
                            sign_changes=int(np.sum(np.sign(j) != np.sign(d))),
                            top5_influence=[dict(rank=k + 1, influence=float(infl[i]), delta_without=float(j[i])) for k, i in enumerate(order[:5])],
                            influence_skewness=float(stats.skew(infl)), ratio_boot_sd_to_jack_se=float(b.std() / np.sqrt((n - 1) / n * np.sum((j - j.mean()) ** 2))))
    # cluster sensitivity
    rob = json.load(open(ROB / "robustness.json"))
    for key, lab in (("R5_leave_one_team_out", "team"), ("diag_leave_one_team_season_out", "team_season")):
        v = np.array([x["delta"] for x in rob[key]])
        m = len(v); jse = np.sqrt((m - 1) / m * np.sum((v - v.mean()) ** 2))
        out[f"leave_one_{lab}_out"] = dict(clusters=m, min=float(v.min()), max=float(v.max()), max_abs_change=float(np.max(np.abs(v - d))),
                                           sign_changes=int(np.sum(np.sign(v) != np.sign(d))), cluster_jackknife_se=float(jse),
                                           all_converged=bool(all(x["converged"] for x in rob[key])))
    # Phase 4: same bootstrap, synthetic outcomes on the real design
    w = pl.read_parquet(P4 / "h1_warp.parquet"); sim = []
    for (s,), g in w.group_by("scenario", maintain_order=True):
        dd = g["delta_reml"].to_numpy(); tr = g["true_delta_obs"].to_numpy()
        cen = np.concatenate([np.asarray(bb) - e for bb, e in zip(g["reml_boot"].to_list(), dd)])
        zz = float(stats.norm.ppf((cen < 0).mean()))
        row = dict(scenario=int(s), truth=float(tr[0]), reml_bias=float((dd - tr).mean()), boot_median_shift=float(np.median(cen)), implied_z0=zz,
                   sampling_sd=float(dd.std(ddof=1)), boot_sd=float(cen.std()))
        for lab, lv in (("percentile", [0.025, 0.975]), ("bca_type", bca_levels(zz, a))):
            ql, qh = np.quantile(cen, lv)
            row[f"{lab}_coverage"] = float(np.mean((dd + ql <= tr) & (dd + qh >= tr)))
            row[f"{lab}_reject"] = float(np.mean((dd > 0) & (dd + ql > 0)))
            row[f"{lab}_miss_high"] = float(np.mean(dd + qh < tr))
        sim.append(row)
    out["phase4_bootstrap_world"] = sim
    out["wald"] = rob["wald"]
    json.dump(out, open(ROB / "bootstrap_diagnostics.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
