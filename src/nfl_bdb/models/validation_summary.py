"""Monte Carlo summaries for Phase 4 (rates with binomial MC SE; bias / RMSE with MC SE; coverage)."""
from __future__ import annotations

import numpy as np
import polars as pl


def rate(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    p = x.mean() if len(x) else np.nan
    return p, (np.sqrt(p * (1 - p) / len(x)) if len(x) else np.nan)


def mean_se(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return (x.mean(), x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else (np.nan, np.nan)


def summarise_h1(df: pl.DataFrame, holm_alpha=0.05 / 3) -> pl.DataFrame:
    rows = []
    keys = [k for k in ("pos", "scenario", "label", "mech", "mechanism", "rule") if k in df.columns]
    for key, g in df.group_by(keys, maintain_order=True):
        ok = g.filter(pl.col("delta_reml").is_not_null()) if "delta_reml" in g.columns else g
        n_err = g.height - ok.height
        tr = ok["true_delta_obs"].to_numpy(); d = ok["delta_reml"].to_numpy(); dm_ = ok["delta_moment"].to_numpy()
        rej, rej_se = rate(ok["supported"].to_numpy())
        holm, holm_se = rate(((ok["p"] < holm_alpha) & (ok["delta_reml"] > 0)).to_numpy())
        raw, raw_se = rate(((ok["p_raw"] < 0.05) & (ok["delta_raw"] > 0)).to_numpy())
        cover, cover_se = rate(((ok["ci_lo"] <= tr) & (ok["ci_hi"] >= tr)).to_numpy())
        b, b_se = mean_se(d - tr); bm, bm_se = mean_se(dm_ - tr)
        row = dict(zip(keys, key), reps=ok.height, errors=n_err, converged=float(ok["converged"].mean()),
                   true_delta=float(ok["true_delta"][0]), true_delta_obs=float(tr[0]),
                   reject=rej, reject_mcse=rej_se, reject_holm=holm, reject_holm_mcse=holm_se,
                   reject_raw_contrast=raw, reject_raw_mcse=raw_se,
                   mean_delta_reml=float(np.mean(d)), bias_reml=b, bias_reml_mcse=b_se, rmse_reml=float(np.sqrt(np.mean((d - tr) ** 2))),
                   mean_delta_moment=float(np.mean(dm_)), bias_moment=bm, bias_moment_mcse=bm_se,
                   coverage95=cover, coverage_mcse=cover_se, mean_se_boot=float(ok["se_boot"].mean()),
                   sd_delta_reml=float(np.std(d, ddof=1)), disagree_rate=float(ok["disagree"].mean()),
                   n_players=float(ok["n_players"].mean()))
        if "delta_naive_unadj" in ok.columns:
            row["mean_delta_naive_unadj"] = float(ok["delta_naive_unadj"].mean())
            row["mean_delta_naive_raw"] = float(ok["delta_naive_raw"].mean())
        if "delta_2025" in ok.columns:
            v = ok.filter(pl.col("delta_2025").is_not_null() & pl.col("delta_2025").is_not_nan())
            row["sf_same_sign_given_supported"] = float((v.filter(pl.col("supported"))["delta_2025"] > 0).mean()) if v.filter(pl.col("supported")).height else np.nan
            row["supported_and_sf_sign"] = float((ok["supported"] & (ok["delta_2025"].fill_nan(None).fill_null(-1) > 0)).mean())
        rows.append(row)
    return pl.DataFrame(rows, infer_schema_length=None)


def summarise_h2(df: pl.DataFrame, holm_alpha=0.05 / 3) -> pl.DataFrame:
    rows = []
    for key, g in df.group_by(["scenario", "label"], maintain_order=True):
        ok = g.filter(pl.col("beta_P_reml").is_not_null())
        tp = float(ok["true_partial"][0])
        rej, rej_se = rate(ok["test_rejected"].to_numpy())
        holm, holm_se = rate(((ok["p"] < holm_alpha) & (ok["beta_P_reml"] > 0)).to_numpy())
        sup, sup_se = rate(ok["h2_supported_if_reached"].to_numpy())
        wald, wald_se = rate(((ok["beta_P_reml"] / ok["se_wald"]) > 1.96).to_numpy())
        b, b_se = mean_se(ok["partial_hat"].to_numpy() - tp)
        row = dict(scenario=key[0], label=key[1], reps=ok.height, errors=g.height - ok.height, true_partial=tp,
                   converged=float(ok["converged"].mean()),
                   reject=rej, reject_mcse=rej_se, reject_holm=holm, reject_holm_mcse=holm_se,
                   reject_wald_reml=wald, reject_wald_mcse=wald_se,
                   full_support=sup, full_support_mcse=sup_se,
                   mean_partial_hat=float(ok["partial_hat"].mean()), bias_partial=b, bias_partial_mcse=b_se,
                   sd_partial_hat=float(ok["partial_hat"].std()),
                   mean_beta_std=float(ok["beta_P_std"].mean()),
                   agree_sign_reml_2s=float(((ok["beta_P_reml"] > 0) == (ok["beta_P_2s"] > 0)).mean()),
                   mean_dr2_cv=float(ok["dr2_cv"].mean()), p_dr2_ge_002=float((ok["dr2_cv"] >= 0.02).mean()),
                   p_lb90_pos=float((ok["dr2_lb90"] > 0).mean()), p_predictive_ok=float(ok["predictive_ok"].mean()),
                   p_eiv_pos=float(ok["eiv_ok"].mean()), mean_dRMSE_sf=float(ok["dRMSE_sf"].mean()))
        if "dr2_playsplit" in ok.columns:
            lk = ok.filter(pl.col("dr2_playsplit").is_not_null())
            row["mean_dr2_playsplit"] = float(lk["dr2_playsplit"].mean())
            row["mean_dr2_player_cv_same_reps"] = float(lk["dr2_cv"].mean())
        rows.append(row)
    return pl.DataFrame(rows, infer_schema_length=None)
