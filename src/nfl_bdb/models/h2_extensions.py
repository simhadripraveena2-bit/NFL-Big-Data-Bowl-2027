"""H2 (secondary, estimation-focused after D4): registered pieces not contained in the frozen `confirmatory` module.

Frozen pieces re-used unchanged: confirmatory.h2_reml, wls_two_stage, h2_bootstrap, eiv_two_stage, player_sufficient,
h2_cv, h2_cv_bootstrap, _resid_means.  Added here (all registered in statistical_model_specification.md §2):
  * design / indexing identical to the Phase 4 H2 skeleton (one-hot H2 covariates incl. season + linear NFL year);
  * Delta R^2 of the TRUE between-player deep-separation level (spec §2.1 reported scale);
  * player-cluster bootstrap of the REML fit (B = 2000, percentile; duplicates distinct, team-season shared),
    jointly for deep and short routes (negative control N3: beta_P^deep - beta_P^short, spec §2.4);
  * extended player-grouped CV (spec §2.2): M0, M1 (F), M2 (F + x), M2s (F + spline(x), 3 df), M3 (F + 10-yd split);
    metrics R^2, RMSE, Spearman, mean log predictive density; folds stratified by draft class (protocol §13);
    leave-one-player-out (closed-form-equivalent PRESS) as a check;
  * season-forward (fit 2023-24, predict 2025 levels) exactly as in the Phase 4 runner;
  * errors-in-variables grid and the tipping-point R_F (D3 reporting).
"""
from __future__ import annotations

import numpy as np
import polars as pl
from scipy import optimize, stats

from nfl_bdb.data.play_table import H2_COVARIATES
from nfl_bdb.models import confirmatory as cf
from nfl_bdb.models.h1_extensions import ns_basis


def design(df: pl.DataFrame) -> np.ndarray:
    W = cf.one_hot(df, [c for c in H2_COVARIATES if c in df.columns])
    return cf.full_rank(np.column_stack([W, df["nfl_year"].to_numpy().astype(float)]))


def index(df: pl.DataFrame, ids: list[int]):
    """Player index over a FIXED id list (so deep and short share player numbering); team-season index."""
    pm = {k: i for i, k in enumerate(ids)}
    df = df.with_columns((pl.col("team_abbr") + "_" + pl.col("season").cast(pl.Utf8)).alias("team_season"))
    ts = sorted(df["team_season"].unique().to_list()); tm = {k: i for i, k in enumerate(ts)}
    df = df.with_columns(pl.col("nfl_id").replace_strict(pm).alias("pid"), pl.col("team_season").replace_strict(tm).alias("team_i"))
    return df.sort("pid", "game_id", "play_id")


def true_scale(bF, bP, r, s2b):
    """Standardised F, x (unit variance, correlation r). Returns beta_P*, partial r_{P.F}, Delta R^2 of the true level."""
    tot = bF ** 2 + bP ** 2 + 2 * bF * bP * r + s2b
    r2_full = (bF ** 2 + bP ** 2 + 2 * bF * bP * r) / tot
    r2_F = (bF + bP * r) ** 2 / tot
    partial = bP * np.sqrt(1 - r ** 2) / np.sqrt(bP ** 2 * (1 - r ** 2) + s2b)
    return dict(beta_P_std=float(bP / np.sqrt(tot)), partial=float(partial), dR2_true=float(r2_full - r2_F),
                R2_true_F=float(r2_F), R2_true_full=float(r2_full))


def fit(pid, team, y, W, F, x):
    r = cf.h2_reml(pid, team, y, W, F, x)
    rr = float(np.corrcoef(cf.standardise(F), cf.standardise(x))[0, 1])
    r.update(true_scale(r["beta_F"], r["beta_P"], rr, r["s2b"]))
    r["r_F_x"] = rr
    return r


def _rows(pid, P):
    order = np.argsort(pid, kind="stable"); bnd = np.searchsorted(pid[order], np.arange(P + 1))
    return [order[bnd[i]:bnd[i + 1]] for i in range(P)]


