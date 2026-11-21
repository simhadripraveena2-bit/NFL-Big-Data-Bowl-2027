"""Phase 4, item 7: why the DB man / underneath-zone true player correlation moved from -0.33 (Phase 3.5 power
calibration) to +0.36 (Phase 4 REML calibration). Outcome-only (game play max speed); no combine values used.
Writes experiments/synthetic_validation/<LATEST>/db_corr_decomposition.parquet"""
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from nfl_bdb.data.play_table import H1_COVARIATES, h1_frame, reg_play_table, residualise  # noqa: E402
from nfl_bdb.models import confirmatory as cf  # noqa: E402
from nfl_bdb.models.reml import fit_reml  # noqa: E402
from run_power_analysis import primary_opp_counts, tracked40_ids, variance_components  # noqa: E402


def team_idx(df):
    ts = df["team_abbr"] + "_" + df["season"].cast(pl.Utf8)
    return np.unique(ts.to_numpy(), return_inverse=True)[1]


def main():
    d0 = reg_play_table()
    ids = tracked40_ids().implode()
    rows = []
    for penalty_rule in ("phase3.5 (nullified plays kept)", "registered (nullified plays excluded)"):
        d = d0 if penalty_rule.startswith("phase3.5") else d0.filter(pl.col("play_nullified_by_penalty") != "Y")
        opp = primary_opp_counts(d)
        el = opp.filter((pl.col("pos") == "DB") & (pl.col("coverage") >= 100) & pl.col("nfl_id").is_in(ids))
        x = h1_frame(d, "DB").join(el.select("nfl_id"), on="nfl_id")
        covs = H1_COVARIATES["DB"]
        # A. Phase 3.5 method: pooled OLS residualisation over ALL three contexts, then moment covariance (man vs under)
        xa = x.with_columns(pl.Series("y_adj", residualise(x, "y", covs)))
        cnt = xa.group_by("nfl_id", "ctx").len().pivot(index="nfl_id", on="ctx", values="len").fill_null(0)
        keep = cnt.filter((pl.col("man") >= 20) & (pl.col("under_zone") >= 20))["nfl_id"]
        xa2 = xa.filter(pl.col("nfl_id").is_in(keep.implode()) & pl.col("ctx").is_in(["man", "under_zone"]))
        vc = variance_components(xa2, "y_adj", ["man", "under_zone"])
        rows.append(dict(data=penalty_rule, spec="A. pooled residualisation (3 contexts), moment", corr=vc["corr_between_true"], n=vc["n_players"]))
        # B. same but residualisation without lined_up_position
        xb = x.with_columns(pl.Series("y_adj", residualise(x, "y", [c for c in covs if c != "lined_up_position"])))
        xb2 = xb.filter(pl.col("nfl_id").is_in(keep.implode()) & pl.col("ctx").is_in(["man", "under_zone"]))
        vc = variance_components(xb2, "y_adj", ["man", "under_zone"])
        rows.append(dict(data=penalty_rule, spec="B. as A without lined_up_position", corr=vc["corr_between_true"], n=vc["n_players"]))
        # C. pooled residualisation on the two contrast contexts only
        x2 = x.filter(pl.col("nfl_id").is_in(keep.implode()) & pl.col("ctx").is_in(["man", "under_zone"]))
        xc = x2.with_columns(pl.Series("y_adj", residualise(x2, "y", covs)))
        vc = variance_components(xc, "y_adj", ["man", "under_zone"])
        rows.append(dict(data=penalty_rule, spec="C. pooled residualisation, 2 contexts, moment", corr=vc["corr_between_true"], n=vc["n_players"]))
        # D. context-specific residualisation (covariate effects differ by context), moment
        parts = [x2.filter(pl.col("ctx") == c) for c in ("man", "under_zone")]
        parts = [p.with_columns(pl.Series("y_adj", residualise(p, "y", [v for v in covs if v != "ctx"]))) for p in parts]
        vc = variance_components(pl.concat(parts), "y_adj", ["man", "under_zone"])
        rows.append(dict(data=penalty_rule, spec="D. context-specific residualisation, moment", corr=vc["corr_between_true"], n=vc["n_players"]))
        # E/F. registered REML (context-specific covariates), without / with team-season random effect
        x3 = x2.with_columns(pl.when(pl.col("ctx") == "man").then(0).otherwise(1).alias("ctx_i"))
        Xw = cf.design_h1(x3, covs, 2)
        pid = np.unique(x3["nfl_id"].to_numpy(), return_inverse=True)[1]
        for team, nm in ((None, "E. REML, context-specific covariates, no team-season"), (team_idx(x3), "F. REML + team-season random effect (registered)")):
            f = fit_reml(x3["y"].to_numpy(), Xw, pid, x3["ctx_i"].to_numpy(), team, 2)
            rows.append(dict(data=penalty_rule, spec=nm, corr=float(f.sigma_b[0, 1] / np.sqrt(f.sigma_b[0, 0] * f.sigma_b[1, 1])), n=int(pid.max() + 1)))
        # G. pooled covariates in REML (common covariate effects) + team
        W = cf.full_rank(cf.one_hot(x3, [v for v in covs if v != "ctx"]))
        X = np.column_stack([(x3["ctx_i"] == 0).to_numpy(), (x3["ctx_i"] == 1).to_numpy(), W]).astype(float)
        f = fit_reml(x3["y"].to_numpy(), cf.full_rank(X), pid, x3["ctx_i"].to_numpy(), team_idx(x3), 2)
        rows.append(dict(data=penalty_rule, spec="G. REML with COMMON covariate effects + team-season", corr=float(f.sigma_b[0, 1] / np.sqrt(f.sigma_b[0, 0] * f.sigma_b[1, 1])), n=int(pid.max() + 1)))
    df = pl.DataFrame(rows)
    run = (ROOT / "experiments/synthetic_validation/LATEST").read_text().strip()
    df.write_parquet(ROOT / "experiments/synthetic_validation" / run / "db_corr_decomposition.parquet")
    pl.Config.set_tbl_width_chars(200); pl.Config.set_fmt_str_lengths(80)
    print(df)


if __name__ == "__main__":
    main()
