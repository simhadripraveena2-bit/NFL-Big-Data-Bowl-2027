"""Phase 4 stages: H2, family-wise testing, selection, demand-measure validation.
Called from run_synthetic_validation.py. No combine x outcome join anywhere."""
from __future__ import annotations

import json
import time

import numpy as np
import polars as pl

import run_synthetic_validation as sv
from nfl_bdb.data.play_table import H2_COVARIATES, h1_frame, reg_play_table
from nfl_bdb.features import demand as dm
from nfl_bdb.models import confirmatory as cf
from nfl_bdb.simulation import confirmatory_sim as cs

CFG = sv.CFG


# =================================================================================================
# H2
# =================================================================================================
_H2 = {}


def _h2_load():
    if not _H2:
        sk = pl.read_parquet(sv.SK / "h2_WR.parquet")
        cal = json.load(open(sv.SK / "calibration.json"))["H2"]
        W = cf.one_hot(sk, [c for c in H2_COVARIATES if c in sk.columns])          # play covariates w (incl. season)
        W = cf.full_rank(np.column_stack([W, sk["nfl_year"].to_numpy().astype(float)]))   # + linear NFL year (kappa a_ij)
        _H2.update(sk=sk, cal=cal, W=W)
    return _H2


def run_h2_once(scen, seed, B=None, cv_boot=None, leakage=False):
    H = _h2_load(); sk, cal, W = H["sk"], H["cal"], H["W"]
    rng = np.random.default_rng(seed)
    pool = sk["resid_within"].to_numpy() if scen.get("empirical") else None
    y, F, x, truth = cs.simulate_h2(sk, cal, scen["partial"], rng, rho_forty=scen.get("rho_forty", 0.3),
                                    rel_F=scen.get("rel_F", 0.95), rel_x=scen.get("rel_x", 0.987), resid_pool=pool)
    pid = sk["pid"].to_numpy(); team = sk["team_i"].to_numpy(); P = len(F)
    t0 = time.time()
    reml = cf.h2_reml(pid, team, y, W, F, x)
    r = cf.residualise_np(W, y)
    m, n, sw2 = cf.player_stats(pid, r, P)
    b, se, s2b = cf.wls_two_stage(m, n, sw2, F, x)
    bt = cf.h2_bootstrap(m, n, sw2, F, x, B or CFG["B_h2"], rng)
    eiv = cf.eiv_two_stage(m, n, sw2, F, x, rel_F=0.95, rel_x=CFG["rel_x"])
    S = cf.player_sufficient(pid, W, y, P)
    cv = cf.h2_cv(S, F, x, rng, CFG["cv_folds"], CFG["cv_repeats"])
    lb, _ = cf.h2_cv_bootstrap(S, F, x, rng, B=cv_boot or CFG["B_cv"], folds=CFG["cv_folds"], repeats=CFG["cv_boot_repeats"])
    # season-forward: fit on 2023-24 plays, predict 2025 player levels (players with >= 20 deep plays in 2025)
    season = sk["season"].to_numpy()
    tr, te = season < 2025, season == 2025
    sf = dict(dRMSE_sf=np.nan, n_sf=0)
    nte = np.bincount(pid[te], minlength=P); ntr = np.bincount(pid[tr], minlength=P)
    ok = np.where((nte >= 20) & (ntr >= 20))[0]
    if len(ok) >= 15:
        Wtr = np.column_stack([np.ones(tr.sum()), W[tr]]); beta = np.linalg.lstsq(Wtr, y[tr], rcond=None)[0]
        res_all = y - np.column_stack([np.ones(len(y)), W]) @ beta
        mtr, ntr2, sw2tr = cf.player_stats(pid[tr], res_all[tr], P)
        mte, nte2, _ = cf.player_stats(pid[te], res_all[te], P)
        okt = np.where(ntr2 >= 20)[0]
        s2b_tr = max(np.var(mtr[okt], ddof=1) - np.mean(sw2tr / ntr2[okt]), 1e-6)
        k = s2b_tr / (s2b_tr + sw2tr / np.maximum(nte2, 1)); mu = mtr[okt].mean()
        target = mu + k[ok] * (mte[ok] - mu)
        Fs = (F - F[okt].mean()) / F[okt].std(ddof=1); xs = (x - x[okt].mean()) / x[okt].std(ddof=1)
        X1 = np.column_stack([np.ones(len(okt)), Fs[okt]]); X2 = np.column_stack([X1, xs[okt]])
        ktr = s2b_tr / (s2b_tr + sw2tr / ntr2[okt]); ttr = mu + ktr * (mtr[okt] - mu)
        p1 = np.column_stack([np.ones(len(ok)), Fs[ok]]) @ np.linalg.lstsq(X1, ttr, rcond=None)[0]
        p2 = np.column_stack([np.ones(len(ok)), Fs[ok], xs[ok]]) @ np.linalg.lstsq(X2, ttr, rcond=None)[0]
        sf = dict(dRMSE_sf=float(np.sqrt(np.mean((target - p2) ** 2)) - np.sqrt(np.mean((target - p1) ** 2))), n_sf=len(ok))
    out = dict(beta_P_reml=reml["beta_P"], beta_P_std=reml["beta_P_std"], partial_hat=reml["partial"], se_wald=reml["se_wald"],
               s2b_hat=reml["s2b"], s2_team_hat=reml["s2_team"], converged=reml["converged"],
               beta_P_2s=float(b[2]), se_hc3=float(se[2]), ci_lo=bt["ci"][0], ci_hi=bt["ci"][1], p=bt["p"], se_boot=bt["se"],
               eiv_beta_P=float(eiv[1]), dr2_cv=cv["dr2"], r2_m1=cv["r2_m1"], r2_m2=cv["r2_m2"], dr2_lb90=lb, **sf,
               seconds=time.time() - t0, true_partial=truth["partial"])
    out["test_rejected"] = bool(out["beta_P_reml"] > 0 and out["ci_lo"] > 0)
    out["predictive_ok"] = bool(out["dr2_cv"] >= 0.02 and out["dr2_lb90"] > 0 and (not np.isfinite(out["dRMSE_sf"]) or out["dRMSE_sf"] <= 0))
    out["eiv_ok"] = bool(out["eiv_beta_P"] > 0)
    out["h2_supported_if_reached"] = out["test_rejected"] and out["predictive_ok"] and out["eiv_ok"]
    if leakage:
        out.update(_leakage_check(pid, W, y, F, x, P, rng))
    return out


