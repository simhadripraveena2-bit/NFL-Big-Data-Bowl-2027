"""Exploratory validation of the H1 Wald interval (h1_extensions.wald_delta) on the real WR design with SYNTHETIC
outcomes (Phase 4 generator, scenarios S1 null and S3 moderate, seeds as Phase 4). Usage: python scripts/validate_wald_synthetic.py out.parquet"""
import os, sys
os.environ.setdefault("OMP_NUM_THREADS", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
import numpy as np, polars as pl
from concurrent.futures import ProcessPoolExecutor

def one(args):
    sid, r = args
    import run_synthetic_validation as sv
    from nfl_bdb.simulation import confirmatory_sim as cs
    from nfl_bdb.models import h1_extensions as hx
    sk, par = sv._load("WR")
    sc = {s[0]: s for s in sv.H1_SCENARIOS}[sid][2]
    rng = np.random.default_rng(sv._seed(sid, r))
    sim, xall, truth, z = cs.simulate_h1(sk, par, sc["rho_h"], sc["rho_l"], rng, rel_x=0.987, r_dep=0.3)
    sel = sim["keep"] & sk["eligible"].to_numpy()
    sub = sk.filter(pl.Series(sel)).with_columns(pl.Series("y", sim["y"][sel]))
    pids = np.unique(sub["pid"].to_numpy()); pm = -np.ones(int(sk["pid"].max()) + 1, int); pm[pids] = np.arange(len(pids))
    _, team = np.unique(sub["team_i"].to_numpy(), return_inverse=True)
    Xw, _ = sv._design(sub, "WR")
    w = hx.wald_delta(pm[sub["pid"].to_numpy()], sub["ctx_i"].to_numpy(), team, sub["y"].to_numpy(), Xw, xall[pids])
    return dict(scenario=sid, rep=r, delta=w["delta"], se=w["se"], truth=truth.delta_obs_scale, crit=w["criterion_reproduced_abs_diff"])

if __name__ == "__main__":
    jobs = [(1, r) for r in range(100)] + [(4, r) for r in range(100)]
    with ProcessPoolExecutor(4) as ex:
        res = pl.DataFrame(list(ex.map(one, jobs)))
    res.write_parquet(sys.argv[1])
    for (s,), g in res.group_by("scenario", maintain_order=True):
        d = g["delta"].to_numpy(); se = g["se"].to_numpy(); tr = g["truth"].to_numpy()
        cov = np.mean(np.abs(d - tr) <= 1.96 * se); rej = np.mean((d - 1.96 * se) > 0)
        print(f"S{s}: reps {len(d)} sd(delta) {d.std(ddof=1):.3f} mean Wald SE {se.mean():.3f} coverage {cov:.3f} directional reject {rej:.3f} max crit diff {g['crit'].max():.2e}")
