"""Phase 2, Experiment 1: combine-to-game capacity transfer (no performance outcomes used).

Outputs (experiments/real_capacity/<run_id>/):
  combine_forty_attempts.parquet  per 40-yd attempt: mono-exponential S0, tau, A0, peak speed, R²
  game_capacity.parquet           per player x scope (all / half 0 / half 1): exposure and capacity
                                  measures from REG+POST game tracking
  exclusions.json, config.json
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import polars as pl
from scipy.optimize import curve_fit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")
from nfl_bdb.data.game_kinematics import load_game_sequences, sg_kinematics  # noqa: E402
from nfl_bdb.data.io import load  # noqa: E402
from nfl_bdb.models.capacity_estimator import fit_binned, fit_simex, jackknife_se  # noqa: E402

CFG = dict(window=7, noise_sd=0.01, simex_lambdas=(0.5, 1.0, 1.5, 2.0), simex_rep=3, jk_groups=10,
           season_types=("REG", "POST"), min_plays_for_fit=10)
G = {}


def forty_fits():
    ct = load("combine_tracking", lazy=False).filter((pl.col("entity_type") == "PLAYER") & (pl.col("drill_type") == "FORTY_YARD_DASH")).sort("event_id", "time")
    mono = lambda t, S0, tau, t0: np.where(t > t0, S0 * (1 - np.exp(-(t - t0) / tau)), 0.0)
    rows = []
    for (eid, nid, att, dy), g in ct.group_by(["event_id", "nfl_id", "attempt", "draft_year"]):
        s = g["s"].to_numpy(); t = np.arange(len(s)) / 10; ip = int(np.argmax(s))
        r = dict(event_id=eid, nfl_id=nid, attempt=int(att), draft_year=int(dy), vpeak=float(s.max()), n=len(s))
        if ip >= 15:
            try:
                p, _ = curve_fit(mono, t[:ip + 1], s[:ip + 1], p0=[s.max(), 1.0, t[np.argmax(s > 0.3)]],
                                 bounds=([5, 0.3, -1], [14, 3, 3]), maxfev=5000)
                res = s[:ip + 1] - mono(t[:ip + 1], *p)
                r.update(S0=p[0], tau=p[1], A0=p[0] / p[1], r2=float(1 - np.sum(res ** 2) / np.sum((s[:ip + 1] - s[:ip + 1].mean()) ** 2)))
            except Exception:
                pass
        rows.append(r)
    return pl.DataFrame(rows, infer_schema_length=None)


def player_measures(args):
    nid, lo, hi = args
    x, y, s, seq, half, speed, at = (G[k][lo:hi] for k in ("x", "y", "s", "seq", "half", "speed", "at"))
    out = []
    for scope in ("all", 0, 1):
        m = np.ones(hi - lo, bool) if scope == "all" else (half == scope)
        if m.sum() == 0:
            continue
        sq = seq[m]
        plays = np.unique(sq)
        sm = s[m]
        starts = np.r_[0, np.flatnonzero(np.diff(sq)) + 1]
        play_max = np.maximum.reduceat(sm, starts)
        top = np.sort(play_max)[::-1]
        r = dict(nfl_id=int(nid), scope=str(scope), n_plays=int(len(plays)), n_frames=int(m.sum()),
                 vmax_obs=float(s[m].max()), vmax_2nd=float(top[1]) if len(top) > 1 else np.nan,
                 vmax_top5_mean=float(top[:5].mean()) if len(top) >= 5 else np.nan)
        if len(plays) >= CFG["min_plays_for_fit"]:
            b = fit_binned(speed[m], at[m], sq)
            r.update(S0_bin=b["S0"], A0_bin=b["A0"])
            if scope == "all":
                rng = np.random.default_rng(int(nid))

                def fn(keep, x=x[m], y=y[m], sq=sq):
                    mm = np.isin(sq, plays[keep])
                    q = fit_simex(x[mm], y[mm], sq[mm], noise_sd=CFG["noise_sd"], lambdas=CFG["simex_lambdas"],
                                  n_rep=CFG["simex_rep"], window=CFG["window"], rng=np.random.default_rng(rng.integers(1 << 31)))
                    return [np.log(q["A0"]) if q["A0"] > 0 else np.nan, np.log(q["S0"]) if q["S0"] > 0 else np.nan]
                est, se = jackknife_se(fn, CFG["jk_groups"], plays, rng)
                r.update(A0_simex=float(np.exp(est[0])), S0_simex=float(np.exp(est[1])), se_logA0_simex=float(se[0]), se_logS0_simex=float(se[1]))
            else:
                q = fit_simex(x[m], y[m], sq, noise_sd=CFG["noise_sd"], lambdas=CFG["simex_lambdas"], n_rep=CFG["simex_rep"],
                              window=CFG["window"], rng=np.random.default_rng(int(nid) + 7))
                r.update(A0_simex=q["A0"], S0_simex=q["S0"])
        out.append(r)
    return out


def main():
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "experiments" / "real_capacity" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    json.dump(CFG, open(out_dir / "config.json", "w"), indent=1, default=str)
    t0 = time.time()
    forty_fits().write_parquet(out_dir / "combine_forty_attempts.parquet")
    print("40 fits done", round(time.time() - t0), "s", flush=True)
    df, rep = load_game_sequences(season_types=CFG["season_types"], cols=["game_id", "play_id", "nfl_id", "time", "x", "y", "s"])
    json.dump(rep, open(out_dir / "exclusions.json", "w"), indent=1)
    g = df.select("nfl_id", "game_id").unique().sort("nfl_id", "game_id").with_columns((pl.int_range(pl.len()).over("nfl_id") % 2).alias("half"))
    df = df.join(g, on=["nfl_id", "game_id"]).sort("seq", "time")
    k = sg_kinematics(df["x"].to_numpy(), df["y"].to_numpy(), df["seq"].to_numpy(), CFG["window"])
    for c in ("x", "y", "s", "seq", "half", "nfl_id"):
        G[c] = df[c].to_numpy()
    G["speed"], G["at"] = k["speed"], k["a_t"]
    del df, k
    nid = G["nfl_id"]
    bounds = np.r_[0, np.flatnonzero(np.diff(nid)) + 1, len(nid)]
    jobs = [(int(nid[a]), int(a), int(b)) for a, b in zip(bounds[:-1], bounds[1:])]
    print("players", len(jobs), "loaded", round(time.time() - t0), "s", flush=True)
    rows = []
    with Pool(4) as pool:
        for i, r in enumerate(pool.imap_unordered(player_measures, jobs, chunksize=4)):
            rows += r
            if (i + 1) % 50 == 0:
                print(f"[{i + 1}/{len(jobs)}] {time.time() - t0:.0f}s", flush=True)
    pl.DataFrame(rows, infer_schema_length=None).write_parquet(out_dir / "game_capacity.parquet")
    (ROOT / "experiments" / "real_capacity" / "LATEST").write_text(run_id)
    print("done", out_dir, round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