def reml_bootstrap(deep: dict, short: dict, F, x, B, seed):
    """Joint player-cluster bootstrap of the REML H2 fit on deep and short routes (same resampled players)."""
    rng = np.random.default_rng(seed); P = len(F)
    rd, rs = _rows(deep["pid"], P), _rows(short["pid"], P)
    keys = ["beta_P", "beta_F", "beta_P_std", "partial", "dR2_true"]
    out = {f"{s}_{k}": np.full(B, np.nan) for s in ("deep", "short") for k in keys}
    for b in range(B):
        pick = rng.integers(0, P, P)
        for name, arr, rows in (("deep", deep, rd), ("short", short, rs)):
            idx = np.concatenate([rows[i] for i in pick])
            newp = np.concatenate([np.full(len(rows[i]), k) for k, i in enumerate(pick)])
            _, tn = np.unique(arr["team"][idx], return_inverse=True)
            Wb = arr["W"][idx]; Wb = cf.full_rank(Wb[:, np.abs(Wb).sum(0) > 0])
            try:
                r = fit(newp, tn, arr["y"][idx], Wb, F[pick], x[pick])
                for k in keys:
                    out[f"{name}_{k}"][b] = r[k]
            except Exception:  # noqa: BLE001
                pass
    return out


# ------------------------------------------------------------------------------------------------ CV (spec §2.2)
def stratified_folds(draft_class, folds, rng):
    fid = np.empty(len(draft_class), int)
    for c in np.unique(draft_class):
        m = np.where(draft_class == c)[0]; perm = rng.permutation(m)
        fid[perm] = (np.arange(len(m)) + rng.integers(0, folds)) % folds
    return fid


def _feats(F, x, ten, knots_raw, tr):
    z = lambda v: (v - v[tr].mean()) / v[tr].std(ddof=1)  # noqa: E731
    Fs, xs, ts = z(F), z(x), z(ten)
    kn = (np.asarray(knots_raw) - x[tr].mean()) / x[tr].std(ddof=1)
    kn = np.concatenate([[min(kn[0], xs.min())], kn[1:-1], [max(kn[-1], xs.max())]])
    one = np.ones(len(F))
    return {"M0": one[:, None], "M1": np.column_stack([one, Fs]), "M2": np.column_stack([one, Fs, xs]),
            "M2s": np.column_stack([one, Fs, ns_basis(xs, kn)]), "M3": np.column_stack([one, Fs, ts])}


def cv_extended(S: cf.PlayerSuff, F, x, ten, draft_class, knots_raw, rng, folds=10, repeats=20, stratify=True):
    """Held-out PLAYERS: each player's covariate-adjusted deep separation level (residualised on training folds,
    shrunk with training-fold variance), predicted from combine measures fitted on training players."""
    P = len(F); models = ["M0", "M1", "M2", "M2s", "M3"]; per = []
    for _ in range(repeats):
        fid = stratified_folds(draft_class, folds, rng) if stratify else cf.player_folds(P, folds, rng)
        pred = {m: np.empty(P) for m in models}; sig2 = {m: np.empty(P) for m in models}
        target = np.empty(P); mu_tr = np.empty(P)
        for f in np.unique(fid):
            te = np.where(fid == f)[0]; tr = np.where(fid != f)[0]
            m_tr, m_te, sw2 = cf._resid_means(S, tr, te)
            s2b = max(np.var(m_tr, ddof=1) - np.mean(sw2 / S.n[tr]), 1e-6)
            k_tr = s2b / (s2b + sw2 / S.n[tr]); k_te = s2b / (s2b + sw2 / S.n[te])
            mu = np.average(m_tr, weights=k_tr)
            t_tr = mu + k_tr * (m_tr - mu); t_te = mu + k_te * (m_te - mu)
            X = _feats(F, x, ten, knots_raw, tr)
            for m in models:
                coef, *_ = np.linalg.lstsq(X[m][tr], t_tr, rcond=None)
                res = t_tr - X[m][tr] @ coef
                pred[m][te] = X[m][te] @ coef
                sig2[m][te] = max(res @ res / max(len(tr) - X[m].shape[1], 1), 1e-8)
            target[te] = t_te; mu_tr[te] = mu
        sst = ((target - mu_tr) ** 2).sum(); row = {}
        for m in models:
            e = target - pred[m]
            row[f"R2_{m}"] = 1 - (e ** 2).sum() / sst
            row[f"RMSE_{m}"] = float(np.sqrt(np.mean(e ** 2)))
            row[f"spearman_{m}"] = float(stats.spearmanr(pred[m], target).statistic) if m != "M0" else np.nan
            row[f"lpd_{m}"] = float(np.mean(stats.norm.logpdf(target, pred[m], np.sqrt(sig2[m]))))
        per.append(row)
    df = pl.DataFrame(per)
    summary = {c: float(df[c].mean()) for c in df.columns}
    summary["dR2_CV"] = summary["R2_M2"] - summary["R2_M1"]
    summary["dRMSE_CV"] = summary["RMSE_M2"] - summary["RMSE_M1"]
    summary["dSpearman_CV"] = summary["spearman_M2"] - summary["spearman_M1"]
    summary["dLPD_CV"] = summary["lpd_M2"] - summary["lpd_M1"]
    summary["dR2_CV_spline"] = summary["R2_M2s"] - summary["R2_M1"]
    summary["dR2_CV_M3_reference"] = summary["R2_M3"] - summary["R2_M1"]
    summary["repeat_dR2_sd"] = float((df["R2_M2"] - df["R2_M1"]).std()) if repeats > 1 else np.nan
    return summary


