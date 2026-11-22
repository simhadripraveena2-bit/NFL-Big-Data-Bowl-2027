"""H1-DL(b) interpretation audit: DESCRIPTIVE diagnostics only (no hypothesis test, Holm family untouched).

Uses the registered DL frame and estimator (confirmatory.design_h1 + REML), the registered adjusted design
(run_secondary.dl_adjusted_design), and the delta-method Wald SEs of secondary.rho_wald. Computes:
  * correlation structure of combine peak speed, combine weight and EDGE role (53 eligible DL; all DL participants);
  * collinearity: R^2 / VIF of peak speed on role and weight; SD of peak speed conditional on them;
  * four conditioning variants of the pooled rho: none (registered), + role x ctx, + weight x ctx, + both (registered
    adjusted), each with per-context rho, Wald SEs, the standardised slope and a partial-correlation version that uses
    the conditional SD of x (descriptive);
  * alternative pooling weights for the registered quantity (equal, play-weighted, per context);
  * within-role consistency (EDGE-only, interior-only fits; within-role speed-weight correlation).
Output: experiments/secondary/<LATEST>/dl_role_weight_diagnostics.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
import run_secondary as RS  # noqa: E402
from nfl_bdb.data.play_table import H1_COVARIATES  # noqa: E402
from nfl_bdb.models import confirmatory as cf  # noqa: E402
from nfl_bdb.models import secondary as sc  # noqa: E402

OUT = ROOT / "experiments/secondary" / (ROOT / "experiments/secondary/LATEST").read_text().strip()


def player_table(dfi):
    cr = pl.read_parquet(ROOT / "data/interim/combine_results.parquet").filter(pl.col("combine_position") == "DL")
    wz = cr.with_columns(((pl.col("combine_weight") - pl.col("combine_weight").mean()) / pl.col("combine_weight").std()).alias("wz")).select("nfl_id", "combine_weight", "wz")
    role = (dfi.group_by("pid", "lined_up_position").len().sort(["pid", "len"], descending=[False, True]).group_by("pid", maintain_order=True)
            .agg(pl.col("lined_up_position").first().alias("modal")))
    return (dfi.group_by("pid").agg(pl.col("nfl_id").first(), pl.col("x_peak").first()).sort("pid")
            .join(role, on="pid").join(wz, on="nfl_id", how="left").sort("pid").with_columns((pl.col("modal") == "EDGE").cast(pl.Float64).alias("edge")))


def corr_table(t):
    M = np.column_stack([t["x_peak"].to_numpy(), t["combine_weight"].to_numpy(), t["edge"].to_numpy()])
    return np.corrcoef(M.T).tolist()


def fit_variant(dfi, Xw, cols, label):
    player, ctx, team, y, xp = sc.arrays(dfi)
    X = cf.full_rank(np.column_stack([Xw] + ([sc.player_ctx_columns(cols, player, ctx, 2)] if cols is not None else [])))
    w = sc.rho_wald(player, ctx, team, y, X, xp, 2)
    xs = (xp - xp.mean()) / xp.std(ddof=1)
    if cols is not None:
        Z = np.column_stack([np.ones(len(xs)), cols]); res = xs - Z @ np.linalg.lstsq(Z, xs, rcond=None)[0]
        sd_cond = float(res.std(ddof=Z.shape[1]))
    else:
        sd_cond = 1.0
    Sb = np.asarray(w["sigma_b"]); bx = np.asarray(w["beta_x"])
    partial = bx * sd_cond / np.sqrt(bx ** 2 * sd_cond ** 2 + np.diag(Sb))   # rho using the conditional SD of x (descriptive)
    cov = np.asarray(w["cov"])
    return dict(label=label, rho=w["rho"].tolist(), se=w["se"].tolist(), pooled=float(np.mean(w["rho"])),
                pooled_se=float(np.sqrt(np.ones(2) @ cov @ np.ones(2)) / 2), beta_x_std=bx.tolist(), sigma_b_diag=np.diag(Sb).tolist(),
                sd_x_conditional=sd_cond, rho_using_conditional_sd=partial.tolist(), pooled_conditional_sd=float(partial.mean()),
                converged=w["converged"], hessian_min_eig=w["hessian_min_eig"])


def main():
    dfi, _ = sc.index_frame(RS.frame("DL"), RS.CTX["DL"])
    Xw = cf.design_h1(dfi, H1_COVARIATES["DL"], 2)
    t = player_table(dfi)
    edge = t["edge"].to_numpy(); wz = t["wz"].to_numpy()
    out = {}
    # correlation structure (eligible 53) and all DL combine participants with a valid tracked 40 (combine data only)
    out["corr_eligible"] = dict(vars=["x_peak", "combine_weight", "edge"], matrix=corr_table(t), n=t.height)
    pred = pl.read_parquet(RS.JOIN / "predictors.parquet").filter((pl.col("pos") == "DL") & pl.col("x_peak").is_not_null())
    cr = pl.read_parquet(ROOT / "data/interim/combine_results.parquet").select("nfl_id", "combine_weight")
    allp = pred.join(cr, on="nfl_id")
    out["corr_all_DL_participants_speed_weight"] = dict(r=float(np.corrcoef(allp["x_peak"], allp["combine_weight"])[0, 1]), n=allp.height)
    out["role_means"] = t.group_by("modal").agg(pl.len().alias("n"), pl.col("x_peak").mean(), pl.col("x_peak").std().alias("x_sd"),
                                               pl.col("combine_weight").mean(), pl.col("combine_weight").std().alias("w_sd")).sort("modal").to_dicts()
    xs = (t["x_peak"].to_numpy() - t["x_peak"].mean()) / t["x_peak"].std()
    for lab, Z in (("role", edge[:, None]), ("weight", wz[:, None]), ("role+weight", np.column_stack([edge, wz]))):
        Zc = np.column_stack([np.ones(len(xs)), Z]); r2 = 1 - np.sum((xs - Zc @ np.linalg.lstsq(Zc, xs, rcond=None)[0]) ** 2) / np.sum((xs - xs.mean()) ** 2)
        out.setdefault("collinearity", {})[lab] = dict(R2_x_on=float(r2), VIF=float(1 / (1 - r2)), sd_x_conditional=float(np.sqrt(1 - r2)))
    # within-role speed-weight correlation
    out["within_role_speed_weight_r"] = {r: float(np.corrcoef(t.filter(pl.col("modal") == r)["x_peak"], t.filter(pl.col("modal") == r)["combine_weight"])[0, 1])
                                         for r in ("EDGE", "INTERIOR_LINE")}
    # four conditioning variants (registered base and registered adjusted are reproduced)
    out["variants"] = [fit_variant(dfi, Xw, None, "unadjusted (registered model)"),
                       fit_variant(dfi, Xw, edge[:, None], "+ role x context"),
                       fit_variant(dfi, Xw, wz[:, None], "+ weight x context"),
                       fit_variant(dfi, Xw, np.column_stack([edge, wz]), "+ role and weight x context (registered adjusted)")]
    # operational-choice check: weight as a MAIN effect (not x context), role x context (descriptive)
    player, ctx = dfi["pid"].to_numpy(), dfi["ctx_i"].to_numpy()
    Xm = cf.full_rank(np.column_stack([Xw, wz[player]]))
    out["variant_weight_main_effect"] = fit_variant(dfi, Xm, edge[:, None], "+ role x context + weight (main effect)")
    # pooling definitions for the registered quantity (point estimates)
    base, adj = out["variants"][0], out["variants"][3]
    n_pr, n_run = int((dfi["ctx_i"] == 0).sum()), int((dfi["ctx_i"] == 1).sum())
    wpl = n_pr / (n_pr + n_run)
    out["pooling_definitions"] = dict(
        equal_mean=base["pooled"] - adj["pooled"],
        play_weighted=(wpl * base["rho"][0] + (1 - wpl) * base["rho"][1]) - (wpl * adj["rho"][0] + (1 - wpl) * adj["rho"][1]),
        pass_rush_only=base["rho"][0] - adj["rho"][0], run_only=base["rho"][1] - adj["rho"][1], play_weight_pass_rush=wpl)
    reg = json.load(open(OUT / "secondary_result.json"))["dl_b"]
    out["reproduces_registered"] = dict(base=abs(base["pooled"] - reg["base_pooled"]) < 1e-6, adjusted=abs(adj["pooled"] - reg["adjusted_pooled"]) < 1e-6)
    # within-role consistency (same exploratory fits as the secondary run; reproduced here)
    for role in ("EDGE", "INTERIOR_LINE"):
        ids = t.filter(pl.col("modal") == role)["nfl_id"].to_list()
        sub, _ = sc.index_frame(RS.frame("DL").filter(pl.col("nfl_id").is_in(ids)), RS.CTX["DL"])
        out.setdefault("within_role", {})[role] = fit_variant(sub, cf.design_h1(sub, H1_COVARIATES["DL"], 2), None, f"{role} only")
    json.dump(out, open(OUT / "dl_role_weight_diagnostics.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