def _leakage_check(pid, W, y, F, x, P, rng, folds=10):
    """Contrast: CV that holds out random PLAYS (player identity leaks into training) vs held-out PLAYERS."""
    fold = rng.integers(0, folds, len(y))
    pred1, pred2, targ = [], [], []
    for f in range(folds):
        tr, te = fold != f, fold == f
        Wtr = np.column_stack([np.ones(tr.sum()), W[tr]]); beta = np.linalg.lstsq(Wtr, y[tr], rcond=None)[0]
        res = y - np.column_stack([np.ones(len(y)), W]) @ beta
        mtr, ntr, _ = cf.player_stats(pid[tr], res[tr], P); mte, nte, _ = cf.player_stats(pid[te], res[te], P)
        ok = (ntr > 0) & (nte > 0)
        # model trained on training-play player means of ALL players (the same players are then "tested")
        X1 = np.column_stack([np.ones(P), cf.standardise(F)]); X2 = np.column_stack([X1, cf.standardise(x)])
        # play-split "prediction" uses the player's own training mean as a feature-free memorised target too
        b1 = np.linalg.lstsq(X1[ok], mtr[ok], rcond=None)[0]; b2 = np.linalg.lstsq(X2[ok], mtr[ok], rcond=None)[0]
        pred1.append(X1[ok] @ b1); pred2.append(X2[ok] @ b2); targ.append(mte[ok])
    p1, p2, t = map(np.concatenate, (pred1, pred2, targ))
    sst = ((t - t.mean()) ** 2).sum()
    return dict(dr2_playsplit=float(((t - p1) ** 2).sum() / sst - ((t - p2) ** 2).sum() / sst),
                r2_m2_playsplit=float(1 - ((t - p2) ** 2).sum() / sst))


H2_SCENARIOS = [(i + 1, f"partial {p}", dict(partial=p)) for i, p in enumerate([0.0, 0.1, 0.2, 0.3, 0.4])] + [
    (6, "partial 0, R_F 0.90", dict(partial=0.0, rel_F=0.90)),
    (7, "partial 0, R_F 0.99", dict(partial=0.0, rel_F=0.99)),
    (8, "partial 0, R_x 0.90", dict(partial=0.0, rel_x=0.90)),
    (9, "partial 0.3, R_F 0.90", dict(partial=0.3, rel_F=0.90)),
    (10, "partial 0.3, R_F 0.99", dict(partial=0.3, rel_F=0.99)),
    (11, "partial 0.3, R_x 0.90", dict(partial=0.3, rel_x=0.90)),
    (12, "partial 0, R_F 0.90, corr(40, sep) 0.6", dict(partial=0.0, rel_F=0.90, rho_forty=0.6)),
    (13, "partial 0, empirical residuals", dict(partial=0.0, empirical=True)),
    (14, "partial 0.3, empirical residuals", dict(partial=0.3, empirical=True)),
]


