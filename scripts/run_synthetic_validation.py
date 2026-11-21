"""Phase 4: synthetic validation of the registered confirmatory pipeline (no combine x outcome join).

Stages
  skeleton  real REG-season designs (outcome-free) + outcome-only REML calibration of nuisance parameters
            -> data/interim/phase4/ (git-ignored)
  h1        H1 scenarios 1-6 (+ naive comparators)         -> experiments/synthetic_validation/<run>/h1_*.parquet
  h2        H2 scenarios (partial r grid x measurement error) + CV leakage check
  family    joint H1-WR, H1-DB, H2 replicates: fixed sequence vs Holm
  selection eligibility-threshold scenarios (selection on outcome / on capacity)

Seeds: every scenario uses SeedSequence(BASE_SEED, scenario index); replicate r uses spawn(r).
"""
from __future__ import annotations

import json
import os
import sys
import time

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):   # one BLAS thread per worker
    os.environ.setdefault(_v, "1")
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from nfl_bdb.data.io import INTERIM  # noqa: E402
from nfl_bdb.data.play_table import H1_COVARIATES, H2_COVARIATES, h1_frame, reg_play_table  # noqa: E402
from nfl_bdb.models import confirmatory as cf  # noqa: E402
from nfl_bdb.models.reml import fit_reml  # noqa: E402
from nfl_bdb.simulation import confirmatory_sim as cs  # noqa: E402

SK = INTERIM / "phase4"
OUTROOT = ROOT / "experiments" / "synthetic_validation"
BASE_SEED = 4004
CFG = dict(base_seed=BASE_SEED, B_h1=2000, B_h2=2000, B_cv=200, cv_folds=10, cv_repeats=20, cv_boot_repeats=2,
           alpha=0.05, rel_x=0.987, r_dep=0.3, n_rep_h1=400, n_rep_h2=400, n_rep_family=300, n_rep_sel=300,
           workers=4)
CTX = {"WR": ["deep", "short"], "DB": ["man", "under_zone"]}
PRIMARY_OPP = {"WR": "route", "DB": "coverage"}


# =================================================================================================
# skeleton
# =================================================================================================
def _team_index(df):
    ts = (df["team_abbr"] + "_" + df["season"].cast(pl.Utf8))
    u = {k: i for i, k in enumerate(sorted(ts.unique().to_list()))}
    return pl.Series("team_i", [u[k] for k in ts.to_list()])


