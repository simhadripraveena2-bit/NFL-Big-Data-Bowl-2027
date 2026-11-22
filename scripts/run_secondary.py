"""Registered secondary analyses (preregistration §2, §9, §12; spec §1, §1.4, §3). Run once.

Hierarchy (D4): H1-WR primary (done, frozen); H2 secondary estimation (done). THIS RUN:
  Holm secondary family, alpha = 0.05, m = 4:  H1-DB, H1-DL(a), H1-DL(b), H5(b)
  estimation only:  H5(a) (= registered OL negative control N2), H5(c), H1-global (demand meta-regression)
  descriptive only: H1-TE (point estimates + Wald CIs; needed as meta-regression input)
  exploratory:      DL role subgroups (EDGE-only, interior-only)

Declared before the run (operational choices the registration leaves open):
  * Tests use `h1_registered_test` (REML + full REML player-cluster percentile bootstrap, B = 2000, D1/D2) where the
    quantity is a single-model Delta. p = two-sided percentile-bootstrap p (CI inversion, `confirmatory.boot_p`);
    a hypothesis can be rejected only in the predicted direction (all four predicted > 0).
  * Holm (§9): step-down at alpha/(m-k+1); adjusted p-values reported; Holm-level CIs = percentile intervals at the
    level of the step each hypothesis is tested at. Decision rules §12: supported iff Holm-adjusted CI excludes 0 in
    the predicted direction. Falsified: H1-DB / H1-DL(a) 90 % CI upper < 0.15; H1-DL(b) 95 % CI includes 0 and its
    upper bound < 0.10; H5(b) 90 % CI upper < 0.
  * H1-DL(b): "pooled DL translation" := mean of rho_pass-rush and rho_run from the registered bivariate DL model.
    Adjusted model = registered model + player alignment (modal REG lined_up_position: EDGE = 1, INTERIOR_LINE = 0)
    x context + standardised combine weight (within DL, all combine participants) x context. Quantity = pooled_base
    - pooled_adjusted; paired registered-scheme bootstrap, B = 2000 (4 chunks x 500).
  * H5(b): Delta_WR - Delta_OL; Delta_WR and its 2000 bootstrap draws are the FROZEN primary run (seed 4004);
    Delta_OL from this run's registered test; CI from the independent player bootstraps (draw-wise difference).
  * H5(a): Delta_OL with 95 % / 90 % CI; "consistent with the demand model" iff the 90 % CI lies within +/-0.15.
  * H1-global / H5(c): rho_k for the 11 position-context cells (DB with its three contexts in one model) fitted on
    the registered cross-fit halves (seed 3503, halves of the demand-eligible players), se_k = delta-method SE
    (numerical REML Hessian); D_k = cross-fitted demand of the OTHER half (validated Phase 4 demand code);
    meta-regressions for both swaps averaged. H5(c): meta-regression WITHOUT OL cells; prediction for OL =
    mean position intercept + lambda * mean(D of the two OL cells); observed = pooled OL rho (mean of contexts) on the
    rho-half; 90 % prediction interval with t(df = 9 - 5) and sqrt(se_obs^2 + omega^2 + se_fit^2); averaged over swaps.
    Cell-cluster bootstrap within position for lambda (B = 2000).
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
from scipy import stats  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from nfl_bdb.data import confirmatory_data as cd  # noqa: E402
from nfl_bdb.data.play_table import H1_COVARIATES, h1_frame  # noqa: E402
from nfl_bdb.features import demand as dm  # noqa: E402
from nfl_bdb.models import confirmatory as cf  # noqa: E402
from nfl_bdb.models import secondary as sc  # noqa: E402

JOIN = ROOT / "data/interim/confirmatory_join/20261121T135032Z"
PRIMARY = ROOT / "experiments/h1_wr_confirmatory/20261121T223645Z"
OUTROOT = ROOT / "experiments/secondary"
B = cf.H1_B_REGISTERED; ALPHA = 0.05
SEEDS = dict(DB=8001, DL=8002, OL=8003, DLb=[8101, 8102, 8103, 8104], meta_boot=8201)
CTX = {"WR": ["deep", "short"], "TE": ["deep", "short"], "DB": ["man", "under_zone"], "DB3": ["man", "deep_zone", "under_zone"],
       "DL": ["pass_rush", "run"], "OL": ["pass_block", "run"]}


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def frame(pos):
    return pl.read_parquet(JOIN / f"h1_{pos}.parquet")


def db3_frame():
    pred = pl.read_parquet(JOIN / "predictors.parquet")
    d, _ = cd.outcome_table()
    el = pl.read_parquet(JOIN / "eligibility_h1_DB.parquet").filter(pl.col("elig_h1"))["nfl_id"].implode()
    fr = h1_frame(d, "DB").filter(pl.col("ctx").is_in(CTX["DB3"]) & pl.col("nfl_id").is_in(el))
    return cd.join_predictors(fr, pred).select(frame("DB").columns)


def dl_adjusted_design(dfi, Xw, d=2):
    cr = pl.read_parquet(ROOT / "data/interim/combine_results.parquet").filter(pl.col("combine_position") == "DL")
    wz = cr.with_columns(((pl.col("combine_weight") - pl.col("combine_weight").mean()) / pl.col("combine_weight").std()).alias("wz")).select("nfl_id", "wz")
    role = (dfi.group_by("pid", "lined_up_position").len().sort(["pid", "len"], descending=[False, True]).group_by("pid", maintain_order=True)
            .agg(pl.col("lined_up_position").first().alias("modal")))
    pp = dfi.select("pid", "nfl_id").unique().sort("pid").join(role, on="pid").join(wz, on="nfl_id", how="left").sort("pid")
    edge = (pp["modal"] == "EDGE").to_numpy().astype(float); w = pp["wz"].to_numpy().astype(float)
    player, ctx = dfi["pid"].to_numpy(), dfi["ctx_i"].to_numpy()
    Xa = cf.full_rank(np.column_stack([Xw, sc.player_ctx_columns(np.column_stack([edge, w]), player, ctx, d)]))
    return Xa, dict(edge=int(edge.sum()), interior=int((1 - edge).sum()), weight_missing=int(np.isnan(w).sum()), modal=pp.select("pid", "modal"))


def job_test(args):
    pos, seed = args
    dfi, ids = sc.index_frame(frame(pos), CTX[pos])
    player, ctx, team, y, xp = sc.arrays(dfi)
    Xw = cf.design_h1(dfi, H1_COVARIATES[pos], 2)
    r = cf.h1_registered_test(player, ctx, team, y, Xw, xp, seed=seed, B=B)
    boot = r.pop("boot")
    return pos, dict(delta=r["delta"], rho=[float(v) for v in r["rho"]], beta=[float(v) for v in r["beta"]], sigma_b=np.asarray(r["sigma_b"]).tolist(),
                     s2_team=float(r["s2_team"]), converged=r["converged"], ci95=[r["ci_lo"], r["ci_hi"]], se_boot=r["se_boot"], p=r["p"], n_ok=r["n_ok"],
                     players=len(xp), plays=dfi.height, plays_by_ctx={c: int((ctx == i).sum()) for i, c in enumerate(CTX[pos])},
                     team_seasons=int(team.max() + 1), x_sd=float(np.std(xp, ddof=1)), seed=seed), boot


def job_dlb(seed):
    dfi, _ = sc.index_frame(frame("DL"), CTX["DL"])
    player, ctx, team, y, xp = sc.arrays(dfi)
    Xw = cf.design_h1(dfi, H1_COVARIATES["DL"], 2); Xa, _ = dl_adjusted_design(dfi, Xw)
    b0 = cf.h1_reml(player, ctx, team, y, Xw, xp); a0 = cf.h1_reml(player, ctx, team, y, Xa, xp)
    return sc.dlb_bootstrap(player, ctx, team, y, Xw, Xa, xp, B // 4, seed, start_base=b0.extra["theta"], start_adj=a0.extra["theta"])


def job_wald(args):
    name, df, contexts, covs, extra = args
    dfi, ids = sc.index_frame(df, contexts)
    player, ctx, team, y, xp = sc.arrays(dfi)
    d = len(contexts)
    Xw = cf.design_h1(dfi, covs, d)
    if extra == "dl_adjusted":
        Xw, info = dl_adjusted_design(dfi, Xw)
    try:
        w = sc.rho_wald(player, ctx, team, y, Xw, xp, d)
    except Exception as e:  # noqa: BLE001  (e.g. a 9-player TE half): reported, cell dropped from the meta-regression
        return name, dict(contexts=contexts, error=repr(e), players=len(xp), plays=dfi.height)
    return name, dict(contexts=contexts, rho=w["rho"].tolist(), cov=w["cov"].tolist(), se=w["se"].tolist(), converged=w["converged"],
                      players=len(xp), plays=dfi.height, sigma_b=np.asarray(w["sigma_b"]).tolist(), s2_team=float(w["s2_team"]),
                      s2_resid=np.asarray(w["s2_resid"]).tolist(), hessian_min_eig=w["hessian_min_eig"])


def main():
    if git("status", "--porcelain", "--", "src", "scripts", "tests"):
        raise SystemExit("refusing to run from uncommitted code")
    if OUTROOT.exists() and any(p.name != "LATEST" for p in OUTROOT.iterdir()):
        raise SystemExit("a secondary run already exists; the registered analyses are run once")
    t0 = time.time()
    # ---------------- demand (validated Phase 4 code) and cross-fit halves ----------------
    import phase4_stages as ps
    D_half, halves = {}, {}
    for pos, allp, ctxp in ps._demand_plays():
        top = dm.player_top5(allp); sh = dm.player_shares(ctxp, top=top)
        A, Bh = dm.crossfit_halves(sh["nfl_id"].unique().to_numpy())
        halves[pos] = dict(A=A.tolist(), B=Bh.tolist())
        for nm, half in (("A", A), ("B", Bh)):
            for row in dm.cell_demand(sh.filter(pl.col("nfl_id").is_in(half)), "share_90").iter_rows(named=True):
                D_half[(pos, row["ctx"], nm)] = row["D"]
        for row in dm.cell_demand(sh, "share_90").iter_rows(named=True):
            D_half[(pos, row["ctx"], "full")] = row["D"]
    frames = {p: frame(p) for p in ("WR", "TE", "DB", "DL", "OL")}; frames["DB3"] = db3_frame()
    # wald jobs: full sample + halves
    wjobs = []
    for p in ("WR", "TE", "DB", "DL", "OL", "DB3"):
        base = "DB" if p == "DB3" else p
        wjobs.append((f"{p}_full", frames[p], CTX[p], H1_COVARIATES[base], None))
    wjobs.append(("DL_full_adjusted", frames["DL"], CTX["DL"], H1_COVARIATES["DL"], "dl_adjusted"))
    for p in ("WR", "TE", "DB3", "DL", "OL"):
        base = "DB" if p == "DB3" else p
        for nm in ("A", "B"):
            ids = halves[base][nm]
            wjobs.append((f"{p}_half{nm}", frames[p].filter(pl.col("nfl_id").is_in(ids)), CTX[p], H1_COVARIATES[base], None))
    # exploratory DL role subgroups
    dfi_dl, _ = sc.index_frame(frames["DL"], CTX["DL"])
    _, info = dl_adjusted_design(dfi_dl, cf.design_h1(dfi_dl, H1_COVARIATES["DL"], 2))
    modal = info["modal"].join(dfi_dl.select("pid", "nfl_id").unique(), on="pid")
    for role in ("EDGE", "INTERIOR_LINE"):
        ids = modal.filter(pl.col("modal") == role)["nfl_id"].to_list()
        wjobs.append((f"DL_{role}_only", frames["DL"].filter(pl.col("nfl_id").is_in(ids)), CTX["DL"], H1_COVARIATES["DL"], None))

    with ProcessPoolExecutor(4, mp_context=mp.get_context("spawn")) as ex:
        ft = {p: ex.submit(job_test, (p, SEEDS[p])) for p in ("DB", "DL", "OL")}
        fb = [ex.submit(job_dlb, s) for s in SEEDS["DLb"]]
        fw = [ex.submit(job_wald, j) for j in wjobs]
        tests, boots = {}, {}
        for p, f in ft.items():
            _, tests[p], boots[p] = f.result(); print("test", p, flush=True)
        dlb = np.vstack([f.result() for f in fb]); print("DL(b) bootstrap done", flush=True)
        wald = dict(f.result() for f in fw); print("wald done", flush=True)

    # ---------------- Holm family ----------------
    wr_boot = np.load(PRIMARY / "bootstrap_delta.npy"); wr = json.load(open(PRIMARY / "h1_wr_result.json"))["primary"]
    h5b_draws = wr_boot - boots["OL"]
    ok = np.isfinite(dlb[:, 4]) & np.isfinite(dlb[:, 5]); dlb_diff = dlb[ok, 4] - dlb[ok, 5]
    dl_base = wald["DL_full"]; dl_adj = wald["DL_full_adjusted"]
    dlb_est = float(np.mean(dl_base["rho"]) - np.mean(dl_adj["rho"]))
    fam = {
        "H1-DB": dict(estimate=tests["DB"]["delta"], draws=boots["DB"], p=tests["DB"]["p"]),
        "H1-DL(a)": dict(estimate=tests["DL"]["delta"], draws=boots["DL"], p=tests["DL"]["p"]),
        "H1-DL(b)": dict(estimate=dlb_est, draws=dlb_diff, p=cf.boot_p(dlb_diff)),
        "H5(b)": dict(estimate=wr["delta"] - tests["OL"]["delta"], draws=h5b_draws, p=cf.boot_p(h5b_draws)),
    }
    names = list(fam); pv = [fam[k]["p"] for k in names]
    adj = sc.holm_adjusted(pv); dec = cf.holm([dict(p=fam[k]["p"], direction_ok=fam[k]["estimate"] > 0) for k in names], ALPHA)
    order = np.argsort(pv); step = {names[i]: k for k, i in enumerate(order)}
    family = {}
    for k, nm in enumerate(names):
        dr = fam[nm]["draws"]; lev = ALPHA / (len(names) - step[nm])
        ci95 = np.percentile(dr, [2.5, 97.5]).tolist(); ci90 = np.percentile(dr, [5, 95]).tolist()
        ciH = np.percentile(dr, [100 * lev / 2, 100 * (1 - lev / 2)]).tolist()
        est = fam[nm]["estimate"]
        if nm in ("H1-DB", "H1-DL(a)"):
            fals = ci90[1] < 0.15
        elif nm == "H1-DL(b)":
            fals = (ci95[0] <= 0 <= ci95[1]) and ci95[1] < 0.10
        else:
            fals = ci90[1] < 0
        sup = bool(dec[k])
        family[nm] = dict(estimate=est, p_unadjusted=pv[k], p_holm=adj[k], holm_step=int(step[nm] + 1), holm_alpha=lev, ci95=ci95, ci90=ci90,
                          ci_holm_level=ciH, se_boot=float(np.std(dr)), n_draws=int(len(dr)), supported=sup, falsified=bool(fals) and not sup,
                          decision="SUPPORTED" if sup else ("FALSIFIED" if fals else "INCONCLUSIVE"))
    # §9 sensitivity Holm over {H1-WR, H1-DB, H2}
    h2p = json.load(open(ROOT / "experiments/h2_estimation" / (ROOT / "experiments/h2_estimation/LATEST").read_text().strip() / "h2_result.json"))
    sens_p = [wr["p_two_sided"], tests["DB"]["p"], h2p["p_boot_reml"]]
    sens = dict(names=["H1-WR", "H1-DB", "H2"], p=sens_p, p_holm=sc.holm_adjusted(sens_p),
                decisions=cf.holm([dict(p=sens_p[0], direction_ok=wr["delta"] > 0), dict(p=sens_p[1], direction_ok=tests["DB"]["delta"] > 0),
                                   dict(p=sens_p[2], direction_ok=h2p["deep"]["beta_P"] > 0)], ALPHA))

    # ---------------- H5(a) ----------------
    ol = tests["OL"]; ol90 = np.percentile(boots["OL"], [5, 95]).tolist()
    h5a = dict(delta=ol["delta"], ci95=ol["ci95"], ci90=ol90, p=ol["p"], consistent_with_demand_model=bool(-0.15 <= ol90[0] and ol90[1] <= 0.15))

    # ---------------- H1-global and H5(c): cross-fitted meta-regression ----------------
    cell_names = [("WR", "deep"), ("WR", "short"), ("TE", "deep"), ("TE", "short"), ("DB", "man"), ("DB", "deep_zone"), ("DB", "under_zone"),
                  ("DL", "pass_rush"), ("DL", "run"), ("OL", "pass_block"), ("OL", "run")]

    def cells_for(rho_half, d_half):
        rows = []
        for pos, c in cell_names:
            key = f"{'DB3' if pos == 'DB' else pos}_half{rho_half}"
            w = wald[key]; i = w["contexts"].index(c)
            if "error" in w or not np.isfinite(w["se"][i]):
                continue
            rows.append(dict(pos=pos, ctx=c, rho=w["rho"][i], se=w["se"][i], D=D_half[(pos, c, d_half)], players=w["players"]))
        return rows
    swaps = {"D_A_rho_B": cells_for("B", "A"), "D_B_rho_A": cells_for("A", "B")}
    glob, h5c = {}, {}
    for sw, rows in swaps.items():
        R_ = pl.DataFrame(rows)
        m_all = sc.meta_reml_full(R_["rho"].to_numpy(), R_["se"].to_numpy(), R_["D"].to_numpy(), R_["pos"].to_list())
        lb = sc.meta_cell_bootstrap(R_["rho"].to_numpy(), R_["se"].to_numpy(), R_["D"].to_numpy(), R_["pos"].to_list(), B, SEEDS["meta_boot"])
        glob[sw] = dict(cells=rows, lam=m_all["lam"], lam_se=m_all["lam_se"], omega2=m_all["omega2"], coef=m_all["coef"].tolist(), levels=m_all["levels"],
                        lam_boot_ci95=np.percentile(lb, [2.5, 97.5]).tolist() if len(lb) else None, n_boot=int(len(lb)))
        noOL = R_.filter(pl.col("pos") != "OL")
        m = sc.meta_reml_full(noOL["rho"].to_numpy(), noOL["se"].to_numpy(), noOL["D"].to_numpy(), noOL["pos"].to_list())
        D_ol = float(R_.filter(pl.col("pos") == "OL")["D"].mean())
        L = len(m["levels"]); x0 = np.concatenate([np.full(L, 1 / L), [D_ol]])
        pred = float(x0 @ m["coef"]); se_fit2 = float(x0 @ m["cov"] @ x0)
        ol_half = wald[f"OL_half{'B' if sw == 'D_A_rho_B' else 'A'}"]   # (OL half fits are 26-27 players)
        cov = np.asarray(ol_half["cov"]); obs = float(np.mean(ol_half["rho"])); se_obs2 = float(np.ones(2) @ cov @ np.ones(2) / 4)
        df_ = len(noOL) - (L + 1); tq = float(stats.t.ppf(0.95, df_))
        half_w = tq * np.sqrt(se_obs2 + m["omega2"] + se_fit2)
        h5c[sw] = dict(pred=pred, observed=obs, se_obs=np.sqrt(se_obs2), omega2=m["omega2"], se_fit=np.sqrt(se_fit2), df=df_, t=tq,
                       pi90=[pred - half_w, pred + half_w], D_OL=D_ol, lam_noOL=m["lam"], departure=obs - pred)
    ks = list(h5c)
    avg = {k: float(np.mean([h5c[s][k] for s in ks])) for k in ("pred", "observed", "se_obs", "omega2", "se_fit", "D_OL", "lam_noOL", "departure")}
    tq = h5c[ks[0]]["t"]; hw = tq * np.sqrt(avg["se_obs"] ** 2 + avg["omega2"] + avg["se_fit"] ** 2)
    avg["pi90"] = [avg["pred"] - hw, avg["pred"] + hw]
    avg["reading"] = ("informative departure (above)" if avg["observed"] > avg["pi90"][1] else
                      "below prediction interval" if avg["observed"] < avg["pi90"][0] else "inside prediction interval")
    avg["pi_width"] = 2 * hw
    h5c["averaged"] = avg
    glob["averaged"] = dict(lam=float(np.mean([glob[s]["lam"] for s in ks])), lam_se=float(np.mean([glob[s]["lam_se"] for s in ks])))

    result = dict(code_commit=git("rev-parse", "HEAD"), join_run=JOIN.name, primary_run=PRIMARY.name, seeds=SEEDS, B=B, alpha=ALPHA,
                  tests=tests, family=family, holm_sensitivity_primary_family=sens, h5a=h5a, h5c=h5c, h1_global=glob,
                  dl_b=dict(base_rho=dl_base["rho"], adjusted_rho=dl_adj["rho"], base_pooled=float(np.mean(dl_base["rho"])),
                            adjusted_pooled=float(np.mean(dl_adj["rho"])), boot_ok=int(ok.sum()), roles=dict(edge=info["edge"], interior=info["interior"]),
                            boot_quantiles_base_adj=np.percentile(dlb[ok][:, 4:6], [2.5, 50, 97.5], axis=0).tolist()),
                  wald=wald, demand=dict((f"{k[0]}|{k[1]}|{k[2]}", v) for k, v in D_half.items()), halves=halves, seconds=time.time() - t0)
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); out = OUTROOT / run; out.mkdir(parents=True)
    np.savez(out / "bootstraps.npz", DB=boots["DB"], DL=boots["DL"], OL=boots["OL"], DLb=dlb, H5b=h5b_draws)
    json.dump(result, open(out / "secondary_result.json", "w"), indent=1, default=float)
    (OUTROOT / "LATEST").write_text(run)
    print("->", out, round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