def stage_h2(out):
    rows = []
    for sid, label, sc in H2_SCENARIOS:
        n_rep = CFG["n_rep_h2"] if sid <= 5 else 300
        jobs = [(run_h2_once, dict(scen=sc, seed=sv._seed(200 + sid, r), leakage=(r < 100))) for r in range(n_rep)]
        t0 = time.time(); res = sv.run_parallel(jobs)
        for r, x in enumerate(res):
            rows.append(dict(scenario=sid, label=label, rep=r, **x))
        print("H2", sid, label, f"{time.time() - t0:.0f}s", flush=True)
    pl.DataFrame(rows, infer_schema_length=None).write_parquet(out / "h2.parquet")


# =================================================================================================
# family-wise: fixed sequence vs Holm, assembled from independent replicate results
# =================================================================================================
def stage_family(out):
    h1w = pl.read_parquet(out / "h1_WR.parquet"); h1d = pl.read_parquet(out / "h1_DB.parquet"); h2 = pl.read_parquet(out / "h2.parquet")

    def take(df, cond, est, n):
        d = df.filter(cond).sort("rep").head(n)
        return [dict(p=r["p"], direction_ok=r[est] > 0, extra=r) for r in d.iter_rows(named=True)]
    combos = [
        ("global null", dict(wr=1, db=1, h2=1)),
        ("H1-WR large, H2 null", dict(wr=5, db=1, h2=1)),
        ("H1-WR moderate, H2 partial 0.3", dict(wr=4, db=1, h2=4)),
        ("H1-WR large, H2 partial 0.3", dict(wr=5, db=1, h2=4)),
        ("H1-WR large, H2 partial 0.4", dict(wr=5, db=1, h2=5)),
        ("H1-WR null, H2 partial 0.4", dict(wr=1, db=1, h2=5)),
        ("H1-WR moderate, DB moderate, H2 null", dict(wr=4, db=4, h2=1)),
    ]
    rows = []
    for label, c in combos:
        a = take(h1w, pl.col("scenario") == c["wr"], "delta_reml", CFG["n_rep_family"])
        bb = take(h1d, pl.col("scenario") == c["db"], "delta_reml", CFG["n_rep_family"])
        h = take(h2, pl.col("scenario") == c["h2"], "beta_P_reml", CFG["n_rep_family"])
        n = min(len(a), len(bb), len(h))
        for k in range(n):
            fs = cf.fixed_sequence([a[k], h[k]], CFG["alpha"])
            ho = cf.holm([a[k], bb[k], h[k]], CFG["alpha"])
            rows.append(dict(combo=label, rep=k, fs_h1=fs[0], fs_h2=fs[1],
                             fs_h2_supported=fs[1] and h[k]["extra"]["h2_supported_if_reached"],
                             holm_h1=ho[0], holm_db=ho[1], holm_h2=ho[2],
                             any_fs=any(fs), any_holm=any(ho)))
    pl.DataFrame(rows).write_parquet(out / "family.parquet")
    print("family done")


# =================================================================================================
# selection: eligibility thresholds under selection mechanisms (common random numbers across rules)
# =================================================================================================
SEL_RULES = {"registered (>=100 opp, >=20/ctx)": dict(min_opp=100, min_ctx=20),
             "alt >=50 opp": dict(min_opp=50, min_ctx=20),
             "alt >=200 opp": dict(min_opp=200, min_ctx=20),
             "fewer obs: all pool (>=5/ctx)": dict(min_opp=0, min_ctx=5)}
SEL_MECH = [(1, "no selection, null", dict(rho_h=0.3, rho_l=0.3)),
            (2, "selection on deep-route level, null", dict(rho_h=0.3, rho_l=0.3, sel_outcome=1.0)),
            (3, "selection on capacity, null", dict(rho_h=0.3, rho_l=0.3, sel_capacity=1.0)),
            (4, "no selection, moderate", dict(rho_h=0.5, rho_l=0.3)),
            (5, "selection on deep-route level, moderate", dict(rho_h=0.5, rho_l=0.3, sel_outcome=1.0)),
            (6, "selection on capacity, moderate", dict(rho_h=0.5, rho_l=0.3, sel_capacity=1.0))]


