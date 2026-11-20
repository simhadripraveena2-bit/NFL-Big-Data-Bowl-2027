"""Experiment 1 (Candidate B): controlled simulation of A–S capacity estimation.

Evaluation seeds are disjoint from the development seeds (101–103) used while designing the
estimator. No NFL outcome data are used anywhere. Writes per-athlete results + config to
experiments/capacity_sim/<run_id>/.

Usage:  python scripts/run_capacity_simulation.py [--reps 5] [--per-pos 20] [--workers 4] [--quick]
"""
from __future__ import annotations

import argparse
import json
import zlib
import os
import sys
import time
import warnings
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")

from nfl_bdb.models.capacity_estimator import (  # noqa: E402
    BASELINES, PooledCapacityEstimator)
from nfl_bdb.simulation.movement import (  # noqa: E402
    GameSimConfig, kinematics_fast, sample_athletes, simulate_game_tracks)

# Ground-truth distributions per position: S0/A0 means and SDs from mono-exponential fits to the
# real combine 40s (notebook 02 §2; best attempt per player). p_max (probability that an effort is
# maximal) and D are ASSUMPTIONS (not estimable from the available data).
CALIB = {
    "WR": dict(S0_mean=11.64, S0_sd=0.44, A0_mean=8.89, A0_sd=1.23, p_max=0.06, D_mean=6.5),
    "TE": dict(S0_mean=10.92, S0_sd=0.37, A0_mean=8.32, A0_sd=0.74, p_max=0.04, D_mean=6.0),
    "OL": dict(S0_mean=9.77, S0_sd=0.42, A0_mean=7.50, A0_sd=1.20, p_max=0.015, D_mean=5.0),
    "DL": dict(S0_mean=10.48, S0_sd=0.72, A0_mean=8.04, A0_sd=0.94, p_max=0.04, D_mean=5.5),
    "DB": dict(S0_mean=11.55, S0_sd=0.43, A0_mean=8.84, A0_sd=1.03, p_max=0.06, D_mean=6.5),
}
BASE = dict(n_plays=100, noise_sd=0.01, window=7, fs=10.0, pmax_mult=1.0, k_shape=1.0, spike=0.0,
            simex_sd_mult=1.0, mixed_exposure=False)


def cells():
    out = [("base", {})]
    out += [(f"exposure_{n}", dict(n_plays=n)) for n in (10, 25, 50, 250, 500)]
    out += [(f"noise_{s}", dict(noise_sd=s)) for s in (0.0, 0.005, 0.02, 0.03)]
    out += [(f"window_{w}", dict(window=w)) for w in (5, 9)]
    out += [(f"pmax_{m}", dict(pmax_mult=m)) for m in (0.25, 0.5, 2.0)]
    out += [(f"shape_{k}", dict(k_shape=k)) for k in (0.8, 1.3)]
    out += [("fs_5", dict(fs=5.0, window=5)), ("fs_25", dict(fs=25.0, window=17))]
    out += [(f"spike_{r}", dict(spike=r)) for r in (0.01, 0.03)]
    out += [(f"simex_sd_x{m}", dict(simex_sd_mult=m)) for m in (0.5, 1.5)]
    out += [("mixed_exposure", dict(mixed_exposure=True))]
    return out