def build_skeletons():
    from run_power_analysis import primary_opp_counts, tracked40_ids
    SK.mkdir(parents=True, exist_ok=True)
    d = reg_play_table().filter(pl.col("play_nullified_by_penalty") != "Y")
    ids = tracked40_ids().implode()
    opp = primary_opp_counts(d)
    cal = {}
    for pos in ("WR", "DB"):
        ctxs = CTX[pos]
        x = h1_frame(d, pos).filter(pl.col("ctx").is_in(ctxs) & pl.col("nfl_id").is_in(ids))
        cnt = x.group_by("nfl_id", "ctx").len().pivot(index="nfl_id", on="ctx", values="len").fill_null(0)
        pool = cnt.filter(pl.all_horizontal([pl.col(c) >= 5 for c in ctxs]))
        pool = pool.join(opp.filter(pl.col("pos") == pos).select("nfl_id", pl.col(PRIMARY_OPP[pos]).alias("opp")), on="nfl_id")
        pool = pool.with_columns(
            ((pl.col("opp") >= 100) & pl.all_horizontal([pl.col(c) >= 20 for c in ctxs])).alias("eligible"),
            (pl.col(ctxs[0]) / (pl.col(ctxs[0]) + pl.col(ctxs[1]))).alias("dep"),
            pl.col("opp").log().alias("lr")).sort("nfl_id").with_row_index("pid").with_columns(pl.col("pid").cast(pl.Int64))
        x = x.join(pool.select("nfl_id", "pid", "eligible", "dep", "lr", "opp"), on="nfl_id")
        x = x.with_columns(pl.when(pl.col("ctx") == ctxs[0]).then(0).otherwise(1).alias("ctx_i"))
        go = x.filter(pl.col("ctx_i") == 0).group_by("pid").agg((pl.col("route_ran") == "GO").mean().alias("go_share"))
        x = x.join(go, on="pid", how="left").with_columns(pl.col("go_share").fill_null(0))
        for c in ("dep", "lr", "go_share"):
            pv = x.group_by("pid").agg(pl.col(c).first())[c]
            x = x.with_columns(((pl.col(c) - pv.mean()) / max(pv.std(), 1e-9)).alias(f"{c}_std"))
        x = x.with_columns(_team_index(x)).sort("pid", "ctx_i", "game_id", "play_id")
        covs = H1_COVARIATES[pos]
        Xw = cf.design_h1(x, covs, 2)
        y = x["y"].to_numpy(); pid = x["pid"].to_numpy(); ctx = x["ctx_i"].to_numpy(); team = x["team_i"].to_numpy()
        t0 = time.time(); fit = fit_reml(y, Xw, pid, ctx, team, 2); dt = time.time() - t0
        mu_hat = Xw @ fit.beta
        r = y - mu_hat
        grp = pid * 2 + ctx
        rm = np.bincount(grp, weights=r) / np.bincount(grp)
        resid = r - rm[grp]
        x = x.with_columns(pl.Series("mu_hat", mu_hat), pl.Series("resid_within", resid))
        el = x.filter(pl.col("eligible"))
        cal[pos] = dict(sigma_b=fit.sigma_b.tolist(), s2_team=fit.s2_team, s2_resid=fit.s2_resid.tolist(), converged=fit.converged,
                        fit_seconds=dt, n_plays=x.height, n_pool=int(pool.height), n_eligible=int(pool["eligible"].sum()),
                        n_team=int(team.max() + 1), n_cols=int(Xw.shape[1]),
                        team_share_of_between=fit.s2_team / (fit.s2_team + float(np.mean(np.diag(fit.sigma_b)))),
                        corr_b=float(fit.sigma_b[0, 1] / np.sqrt(fit.sigma_b[0, 0] * fit.sigma_b[1, 1])),
                        eligible_plays=el.height)
        keep_cols = ["pid", "nfl_id", "ctx_i", "team_i", "season", "nfl_year", "mu_hat", "resid_within", "eligible", "opp",
                     "dep_std", "lr_std", "go_share_std", "dep", "route_ran"] + [c for c in covs if c not in ("ctx", "route_ran", "season")]
        x.select([c for c in dict.fromkeys(keep_cols) if c in x.columns]).write_parquet(SK / f"h1_{pos}.parquet")
        print(pos, cal[pos], flush=True)
    # ---- H2 skeleton: WR deep routes with separation ------------------------------------------------
    w = d.filter((pl.col("pos") == "WR") & pl.col("is_pass") & pl.col("route_depth").is_in(["deep", "short"])
                 & pl.col("separation_at_pass_forward").is_not_null() & pl.col("nfl_id").is_in(ids))
    cnt = w.group_by("nfl_id", "route_depth").len().pivot(index="nfl_id", on="route_depth", values="len").fill_null(0)
    el = cnt.join(opp.filter(pl.col("pos") == "WR").select("nfl_id", "route"), on="nfl_id") \
        .filter((pl.col("route") >= 100) & (pl.col("deep") >= 30) & (pl.col("short") >= 20)).sort("nfl_id") \
        .with_row_index("pid").with_columns(pl.col("pid").cast(pl.Int64))
    deep = w.filter(pl.col("route_depth") == "deep").join(el.select("nfl_id", "pid"), on="nfl_id")
    deep = deep.with_columns(_team_index(deep)).sort("pid", "game_id", "play_id")
    W2 = cf.full_rank(cf.one_hot(deep, H2_COVARIATES + ["nfl_year"]))
    y = deep["separation_at_pass_forward"].to_numpy(); pid = deep["pid"].to_numpy(); team = deep["team_i"].to_numpy()
    X2 = np.column_stack([np.ones(len(y)), W2])
    X2 = cf.full_rank(X2)
    fit = fit_reml(y, X2, pid, np.zeros(len(y), int), team, 1)
    mu_hat = X2 @ fit.beta
    r = y - mu_hat; rm = np.bincount(pid, weights=r) / np.bincount(pid)
    deep = deep.with_columns(pl.Series("mu_hat", mu_hat), pl.Series("resid_within", r - rm[pid]))
    cal["H2"] = dict(s2b=float(fit.sigma_b[0, 0]), s2_team=fit.s2_team, s2=float(fit.s2_resid[0]), n_players=int(el.height),
                     n_plays=deep.height, n_team=int(team.max() + 1), converged=fit.converged,
                     reliability_mean=float(np.mean(fit.sigma_b[0, 0] / (fit.sigma_b[0, 0] + fit.s2_resid[0] / np.bincount(pid)))))
    deep.select(["pid", "nfl_id", "team_i", "season", "nfl_year", "mu_hat", "resid_within"] + [c for c in H2_COVARIATES if c not in ("season",)]) \
        .write_parquet(SK / "h2_WR.parquet")
    print("H2", cal["H2"])
    json.dump(cal, open(SK / "calibration.json", "w"), indent=1)