def stage_selection(out):
    rows = []
    for mid, mlabel, sc in SEL_MECH:
        for rlabel, rule in SEL_RULES.items():
            jobs = [(sv.run_h1_once, dict(pos="WR", scen=sc, seed=sv._seed(300 + mid, r), subset=rule, naive=False))
                    for r in range(CFG["n_rep_sel"])]
            t0 = time.time(); res = sv.run_parallel(jobs)
            for r, x in enumerate(res):
                rows.append(dict(mech=mid, mechanism=mlabel, rule=rlabel, rep=r, **x))
            print("SEL", mid, rlabel, f"{time.time() - t0:.0f}s", flush=True)
    pl.DataFrame(rows, infer_schema_length=None).write_parquet(out / "selection.parquet")


def stage_selection_real(out):
    """Outcome-free real-data composition under eligibility rules (no combine values, no outcomes)."""
    rows = []
    players = pl.read_parquet(sv.INTERIM / "players.parquet").select("nfl_id", "draft_round")
    for pos in ("WR", "DB"):
        sk = pl.read_parquet(sv.SK / f"h1_{pos}.parquet")
        per = sk.group_by("pid").agg(pl.col("nfl_id").first(), pl.col("opp").first(), pl.col("dep").first(),
                                     (pl.col("ctx_i") == 0).sum().alias("n0"), (pl.col("ctx_i") == 1).sum().alias("n1"),
                                     pl.col("nfl_year").mean().alias("mean_year"), pl.col("team_i").n_unique().alias("team_seasons"),
                                     pl.len().alias("plays")).join(players, on="nfl_id", how="left")
        for rlabel, rule in SEL_RULES.items():
            e = per.filter((pl.col("opp") >= rule["min_opp"]) & (pl.col("n0") >= rule["min_ctx"]) & (pl.col("n1") >= rule["min_ctx"]))
            rows.append(dict(pos=pos, rule=rlabel, players=e.height, plays=int(e["plays"].sum()),
                             median_plays_hi=float(e["n0"].median()), median_plays_lo=float(e["n1"].median()),
                             mean_high_demand_share=float(e["dep"].mean()), sd_high_demand_share=float(e["dep"].std()),
                             mean_nfl_year=float(e["mean_year"].mean()), mean_team_seasons=float(e["team_seasons"].mean()),
                             share_round1_2=float((e["draft_round"].fill_null(8) <= 2).mean()),
                             share_udfa=float(e["draft_round"].is_null().mean())))
    pl.DataFrame(rows).write_parquet(out / "selection_real.parquet")
    print(pl.DataFrame(rows))


# =================================================================================================
# demand-measure validation (real, outcome-only) + leakage simulation
# =================================================================================================
def _demand_plays():
    from run_power_analysis import PRIMARY_OPP, primary_opp_counts, tracked40_ids
    d = reg_play_table().filter(pl.col("play_nullified_by_penalty") != "Y")
    ids = tracked40_ids().implode(); opp = primary_opp_counts(d)
    rows = []
    for pos in ("WR", "TE", "DB", "DL", "OL"):
        el = opp.filter((pl.col("pos") == pos) & (pl.col(PRIMARY_OPP[pos]) >= 100) & pl.col("nfl_id").is_in(ids))["nfl_id"]
        allp = d.filter((pl.col("pos") == pos) & pl.col("nfl_id").is_in(el.implode()) & pl.col("vmax_play").is_not_null())
        ctxp = h1_frame(d, pos).filter(pl.col("nfl_id").is_in(el.implode()) & pl.col("vmax_play").is_not_null())
        rows.append((pos, allp.select("nfl_id", "game_id", "play_id", "vmax_play"),
                     ctxp.select("nfl_id", "game_id", "play_id", "ctx", "vmax_play")))
    return rows