def run_one(args):
    cell, over, rep, per_pos = args
    p = {**BASE, **over}
    seed = 10_000 + 1_000 * rep + (zlib.crc32(cell.encode()) % 997)
    rng = np.random.default_rng(seed)
    calib = {k: {**v, "p_max": v["p_max"] * p["pmax_mult"]} for k, v in CALIB.items()}
    ath = sample_athletes(rng, per_pos, calib)
    J = len(ath["A0"])
    if p["mixed_exposure"]:
        n_pl = np.clip(np.round(np.exp(np.log(263) + 1.44 * rng.standard_normal(J))), 10, 600).astype(int)
    else:
        n_pl = np.full(J, p["n_plays"])
    cfg = GameSimConfig(fs=p["fs"], noise_sd=p["noise_sd"], round_to=0.01 if p["noise_sd"] > 0 else 0.0,
                        k_shape=p["k_shape"], spike_play_rate=p["spike"])
    t0 = time.time()
    out = simulate_game_tracks(ath["A0"], ath["S0"], ath["D"], ath["p_max"], n_pl, cfg, rng)
    o = np.lexsort((out["t"], out["play"]))
    out = {k: v[o] for k, v in out.items()}
    sp, at, _ = kinematics_fast(out["x"], out["y"], out["play"], p["fs"], p["window"])
    rows = []
    by = [np.flatnonzero(out["athlete"] == j) for j in range(J)]
    # exposure diagnostics (truth-based; not available to estimators)
    n95 = np.array([len(np.unique(out["play"][i][out["v_true"][i] >= 0.95 * ath["S0"][j]])) for j, i in enumerate(by)])
    vmax_frac = np.array([out["v_true"][i].max() / ath["S0"][j] for j, i in enumerate(by)])

    def add(name, A0, S0, lo=None):
        for j in range(J):
            r = dict(cell=cell, rep=rep, seed=seed, athlete=j, pos=ath["pos"][j], A0_true=ath["A0"][j], S0_true=ath["S0"][j],
                     n_plays=int(n_pl[j]), n_plays_ge95=int(n95[j]), vmax_frac=float(vmax_frac[j]),
                     estimator=name, A0_hat=float(A0[j]), S0_hat=float(S0[j]))
            if lo is not None:
                r.update(A0_lo=float(lo["A0_lo"][j]), A0_hi=float(lo["A0_hi"][j]), S0_lo=float(lo["S0_lo"][j]), S0_hi=float(lo["S0_hi"][j]))
            else:   # keep a fixed schema (polars infers columns from early rows)
                r.update(A0_lo=np.nan, A0_hi=np.nan, S0_lo=np.nan, S0_hi=np.nan)
            rows.append(r)

    for name, fn in BASELINES.items():
        if name == "quantile_0.95":
            continue
        rs = [fn(sp[i], at[i], out["play"][i]) for i in by]
        add(name, np.array([r["A0"] for r in rs]), np.array([r["S0"] for r in rs]))
    tracks = [(out["x"][i], out["y"][i], out["play"][i]) for i in by]
    sd_assumed = max(p["noise_sd"], 1e-4) * p["simex_sd_mult"]
    variants = {
        "binned+JK": PooledCapacityEstimator(simex=False, shrink=False, window=p["window"], fs=p["fs"], seed=seed),
        "binned+EB": PooledCapacityEstimator(simex=False, shrink=True, window=p["window"], fs=p["fs"], seed=seed),
        "NCP-AS (SIMEX+JK, no pooling)": PooledCapacityEstimator(noise_sd=sd_assumed, shrink=False, window=p["window"], fs=p["fs"], seed=seed),
        "NCP-AS": PooledCapacityEstimator(noise_sd=sd_assumed, shrink=True, window=p["window"], fs=p["fs"], seed=seed),
    }
    if p["noise_sd"] == 0:   # SIMEX is undefined without measurement noise
        variants = {k: v for k, v in variants.items() if "NCP" not in k}
    for name, est in variants.items():
        r = est.fit(tracks, ath["pos"])
        add(name, r["A0"], r["S0"], r)
    return rows, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--per-pos", type=int, default=20)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    cl = cells()[:2] if a.quick else cells()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ("_quick" if a.quick else "")
    out_dir = ROOT / "experiments" / "capacity_sim" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    json.dump(dict(base=BASE, calib=CALIB, cells=cl, reps=a.reps, per_pos=a.per_pos,
                   note="evaluation seeds = 10000 + 1000*rep + crc32(cell)%997; dev seeds 101-103 not used"),
              open(out_dir / "config.json", "w"), indent=1, default=str)
    jobs = [(c, o, r, a.per_pos) for c, o in cl for r in range(a.reps)]
    all_rows = []
    t0 = time.time()
    with Pool(a.workers) as pool:
        for i, (rows, dt) in enumerate(pool.imap_unordered(run_one, jobs)):
            all_rows += rows
            print(f"[{i + 1}/{len(jobs)}] {rows[0]['cell']} rep {rows[0]['rep']} {dt:.0f}s  elapsed {time.time() - t0:.0f}s", flush=True)
            if (i + 1) % 10 == 0:
                pl.DataFrame(all_rows, infer_schema_length=None).write_parquet(out_dir / "results.parquet")
    pl.DataFrame(all_rows, infer_schema_length=None).write_parquet(out_dir / "results.parquet")
    (ROOT / "experiments" / "capacity_sim" / "LATEST").write_text(run_id)
    print("done", out_dir)


if __name__ == "__main__":
    main()
