"""Phase 17 power simulation for a possible WR route-launch x context-adjusted separation study (simulation only).

Reads ONLY: counts of separation-defined thrown routes and team-seasons per eligible WR (null flags / identifiers from
player_play, never outcome values), the Phase 16 launch route counts, and documented aggregates (Phase 3.5
calibration, Phase 4 REML calibration, Phase 16 G-study). No outcome value is read or aggregated.

Usage: python scripts/run_phase17_power.py
"""
from __future__ import annotations

import itertools
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nfl_bdb.simulation.outcome_power import mde, simulate_cell  # noqa: E402

INTERIM = ROOT / "data" / "interim"
P16 = "20261125T041228Z"
REPS = 2000
EFFECTS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
G_COMP = (0.182, 0.316, 0.510)        # Phase 16 cell-z G-study components (athlete, athlete x route, residual)


def population(threshold):
    L = pl.read_parquet(INTERIM / "phase16" / P16 / "launch_attempts.parquet").filter(
        (pl.col("drill") == "SKILL_DRILLS_WR") & (pl.col("window") == 7) & pl.col("valid"))
    routes = L.group_by("nfl_id").agg(pl.col("route").n_unique().alias("n_routes"))
    cr = pl.read_parquet(INTERIM / "combine_results.parquet").filter(pl.col("combine_position") == "WR").select("nfl_id", "ten_yd_split", "forty")
    games = pl.read_parquet(INTERIM / "games.parquet").select("game_id", "season", "season_type")
    pp = pl.read_parquet(INTERIM / "player_play.parquet", columns=["game_id", "nfl_id", "team_abbr", "pass_result", "route_ran", "separation_at_pass_forward"])
    pp = pp.join(games, on="game_id").filter((pl.col("season_type") == "REG") & pl.col("route_ran").is_not_null()
                                             & pl.col("separation_at_pass_forward").is_not_null())   # null flag only
    ex = pp.group_by("nfl_id").agg(pl.len().alias("n_sep"), pl.struct("team_abbr", "season").n_unique().alias("k_ts"))
    base = cr.join(routes, on="nfl_id").filter((pl.col("n_routes") >= 8) & pl.col("ten_yd_split").is_not_null() & pl.col("forty").is_not_null())
    full = base.join(ex, on="nfl_id", how="left")
    elig = full.filter(pl.col("n_sep").fill_null(0) >= threshold)
    return base.height, elig


def main():
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "experiments" / "phase17" / run; out.mkdir(parents=True)
    rows = []
    pops = {t: population(t) for t in (50, 100, 200)}
    N, e100 = pops[100]
    n_routes = e100["n_routes"].to_numpy()
    meta = dict(run=run, N_preselection=N, eligible={t: pops[t][1].height for t in pops},
                n_routes_distribution={int(k): int(v) for k, v in zip(*np.unique(n_routes, return_counts=True))},
                exposure_median=float(e100["n_sep"].median()), team_seasons_median=float(e100["k_ts"].median()),
                g_components=G_COMP)
    rng = np.random.default_rng(1717)
    grid = list(itertools.product([0.64, 0.69, "actual"], [0.44, 0.53, 0.61, 0.70], [0.0, 0.3], [0.0, 0.3], [0.0, 1.10]))
    for (R_x, R_y, g, lam, tau) in grid:
        for rho in EFFECTS:
            r = simulate_cell(rho, N=N, n_elig=e100.height, counts=e100["n_sep"].to_numpy(), team_counts=e100["k_ts"].to_numpy(),
                              R_y=R_y, R_x=R_x, R_F=0.90, g=g, lam=lam, tau=tau, reps=REPS, rng=rng, n_routes=n_routes, g_components=G_COMP)
            rows.append(dict(threshold=100, n=e100.height, R_x=str(R_x), R_y=R_y, g=g, lam=lam, tau=tau, R_F=0.90, rho=rho, **r))
    # sensitivity: thresholds 50 / 200 and R_F 0.80 at the primary nuisance setting
    for thr in (50, 200):
        Nt, et = pops[thr]
        for R_y in (0.44, 0.61):
            for rho in EFFECTS:
                r = simulate_cell(rho, N=Nt, n_elig=et.height, counts=et["n_sep"].to_numpy(), team_counts=et["k_ts"].to_numpy(),
                                  R_y=R_y, R_x=0.64, R_F=0.90, g=0.0, lam=0.0, tau=1.10, reps=REPS, rng=rng)
                rows.append(dict(threshold=thr, n=et.height, R_x="0.64", R_y=R_y, g=0.0, lam=0.0, tau=1.10, R_F=0.90, rho=rho, **r))
    for R_y in (0.44, 0.61):
        for rho in EFFECTS:
            r = simulate_cell(rho, N=N, n_elig=e100.height, counts=e100["n_sep"].to_numpy(), team_counts=e100["k_ts"].to_numpy(),
                              R_y=R_y, R_x=0.64, R_F=0.80, g=0.3, lam=0.0, tau=1.10, reps=REPS, rng=rng)
            rows.append(dict(threshold=100, n=e100.height, R_x="0.64", R_y=R_y, g=0.3, lam=0.0, tau=1.10, R_F=0.80, rho=rho, **r))
    # power vs number of players (primary nuisance), to state what external data would need
    for n_e in (54, 100, 150, 250, 400):
        for rho in (0.1, 0.2, 0.3):
            cnt = np.resize(e100["n_sep"].to_numpy(), n_e); kts = np.resize(e100["k_ts"].to_numpy(), n_e)
            r = simulate_cell(rho, N=n_e, n_elig=n_e, counts=cnt, team_counts=kts, R_y=0.61, R_x=0.64, R_F=0.90, g=0.0, lam=0.0,
                              tau=1.10, reps=REPS, rng=rng)
            rows.append(dict(threshold="n_scaling", n=n_e, R_x="0.64", R_y=0.61, g=0.0, lam=0.0, tau=1.10, R_F=0.90, rho=rho, **r))
    D = pl.DataFrame(rows, infer_schema_length=None).with_columns(pl.col("threshold").cast(pl.Utf8))
    D.write_csv(out / "power_grid.csv")
    m = []
    for keys, g_ in D.filter(pl.col("feasible") & (pl.col("threshold") != "n_scaling")).group_by("threshold", "n", "R_x", "R_y", "g", "lam", "tau", "R_F", maintain_order=True):
        g_ = g_.sort("rho")
        m.append(dict(zip(("threshold", "n", "R_x", "R_y", "g", "lam", "tau", "R_F"), keys), size=float(g_.filter(pl.col("rho") == 0)["power_two_sided"][0]),
                      mde_two_sided=mde(g_["rho"].to_list(), g_["power_two_sided"].to_list()),
                      power_at_0_2=float(g_.filter(pl.col("rho") == 0.2)["power_two_sided"][0]), power_at_0_3=float(g_.filter(pl.col("rho") == 0.3)["power_two_sided"][0])))
    pl.DataFrame(m).write_csv(out / "mde_summary.csv")
    json.dump(meta, open(out / "meta.json", "w"), indent=1)
    (ROOT / "experiments" / "phase17" / "LATEST").write_text(run)
    print("done", out, meta["eligible"], N)


if __name__ == "__main__":
    main()