# =================================================================================================
# helpers to run one H1 replicate on a skeleton
# =================================================================================================
_CACHE: dict = {}


def _load(pos):
    if pos not in _CACHE:
        sk = pl.read_parquet(SK / f"h1_{pos}.parquet")
        cal = json.load(open(SK / "calibration.json"))
        _CACHE[pos] = (sk, cal[pos])
    return _CACHE[pos]


def _design(sk_sub, pos):
    covs = H1_COVARIATES[pos]
    Xw = cf.design_h1(sk_sub, covs, 2)
    Wres = cf.full_rank(cf.one_hot(sk_sub, [c for c in covs if c != "ctx"] + (["ctx_i"] if "ctx" in covs else [])))
    return Xw, Wres


def run_h1_once(pos, scen, seed, subset="eligible", B=None, naive=True):
    sk, par = _load(pos)
    rng = np.random.default_rng(seed)
    gen = dict(rel_x=scen.get("rel_x", CFG["rel_x"]), r_dep=scen.get("r_dep", CFG["r_dep"]),
               route_confound=scen.get("route_confound", 0.0), sel_outcome=scen.get("sel_outcome", 0.0),
               thin_low=scen.get("thin_low", 1.0), sel_capacity=scen.get("sel_capacity", 0.0))
    pool_resid = [sk.filter(pl.col("ctx_i") == c)["resid_within"].to_numpy() for c in (0, 1)] if scen.get("empirical") else None
    sim, xall, truth, z = cs.simulate_h1(sk, par, scen["rho_h"], scen["rho_l"], rng, resid_pool=pool_resid, **gen)
    sel = sim["keep"].copy()
    if subset == "eligible":
        sel &= sk["eligible"].to_numpy()
    elif isinstance(subset, dict):          # eligibility rule variants (selection analysis)
        opp = sk["opp"].to_numpy()
        sel &= opp >= subset.get("min_opp", 0)
    sub = sk.filter(pl.Series(sel)).with_columns(pl.Series("y", sim["y"][sel]))
    if isinstance(subset, dict):            # per-context minimum plays, after thinning
        c = sub.group_by("pid", "ctx_i").len().pivot(index="pid", on="ctx_i", values="len").fill_null(0)
        okp = c.filter((pl.col("0") >= subset["min_ctx"]) & (pl.col("1") >= subset["min_ctx"]))["pid"]
        sub = sub.filter(pl.col("pid").is_in(okp.implode()))
    # reindex players / teams
    pids = np.unique(sub["pid"].to_numpy()); pmap = -np.ones(int(sk["pid"].max()) + 1, int); pmap[pids] = np.arange(len(pids))
    teams = np.unique(sub["team_i"].to_numpy()); tmap = -np.ones(int(sk["team_i"].max()) + 1, int); tmap[teams] = np.arange(len(teams))
    player = pmap[sub["pid"].to_numpy()]; team = tmap[sub["team_i"].to_numpy()]; ctx = sub["ctx_i"].to_numpy()
    y = sub["y"].to_numpy(); x = xall[pids]
    Xw, Wres = _design(sub, pos)
    t0 = time.time()
    res = cf.h1_procedure(player, ctx, team, y, Xw, Wres, x, B or CFG["B_h1"], rng, CFG["alpha"])
    res["seconds"] = time.time() - t0
    res["n_players"] = len(pids)
    res["true_delta_obs"] = truth.delta_obs_scale
    res["true_delta"] = truth.rho_h - truth.rho_l
    # Holm-level CI for sensitivity (alpha / 3)
    if naive:   # naive comparator: raw player-context means WITHOUT covariate adjustment (no route_ran etc.)
        m, n, sw2 = cf.player_context_stats(player, ctx, y, len(pids))
        rho, raw = cf.moment_rho(x, m, n, sw2)
        res["delta_naive_unadj"] = float(rho[0] - rho[1]); res["delta_naive_raw"] = float(raw[0] - raw[1])
    # season-forward replication: REML on the last season only (sign check)
    last = sub["season"].to_numpy() == 2025
    if last.sum() > 500:
        c25 = np.bincount(player[last] * 2 + ctx[last], minlength=2 * len(pids)).reshape(-1, 2)
        okp = np.where((c25 >= 20).all(1))[0]
        if len(okp) >= 15:
            mk = last & np.isin(player, okp)
            pm2 = -np.ones(len(pids), int); pm2[okp] = np.arange(len(okp))
            tt = np.unique(team[mk]); tm2 = -np.ones(team.max() + 1, int); tm2[tt] = np.arange(len(tt))
            Xw25, _ = _design(sub.filter(pl.Series(mk)), pos)
            try:
                r25 = cf.h1_reml(pm2[player[mk]], ctx[mk], tm2[team[mk]], y[mk], Xw25, x[okp])
                res["delta_2025"] = r25.delta; res["n_2025"] = len(okp)
            except Exception:  # noqa: BLE001
                res["delta_2025"] = np.nan
    res.pop("rho_reml"); res.pop("beta")
    return res