def stage_demand_real(out):
    res, cells, stab, xf, oos = [], [], [], [], []
    for pos, allp, ctxp in _demand_plays():
        top = dm.player_top5(allp)
        sh = dm.player_shares(ctxp, top=top)
        sh = sh.with_columns(pl.lit(pos).alias("pos"))
        res.append(sh)
        for col in ("share_85", "share_90", "share_95", "share_abs"):
            for mp in (1, 20):
                cd = dm.cell_demand(sh, col, mp).with_columns(pl.lit(pos).alias("pos"), pl.lit(col).alias("def"), pl.lit(mp).alias("min_plays"))
                cells.append(cd)
        # player-level agreement between thresholds within each cell (players with >= 20 plays in the cell)
        for c in sh["ctx"].unique().to_list():
            s = sh.filter((pl.col("ctx") == c) & (pl.col("n") >= 20))
            if s.height > 8:
                from scipy.stats import spearmanr
                stab.append(dict(pos=pos, ctx=c, n=s.height,
                                 rho_85_90=spearmanr(s["share_85"], s["share_90"])[0], rho_90_95=spearmanr(s["share_90"], s["share_95"])[0],
                                 rho_85_95=spearmanr(s["share_85"], s["share_95"])[0], rho_90_abs=spearmanr(s["share_90"], s["share_abs"])[0]))
        # registered cross-fit split (seed 3503) and instability over 500 random splits
        ids = sh["nfl_id"].unique().to_numpy()
        full = dm.cell_demand(sh, "share_90").rename({"D": "D_full"})
        A, Bh = dm.crossfit_halves(ids)
        for nm, half in (("A", A), ("B", Bh)):
            dh = dm.cell_demand(sh.filter(pl.col("nfl_id").is_in(half)), "share_90").rename({"D": "D_half"})
            xf.append(full.join(dh, on="ctx").with_columns(pl.lit(pos).alias("pos"), pl.lit(nm).alias("half"), pl.lit(-1).alias("split")))
        for sidx in range(500):
            A, Bh = dm.crossfit_halves(ids, seed=10_000 + sidx)
            dh = dm.cell_demand(sh.filter(pl.col("nfl_id").is_in(A)), "share_90").rename({"D": "D_half"})
            xf.append(full.join(dh, on="ctx").with_columns(pl.lit(pos).alias("pos"), pl.lit("A").alias("half"), pl.lit(sidx).alias("split")))
        # out-of-sample T: T from odd games, share on even games (and vice versa) -> self-reference check
        g = allp.select("nfl_id", "game_id").unique().sort("nfl_id", "game_id").with_columns((pl.int_range(pl.len()).over("nfl_id") % 2).alias("half"))
        a2 = allp.join(g, on=["nfl_id", "game_id"]); c2 = ctxp.join(g, on=["nfl_id", "game_id"])
        for h in (0, 1):
            t_in = dm.player_top5(a2.filter(pl.col("half") == h)); t_out = dm.player_top5(a2.filter(pl.col("half") != h))
            s_in = dm.player_shares(c2.filter(pl.col("half") == h), top=t_in, absolute=None)
            s_out = dm.player_shares(c2.filter(pl.col("half") == h), top=t_out, absolute=None)
            for nm, s in (("in_sample_T", s_in), ("out_of_sample_T", s_out)):
                oos.append(dm.cell_demand(s, "share_90").with_columns(pl.lit(pos).alias("pos"), pl.lit(nm).alias("T_source"), pl.lit(h).alias("half")))
            # player-level split-half reliability of the share (same T source)
        print("demand", pos, flush=True)
    pl.concat(res).write_parquet(out / "demand_player_shares.parquet")
    pl.concat(cells).write_parquet(out / "demand_cells.parquet")
    pl.DataFrame(stab).write_parquet(out / "demand_threshold_agreement.parquet")
    pl.concat(xf).write_parquet(out / "demand_crossfit.parquet")
    pl.concat(oos).write_parquet(out / "demand_oos_T.parquet")


def stage_demand_reliability(out):
    """Player-level split-half (game parity) reliability of share_90 per cell, T fixed from all plays."""
    from scipy.stats import spearmanr
    rows = []
    for pos, allp, ctxp in _demand_plays():
        top = dm.player_top5(allp)
        g = ctxp.select("nfl_id", "game_id").unique().sort("nfl_id", "game_id").with_columns((pl.int_range(pl.len()).over("nfl_id") % 2).alias("half"))
        c2 = ctxp.join(g, on=["nfl_id", "game_id"])
        s0 = dm.player_shares(c2.filter(pl.col("half") == 0), top=top, absolute=None)
        s1 = dm.player_shares(c2.filter(pl.col("half") == 1), top=top, absolute=None)
        j = s0.join(s1, on=["nfl_id", "ctx"], suffix="_1").filter((pl.col("n") >= 10) & (pl.col("n_1") >= 10))
        for c in j["ctx"].unique().to_list():
            jj = j.filter(pl.col("ctx") == c)
            for th in (85, 90, 95):
                if jj.height > 8:
                    r = spearmanr(jj[f"share_{th}"], jj[f"share_{th}_1"])[0]
                    rows.append(dict(pos=pos, ctx=c, threshold=th, n=jj.height, split_half=r, spearman_brown=2 * r / (1 + r)))
    pl.DataFrame(rows).write_parquet(out / "demand_reliability.parquet")