def lopo(S, F, x, ten, draft_class, knots_raw):
    """Leave-one-player-out (folds = P): the PRESS-type check."""
    return cv_extended(S, F, x, ten, np.zeros(len(F), int), knots_raw, np.random.default_rng(0), folds=len(F), repeats=1, stratify=False)


# ------------------------------------------------------------------------------------------------ season-forward
def season_forward(pid, W, y, season, F, x):
    """Identical to the validated Phase 4 rule: fit on 2023-24, predict 2025 shrunken levels (>= 20 deep plays in both)."""
    P = len(F); tr, te = season < 2025, season == 2025
    nte = np.bincount(pid[te], minlength=P); ntr = np.bincount(pid[tr], minlength=P)
    ok = np.where((nte >= 20) & (ntr >= 20))[0]
    if len(ok) < 15:
        return dict(n=len(ok), dRMSE=np.nan)
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
    r1, r2 = float(np.sqrt(np.mean((target - p1) ** 2))), float(np.sqrt(np.mean((target - p2) ** 2)))
    return dict(n=len(ok), n_train_players=len(okt), RMSE_M1=r1, RMSE_M2=r2, dRMSE=r2 - r1,
                spearman_M1=float(stats.spearmanr(p1, target).statistic), spearman_M2=float(stats.spearmanr(p2, target).statistic))


# ------------------------------------------------------------------------------------------------ measurement error
def eiv_grid(m, n, sw2, F, x, rel_F_grid=(0.85, 0.90, 0.95, 0.99), rel_x_grid=(0.94, 0.987)):
    rows = []
    for rx in rel_x_grid:
        for rf in rel_F_grid:
            b = cf.eiv_two_stage(m, n, sw2, F, x, rel_F=rf, rel_x=rx)
            rows.append(dict(rel_F=rf, rel_x=rx, eiv_beta_F=float(b[0]), eiv_beta_P=float(b[1])))
    return rows


def tipping_point(m, n, sw2, F, x, rel_x, lo=0.5, hi=0.9999):
    """R_F at which the EIV beta_P crosses 0 (None if no sign change on [lo, hi])."""
    f = lambda rf: cf.eiv_two_stage(m, n, sw2, F, x, rel_F=rf, rel_x=rel_x)[1]  # noqa: E731
    try:
        fl, fh = f(lo), f(hi)
        if np.sign(fl) == np.sign(fh):
            return None
        return float(optimize.brentq(f, lo, hi))
    except Exception:  # noqa: BLE001
        return None


def precision_artefact(r_obs, rel_F, rel_x, a):
    """Population partial correlation of the true level with OBSERVED x given OBSERVED F, when the level depends on
    true 40 speed only (validity a). Same algebra as the Phase 4 calculation."""
    r = min(r_obs / np.sqrt(rel_F * rel_x), 0.999)
    C = np.array([[1, np.sqrt(rel_F * rel_x) * r, np.sqrt(rel_F) * a], [np.sqrt(rel_F * rel_x) * r, 1, np.sqrt(rel_x) * r * a],
                  [np.sqrt(rel_F) * a, np.sqrt(rel_x) * r * a, 1]])
    Pm = np.linalg.inv(C)
    return float(-Pm[1, 2] / np.sqrt(Pm[1, 1] * Pm[2, 2]))
