"""Experiment 2 (Candidate C): simulation of the capacity-constrained minimum-time (CCMT) COD cost.

Synthetic athletes have true capacities (A0, S0, D, C) and a latent *technique* trait z that sets the
fractions of capacity used in drills (eta) and dwell time at touch points. Each athlete runs each drill
twice; positions are sampled at fs with noise; the pipeline estimates path, gate-to-gate time and
CCMT costs with *estimated* (noisy) athlete limits. Conventional COD measures are computed from the
same measured times. No NFL outcome data are used. Writes experiments/cod_sim/<run_id>/.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
import zlib
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")

from nfl_bdb.features.change_direction_cost import (  # noqa: E402
    AthleteLimits, ccmt_cost, conventional_measures, drill_paths, estimate_path, linear_sprint_time,
    segment_time, simulate_execution)

CALIB = {  # S0/A0 from combine-40 fits (as Experiment 1); D, C are ASSUMPTIONS (yd/s^2)
    "WR": dict(S0=11.64, S0_sd=0.44, A0=8.89, A0_sd=1.23, D=6.5, C=7.0),
    "TE": dict(S0=10.92, S0_sd=0.37, A0=8.32, A0_sd=0.74, D=6.0, C=6.5),
    "OL": dict(S0=9.77, S0_sd=0.42, A0=7.50, A0_sd=1.20, D=5.0, C=5.5),
    "DL": dict(S0=10.48, S0_sd=0.72, A0=8.04, A0_sd=0.94, D=5.5, C=6.0),
    "DB": dict(S0=11.55, S0_sd=0.43, A0=8.84, A0_sd=1.03, D=6.5, C=7.0),
}
BASE = dict(noise_sd=0.01, fs=10.0, window=7, err_AS=0.05, err_DC=0.10, bias_own=0.0, rho_zS=0.0,
            lateral_known=True, circular=False, n_per_pos=60)
DRILLS = ["three_cone", "shuttle_5_10_5", "cut_90", "cut_135"]
START_GATE = 0.5


def cells():
    out = [("base", {})]
    out += [(f"noise_{s}", dict(noise_sd=s)) for s in (0.0, 0.02, 0.05)]
    out += [("fs_5", dict(fs=5.0, window=5)), ("fs_25", dict(fs=25.0, window=17))]
    out += [(f"window_{w}", dict(window=w)) for w in (5, 9)]
    out += [("limits_err_0", dict(err_AS=0.0, err_DC=0.0)), ("limits_err_10_20", dict(err_AS=0.10, err_DC=0.20)),
            ("limits_err_20_30", dict(err_AS=0.20, err_DC=0.30)), ("limits_bias_+10pct", dict(bias_own=0.10))]
    out += [("lateral_unknown", dict(lateral_known=False)), ("technique_corr_speed_0.3", dict(rho_zS=0.3)),
            ("circular_limits", dict(circular=True))]
    return out


def population(rng, p):
    rows = []
    for pos, c in CALIB.items():
        n = p["n_per_pos"]
        zS = rng.standard_normal(n)
        z = p["rho_zS"] * zS + np.sqrt(1 - p["rho_zS"] ** 2) * rng.standard_normal(n)
        zA = -0.3 * zS + np.sqrt(1 - 0.09) * rng.standard_normal(n)
        S0 = c["S0"] + c["S0_sd"] * zS
        A0 = c["A0"] + c["A0_sd"] * zA
        zz = (A0 - c["A0"]) / c["A0_sd"]
        D = c["D"] * np.exp(0.12 * (0.4 * zz + np.sqrt(1 - 0.16) * rng.standard_normal(n)))
        C = c["C"] * np.exp(0.15 * (0.3 * zz + np.sqrt(1 - 0.09) * rng.standard_normal(n)))
        e = rng.standard_normal((4, n))
        etaA = np.clip(0.96 + 0.015 * z + 0.01 * e[0], 0.8, 1.0)
        etaD = np.clip(0.85 + 0.05 * z + 0.03 * e[1], 0.5, 1.0)
        etaC = np.clip(0.88 + 0.04 * z + 0.03 * e[2], 0.5, 1.0)
        dwell = np.clip(0.06 - 0.025 * z + 0.015 * e[3], 0.0, 0.2)
        for j in range(n):
            rows.append(dict(pos=pos, A0=A0[j], S0=S0[j], D=D[j], C=C[j], z=z[j], etaA=etaA[j], etaD=etaD[j],
                             etaC=etaC[j], dwell=dwell[j]))
    return rows


def run_cell(args):
    name, over = args
    p = {**BASE, **over}
    seed = 20_000 + zlib.crc32(name.encode()) % 9973
    rng = np.random.default_rng(seed)
    pop = population(rng, p)
    paths = drill_paths()
    ref = {pos: AthleteLimits(A0=c["A0"], S0=c["S0"], D=c["D"], C=c["C"]) for pos, c in CALIB.items()}
    meanC = {pos: c["C"] for pos, c in CALIB.items()}
    out = []
    t0 = time.time()
    for k, a in enumerate(pop):
        true = AthleteLimits(A0=a["A0"], S0=a["S0"], D=a["D"], C=a["C"])
        f = np.exp(p["bias_own"] + np.r_[p["err_AS"] * rng.standard_normal(2), p["err_DC"] * rng.standard_normal(2)])
        own = AthleteLimits(A0=a["A0"] * f[0], S0=a["S0"] * f[1], D=a["D"] * f[2], C=a["C"] * f[3])
        if not p["lateral_known"]:
            own = AthleteLimits(A0=own.A0, S0=own.S0, D=own.D, C=meanC[a["pos"]])
        if p["circular"]:   # limits 'estimated' from the athlete's own (inefficient) drill behaviour
            own = AthleteLimits(A0=own.A0, S0=own.S0, D=own.D * a["etaD"], C=own.C * a["etaC"])
        T40_true = linear_sprint_time(40.0, true)
        T40_meas = T40_true + rng.normal(0, 0.02)
        # measured sprint used for COD deficit: own (estimated) A–S line rescaled to hit the measured 40
        sprint = AthleteLimits(A0=own.A0, S0=own.S0, D=own.D, C=own.C)
        sc = linear_sprint_time(40.0, sprint) / T40_meas
        sprint = AthleteLimits(A0=sprint.A0 * sc ** 2, S0=sprint.S0 * sc, D=sprint.D, C=sprint.C)
        for d in DRILLS:
            path = paths[d]
            Tstar_true = segment_time(path, true, START_GATE)
            Tstar_nom_own = segment_time(path, own, START_GATE)
            for att in (1, 2):
                eta = (np.clip(a["etaA"] + rng.normal(0, 0.01), 0.7, 1), np.clip(a["etaD"] + rng.normal(0, 0.015), 0.4, 1),
                       np.clip(a["etaC"] + rng.normal(0, 0.015), 0.4, 1))
                dw = max(0.0, a["dwell"] + rng.normal(0, 0.01))
                ex = simulate_execution(path, true, eta, dw, fs=p["fs"], noise_sd=p["noise_sd"], rng=rng)
                T_gate_true = ex["T_true"] - float(np.interp(START_GATE, path.s, ex["t_profile"]))
                try:
                    P, Tm, s0, sp = estimate_path(ex["x"], ex["y"], fs=p["fs"], window=p["window"],
                                                  finish_point=ex["finish_point"], finish_dir=ex["finish_dir"],
                                                  start_dist=START_GATE)
                except Exception:
                    continue
                c_own = ccmt_cost(P, Tm, own, ref[a["pos"]], s_from=s0)
                nolat = AthleteLimits(A0=own.A0, S0=own.S0, D=own.D, C=own.C, lateral=False)
                E_nolat = Tm - segment_time(P, nolat, s0)
                conv = conventional_measures(Tm, P.length - s0, sprint, speed_trace=sp, fs=p["fs"])
                out.append(dict(cell=name, seed=seed, athlete=k, pos=a["pos"], drill=d, attempt=att, z=a["z"],
                                A0=a["A0"], S0=a["S0"], D=a["D"], C=a["C"], T40_true=T40_true, T40_meas=T40_meas,
                                E_true=T_gate_true - Tstar_true, T_gate_true=T_gate_true, T_meas=Tm,
                                E_hat=c_own["execution_cost"], K_hat=c_own["capacity_cost"],
                                E_ratio=c_own["execution_ratio"], E_nominal=Tm - Tstar_nom_own,
                                E_ref_only=Tm - c_own["T_star_ref"], E_no_lateral=E_nolat,
                                total_time=conv["total_time"], codd=conv["codd"], codd_pct=conv["codd_pct"],
                                cod_speed=conv["cod_speed"], peak_braking=conv.get("peak_braking", np.nan),
                                L_est=P.length, stops_est=int(P.stop.sum()), stops_true=int(path.stop.sum())))
    return out, name, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    cl = cells()
    if a.quick:
        cl = [(n, {**o, "n_per_pos": 4}) for n, o in cl[:2]]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ("_quick" if a.quick else "")
    out_dir = ROOT / "experiments" / "cod_sim" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    json.dump(dict(base=BASE, calib=CALIB, cells=cl, drills=DRILLS, start_gate=START_GATE,
                   note="seed = 20000 + crc32(cell) % 9973"), open(out_dir / "config.json", "w"), indent=1, default=str)
    rows = []
    t0 = time.time()
    with Pool(a.workers) as pool:
        for i, (r, name, dt) in enumerate(pool.imap_unordered(run_cell, cl)):
            rows += r
            print(f"[{i + 1}/{len(cl)}] {name} {dt:.0f}s rows={len(r)} elapsed {time.time() - t0:.0f}s", flush=True)
            pl.DataFrame(rows, infer_schema_length=None).write_parquet(out_dir / "results.parquet")
    (ROOT / "experiments" / "cod_sim" / "LATEST").write_text(run_id)
    print("done", out_dir)


if __name__ == "__main__":
    main()