def _demand_sim_once(seed, lam, crossfit, n_players=55):
    """Synthetic 11-cell world: player play-max speeds per cell with real-like demand spread; capacity x
    correlated with player level at rho_k = 0.3 + lam * (D_k - mean D). Meta-regress rho_hat on D_hat."""
    rng = np.random.default_rng(seed)
    cells = [("WR", 7.6, 1.0), ("WR", 6.3, 0.8), ("TE", 7.0, 1.0), ("TE", 5.8, 0.8), ("DB", 6.6, 1.2), ("DB", 5.9, 1.1),
             ("DB", 5.5, 1.1), ("DL", 4.6, 1.1), ("DL", 3.5, 1.2), ("OL", 3.2, 0.9), ("OL", 3.0, 1.0)]
    Dtrue = np.array([0.17, 0.01, 0.19, 0.03, 0.07, 0.03, 0.02, 0.03, 0.01, 0.01, 0.01])
    rho_k = 0.3 + lam * (Dtrue - Dtrue.mean())
    out = dict(rho=[], se=[], D=[], pos=[])
    positions = {}
    for k, (pos, mu, sd) in enumerate(cells):
        positions.setdefault(pos, []).append(k)
    for pos, ks in positions.items():
        P = n_players
        z = rng.standard_normal(P)
        x = np.sqrt(0.987) * z + np.sqrt(0.013) * rng.standard_normal(P)
        top_pool = []
        per = {}
        for k in ks:
            _, mu, sd = cells[k]
            lev = 0.25 * (rho_k[k] * z + np.sqrt(1 - rho_k[k] ** 2) * rng.standard_normal(P))
            n = rng.integers(40, 300, P)
            plays = [mu + lev[i] + sd * rng.standard_normal(n[i]) for i in range(P)]
            per[k] = (plays, n)
            top_pool.append(plays)
        T = np.array([np.sort(np.concatenate([top_pool[j][i] for j in range(len(ks))]))[-5:].mean() for i in range(P)])
        idx = rng.permutation(P); hA, hB = idx[: P // 2], idx[P // 2:]
        for k in ks:
            plays, n = per[k]
            share = np.array([(plays[i] >= 0.9 * T[i]).mean() for i in range(P)])
            m = np.array([p.mean() for p in plays]); sw2 = np.mean([p.var(ddof=1) for p in plays])
            if crossfit:   # D from half A, rho from half B (and swap); average
                rhos, Ds = [], []
                for a_, b_ in ((hA, hB), (hB, hA)):
                    rr, _ = cf.moment_rho(x[b_], m[b_, None], n[b_, None].astype(float), np.array([sw2]))
                    rhos.append(rr[0]); Ds.append(np.median(share[a_]))
                rho_hat, D_hat, nn = np.mean(rhos), np.mean(Ds), P // 2
            else:
                rr, _ = cf.moment_rho(x, m[:, None], n[:, None].astype(float), np.array([sw2]))
                rho_hat, D_hat, nn = rr[0], np.median(share), P
            out["rho"].append(rho_hat); out["se"].append((1 - min(rho_hat ** 2, 0.9)) / np.sqrt(nn - 3)); out["D"].append(D_hat); out["pos"].append(pos)
    lam_hat, lam_se, om = dm.meta_regression_reml(out["rho"], out["se"], out["D"], out["pos"])
    return dict(lam_hat=lam_hat, lam_se=lam_se, omega2=om, reject=bool(abs(lam_hat / lam_se) > 1.96 and lam_hat > 0))


def stage_demand_sim(out):
    rows = []
    for lam in (0.0, 1.5, 3.0):
        for crossfit in (True, False):
            jobs = [(_demand_sim_once, dict(seed=sv._seed(500 + int(lam * 10) + (1 if crossfit else 0), r), lam=lam, crossfit=crossfit))
                    for r in range(400)]
            res = sv.run_parallel(jobs)
            for r, x in enumerate(res):
                rows.append(dict(lam=lam, crossfit=crossfit, rep=r, **x))
            print("demand sim", lam, crossfit, flush=True)
    pl.DataFrame(rows).write_parquet(out / "demand_sim.parquet")


# =================================================================================================
# H1: registered REML-in-bootstrap inference, validated with the warp-speed Monte Carlo method
# (Giacomini, Politis & White 2013): a few bootstrap draws per replicate, pooled across replicates to
# estimate the (centred) bootstrap distribution. Calibrated against the exact full-B moment bootstrap.
# =================================================================================================
def run_h1_warp_once(pos, scen, seed, nb=10):
    sk, par = sv._load(pos)
    rng = np.random.default_rng(seed)
    gen = dict(rel_x=scen.get("rel_x", CFG["rel_x"]), r_dep=scen.get("r_dep", CFG["r_dep"]),
               route_confound=scen.get("route_confound", 0.0), sel_outcome=scen.get("sel_outcome", 0.0),
               thin_low=scen.get("thin_low", 1.0), sel_capacity=scen.get("sel_capacity", 0.0))
    sim, xall, truth, z = cs.simulate_h1(sk, par, scen["rho_h"], scen["rho_l"], rng, **gen)
    sel = sim["keep"] & sk["eligible"].to_numpy()
    sub = sk.filter(pl.Series(sel)).with_columns(pl.Series("y", sim["y"][sel]))
    pids = np.unique(sub["pid"].to_numpy()); pmap = -np.ones(int(sk["pid"].max()) + 1, int); pmap[pids] = np.arange(len(pids))
    _, team = np.unique(sub["team_i"].to_numpy(), return_inverse=True)
    player = pmap[sub["pid"].to_numpy()]; ctx = sub["ctx_i"].to_numpy(); y = sub["y"].to_numpy(); x = xall[pids]
    Xw, Wres = sv._design(sub, pos)
    full = cf.h1_procedure(player, ctx, team, y, Xw, Wres, x, CFG["B_h1"], rng, CFG["alpha"])
    reml = cf.h1_reml(player, ctx, team, y, Xw, x)   # (deterministic: same fit as inside h1_procedure)
    rng2 = np.random.default_rng(seed + 1)
    rb = cf.h1_reml_bootstrap(player, ctx, team, y, Xw, x, nb, rng2, start=reml.extra["theta"])["boot"]
    r = cf.residualise_np(Wres, y)
    m, n, sw2 = cf.player_context_stats(player, ctx, r, len(pids))
    bi = rng2.integers(0, len(pids), (nb, len(pids)))
    mrho, _ = cf.moment_rho(x[bi], m[bi], n[bi], sw2)
    return dict(delta_reml=reml.delta, delta_moment=full["delta_moment"], supported_full_moment=full["supported"],
                ci_lo_full=full["ci_lo"], true_delta_obs=truth.delta_obs_scale,
                reml_boot=list(map(float, rb)), moment_boot=list(map(float, mrho[:, 0] - mrho[:, 1])))


WARP_SCEN = [1, 2, 3, 4, 5, 6, 7]


def stage_h1_warp(out):
    rows = []
    scen = {s[0]: s for s in sv.H1_SCENARIOS}
    for sid in WARP_SCEN:
        _, label, sc = scen[sid]
        sc = {k: v for k, v in sc.items() if k != "subset"}
        jobs = [(run_h1_warp_once, dict(pos="WR", scen=sc, seed=sv._seed(sid, r))) for r in range(CFG["n_rep_h1"])]
        t0 = time.time(); res = sv.run_parallel(jobs)
        for r, x in enumerate(res):
            rows.append(dict(scenario=sid, label=label, rep=r, **x))
        print("WARP", sid, label, f"{time.time() - t0:.0f}s", flush=True)
    pl.DataFrame(rows, infer_schema_length=None).write_parquet(out / "h1_warp.parquet")


def warp_decisions(df: pl.DataFrame, est: str, boots: str, alpha=0.05):
    """Warp-speed percentile CI: Delta_hat_r + quantiles of the pooled centred draws (Delta*_rb - Delta_hat_r)."""
    out = []
    for key, g in df.group_by(["scenario", "label"], maintain_order=True):
        cen = np.concatenate([np.asarray(b) - e for b, e in zip(g[boots].to_list(), g[est].to_list())])
        cen = cen[np.isfinite(cen)]
        qlo, qhi = np.percentile(cen, [100 * alpha / 2, 100 * (1 - alpha / 2)])
        d = g[est].to_numpy(); tr = g["true_delta_obs"].to_numpy()
        rej = (d > 0) & (d + qlo > 0)
        cov = (d + qlo <= tr) & (d + qhi >= tr)
        out.append(dict(scenario=key[0], label=key[1], estimator=est, reps=g.height, pooled_draws=len(cen),
                        reject=float(rej.mean()), reject_mcse=float(np.sqrt(rej.mean() * (1 - rej.mean()) / g.height)),
                        coverage95=float(cov.mean()), boot_sd=float(cen.std()), sd_estimate=float(d.std(ddof=1)),
                        bias=float((d - tr).mean())))
    return pl.DataFrame(out)


def stage_h1_s8fix(out):
    """S6 (differential reliability) re-run with the registered >= 20 plays/context rule applied AFTER thinning
    (the first run kept players whose thinned low-demand context had < 20 plays, which the protocol excludes)."""
    sid, label, sc = [s for s in sv.H1_SCENARIOS if s[0] == 8][0]
    sc = dict(sc)
    jobs = [(sv.run_h1_once, dict(pos="WR", scen=sc, seed=sv._seed(sid, r), subset=dict(min_opp=100, min_ctx=20))) for r in range(CFG["n_rep_h1"])]
    res = sv.run_parallel(jobs)
    pl.DataFrame([dict(pos="WR", scenario=8, label=label + " [registered >=20/ctx after thinning]", rep=r, **x) for r, x in enumerate(res)],
                 infer_schema_length=None).write_parquet(out / "h1_WR_s8fix.parquet")


def run_h1_direct_once(pos, scen, seed, B=400):
    """Direct (non-warp) registered REML player bootstrap with B draws for one replicate; same dataset as
    run_h1_warp_once / run_h1_once for this seed (the simulation consumes the same RNG stream)."""
    sk, par = sv._load(pos)
    rng = np.random.default_rng(seed)
    sim, xall, truth, z = cs.simulate_h1(sk, par, scen["rho_h"], scen["rho_l"], rng, rel_x=CFG["rel_x"], r_dep=scen.get("r_dep", CFG["r_dep"]),
                                         route_confound=scen.get("route_confound", 0.0))
    sel = sim["keep"] & sk["eligible"].to_numpy()
    sub = sk.filter(pl.Series(sel)).with_columns(pl.Series("y", sim["y"][sel]))
    pids = np.unique(sub["pid"].to_numpy()); pmap = -np.ones(int(sk["pid"].max()) + 1, int); pmap[pids] = np.arange(len(pids))
    _, team = np.unique(sub["team_i"].to_numpy(), return_inverse=True)
    player = pmap[sub["pid"].to_numpy()]; ctx = sub["ctx_i"].to_numpy(); y = sub["y"].to_numpy(); x = xall[pids]
    Xw, _ = sv._design(sub, pos)
    reml = cf.h1_reml(player, ctx, team, y, Xw, x)
    bt = cf.h1_reml_bootstrap(player, ctx, team, y, Xw, x, B, np.random.default_rng(seed + 7), start=reml.extra["theta"])
    return dict(delta_reml=reml.delta, ci_lo=bt["ci"][0], ci_hi=bt["ci"][1], se=bt["se"], n_ok=bt["n_ok"],
                true_delta_obs=truth.delta_obs_scale, boot_q=list(map(float, np.percentile(bt["boot"], [2.5, 5, 50, 95, 97.5]))))


def stage_h1_direct(out):
    rows = []
    scen = {s[0]: s for s in sv.H1_SCENARIOS}
    for sid, nrep in ((1, 60), (6, 40)):
        _, label, sc = scen[sid]
        jobs = [(run_h1_direct_once, dict(pos="WR", scen=sc, seed=sv._seed(sid, r))) for r in range(nrep)]
        t0 = time.time(); res = sv.run_parallel(jobs)
        rows += [dict(scenario=sid, label=label, rep=r, **x) for r, x in enumerate(res)]
        print("DIRECT", sid, f"{time.time() - t0:.0f}s", flush=True)
    pl.DataFrame(rows, infer_schema_length=None).write_parquet(out / "h1_direct.parquet")