def _seed(scen_idx, rep):
    return np.random.SeedSequence([BASE_SEED, scen_idx, rep]).generate_state(1)[0]


def _work(args):
    fn, kw = args
    try:
        return fn(**kw)
    except Exception as e:  # noqa: BLE001
        return dict(error=repr(e))


def run_parallel(jobs):
    with ProcessPoolExecutor(CFG["workers"]) as ex:
        return list(ex.map(_work, jobs, chunksize=4))


H1_SCENARIOS = [
    # id, label, params
    (1, "S1 null (rho 0.3 / 0.3)", dict(rho_h=0.3, rho_l=0.3)),
    (2, "S1b null, no association (0 / 0)", dict(rho_h=0.0, rho_l=0.0)),
    (3, "S2 small (0.4 / 0.3)", dict(rho_h=0.4, rho_l=0.3)),
    (4, "S3 moderate (0.5 / 0.3)", dict(rho_h=0.5, rho_l=0.3)),
    (5, "S4 large (0.65 / 0.3)", dict(rho_h=0.65, rho_l=0.3)),
    (6, "S5a deployment only: route mix driven by capacity (0.3 / 0.3)", dict(rho_h=0.3, rho_l=0.3, r_dep=0.5, route_confound=1.5)),
    (7, "S5b selection on outcome: playing time ~ deep level (0.3 / 0.3)", dict(rho_h=0.3, rho_l=0.3, sel_outcome=1.0, subset="pool_registered")),
    (8, "S6 differential reliability: low-demand context thinned to 15% (0.3 / 0.3)", dict(rho_h=0.3, rho_l=0.3, thin_low=0.15)),
    (9, "S6b combine measurement error R_x = 0.80 (0.5 / 0.3)", dict(rho_h=0.5, rho_l=0.3, rel_x=0.80)),
    (10, "S1 null with empirical (non-normal) residuals", dict(rho_h=0.3, rho_l=0.3, empirical=True)),
    (11, "S3 moderate with empirical residuals", dict(rho_h=0.5, rho_l=0.3, empirical=True)),
]


def stage_h1(out, pos="WR", n_rep=None, scen_list=None):
    n_rep = n_rep or CFG["n_rep_h1"]
    rows = []
    for sid, label, sc in (scen_list or H1_SCENARIOS):
        sc = dict(sc)
        subset = sc.pop("subset", "eligible")
        if subset == "pool_registered":
            subset = dict(min_opp=100, min_ctx=20)
        jobs = [(run_h1_once, dict(pos=pos, scen=sc, seed=_seed(sid + (100 if pos == "DB" else 0), r), subset=subset)) for r in range(n_rep)]
        t0 = time.time(); res = run_parallel(jobs)
        for r, x in enumerate(res):
            rows.append(dict(pos=pos, scenario=sid, label=label, rep=r, **x))
        print(pos, sid, label, f"{time.time() - t0:.0f}s", flush=True)
    df = pl.DataFrame(rows, infer_schema_length=None)
    df.write_parquet(out / f"h1_{pos}.parquet")
    return df


if __name__ == "__main__":
    stage = sys.argv[1]
    if stage == "skeleton":
        build_skeletons()
    else:
        run = sys.argv[2] if len(sys.argv) > 2 else datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = OUTROOT / run; out.mkdir(parents=True, exist_ok=True)
        json.dump(CFG, open(out / f"config_{stage}.json", "w"), indent=1)
        (OUTROOT / "LATEST").write_text(run)
        if stage == "h1":
            stage_h1(out, "WR")
        elif stage == "h1_db":
            stage_h1(out, "DB", n_rep=200, scen_list=[s for s in H1_SCENARIOS if s[0] in (1, 4)])
        else:
            import phase4_stages as ps   # h2 / family / selection stages
            getattr(ps, f"stage_{stage}")(out)
