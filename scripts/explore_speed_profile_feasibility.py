"""EXPLORATORY feasibility audit: "Combine-to-Game Speed Profile" (not registered, not part of the submission).

Purpose: decide whether R_ij = game_speed_ij / combine_peak_i can support a defensible player tool.
Descriptive only: no predictive model is fitted, no Combine-predictor x game-outcome association is estimated or
reported (Combine peak speed enters only as the denominator of the candidate metric), no registered file is used
for decisions. Outputs (aggregates only) go to experiments/speed_profile_feasibility/<run>/ (git-ignored).

Usage: python scripts/explore_speed_profile_feasibility.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
INT = ROOT / "data" / "interim"
JOIN = INT / "confirmatory_join" / "20261121T135032Z"
DEEP = ["GO", "POST", "CORNER", "WHEEL"]
SHORT = ["HITCH", "SLANT", "OUT", "FLAT", "SCREEN", "ANGLE"]
QS = (0.80, 0.85, 0.90)
MIN_ROUTES = 100
RNG = np.random.default_rng(2027)
FAULTY = (2025101205, (1289, 1314))


# ---------------------------------------------------------------------------------------------- data
def wr_routes():
    cr = pl.read_parquet(INT / "combine_results.parquet").filter(pl.col("combine_position") == "WR").select("nfl_id", "draft_year")
    pred = pl.read_parquet(JOIN / "predictors.parquet", columns=["nfl_id", "pos", "x_peak", "n_valid_attempts"]).filter(pl.col("pos") == "WR")
    g = pl.read_parquet(INT / "games.parquet").select("game_id", "season", "season_type", "week")
    pp = pl.read_parquet(INT / "player_play.parquet", columns=["game_id", "play_id", "nfl_id", "route_ran", "pass_result", "target",
                                                               "receiver_alignment", "offense_formation", "in_motion_at_ball_snap"])
    pp = pp.join(g, on="game_id").filter((pl.col("season_type") == "REG") & pl.col("route_ran").is_not_null()).join(cr, on="nfl_id")
    pp = pp.filter(~((pl.col("game_id") == FAULTY[0]) & pl.col("play_id").is_in(list(FAULTY[1]))))
    f = pl.read_parquet(INT / "phase3_play_features.parquet", columns=["game_id", "play_id", "nfl_id", "k_pf", "vmax_prepass", "vmax_play", "s_pf"])
    d = pp.join(f, on=["game_id", "play_id", "nfl_id"], how="left").join(pred.select("nfl_id", "x_peak", "n_valid_attempts"), on="nfl_id", how="left")
    d = d.with_columns(
        pl.when(pl.col("route_ran").is_in(DEEP)).then(pl.lit("deep")).when(pl.col("route_ran").is_in(SHORT)).then(pl.lit("short"))
        .otherwise(pl.lit("in_cross")).alias("ctx"),
        pl.when(pl.col("vmax_prepass") <= 12.5).then(pl.col("vmax_prepass")).alias("v"),
        pl.when(pl.col("vmax_play") <= 12.5).then(pl.col("vmax_play")).alias("v_play"))
    return d.with_columns((pl.col("v") / pl.col("x_peak")).alias("R"), (pl.col("v_play") / pl.col("x_peak")).alias("R_play"))


# ---------------------------------------------------------------------------------------------- measurement checks
def s_vs_displacement():
    """Provider speed s vs 10 x frame displacement at high speed, combine 40 (WR) vs game WR routes (pre-throw)."""
    wr = pl.read_parquet(INT / "combine_results.parquet").filter(pl.col("combine_position") == "WR")["nfl_id"].implode()
    ct = (pl.scan_parquet(INT / "combine_tracking.parquet")
          .filter((pl.col("entity_type") == "PLAYER") & (pl.col("drill_type") == "FORTY_YARD_DASH") & pl.col("nfl_id").is_in(wr))
          .select("event_id", "nfl_id", "time", "x", "y", "s").collect().sort("event_id", "time"))
    ct = ct.with_columns(((pl.col("x").diff() ** 2 + pl.col("y").diff() ** 2).sqrt() * 10).over("event_id").alias("v_xy"))
    out = {}
    hi = ct.filter((pl.col("s") >= 8) & pl.col("v_xy").is_not_null())
    out["combine_40_WR"] = dict(frames=hi.height, median_s_over_vxy=float((hi["s"] / hi["v_xy"]).median()),
                                frames_per_attempt_within_5pct_of_peak=float(ct.with_columns((pl.col("s") >= 0.95 * pl.col("s").max().over("event_id")).alias("near"))
                                                                              .group_by("event_id").agg(pl.col("near").sum())["near"].median()))
    ids = ct["nfl_id"].unique().implode()
    rat, near = [], []
    for yr in (2023, 2024, 2025):
        gt = (pl.scan_parquet(INT / f"game_tracking_{yr}.parquet").filter(pl.col("nfl_id").is_in(ids))
              .select("game_id", "play_id", "nfl_id", "time", "x", "y", "s").collect().sort("game_id", "play_id", "nfl_id", "time"))
        gt = gt.with_columns(((pl.col("x").diff() ** 2 + pl.col("y").diff() ** 2).sqrt() * 10).over("game_id", "play_id", "nfl_id").alias("v_xy"))
        h = gt.filter((pl.col("s") >= 8) & (pl.col("s") <= 12.5) & pl.col("v_xy").is_not_null() & (pl.col("v_xy") > 0))
        rat.append((h["s"] / h["v_xy"]).to_numpy())
    r = np.concatenate(rat)
    out["game_WR_all_frames"] = dict(frames=int(len(r)), median_s_over_vxy=float(np.median(r)))
    return out


# ---------------------------------------------------------------------------------------------- player metrics
def metrics(df: pl.DataFrame, rcol="R", vcol="v", xconst=None):
    """Per-player metrics on a set of routes. xconst: replace the player's own denominator by a constant (control)."""
    d = df.filter(pl.col(rcol).is_not_null())
    if xconst is not None:
        d = d.with_columns((pl.col(vcol) / xconst).alias(rcol))
    agg = [pl.len().alias("n")]
    agg += [(pl.col(rcol) >= q).mean().alias(f"A{int(q*100)}") for q in QS]
    agg += [(pl.col(rcol) >= q).sum().alias(f"k{int(q*100)}") for q in QS]
    agg += [pl.col(rcol).quantile(0.9).alias("R_p90"), pl.col(rcol).sort(descending=True).head(5).mean().alias("R_top5"),
            pl.col(vcol).quantile(0.9).alias("V_p90"), pl.col(vcol).sort(descending=True).head(5).mean().alias("V_top5")]
    return d.group_by("nfl_id").agg(agg)


def own_top_share(df, vcol="v"):
    """Game-only control: share of routes >= q x the player's own top-5 mean game speed (within the same subset)."""
    d = df.filter(pl.col(vcol).is_not_null())
    top = d.group_by("nfl_id").agg(pl.col(vcol).sort(descending=True).head(5).mean().alias("top5"))
    d = d.join(top, on="nfl_id")
    return d.group_by("nfl_id").agg([(pl.col(vcol) >= q * pl.col("top5")).mean().alias(f"O{int(q*100)}") for q in QS])


def split(df, how):
    """Assign each route to half 0/1 by the player's chronological game order."""
    gorder = (df.select("nfl_id", "season", "week", "game_id").unique().sort("nfl_id", "season", "week", "game_id")
              .with_columns(pl.int_range(pl.len()).over("nfl_id").alias("gi"), pl.len().over("nfl_id").alias("ng")))
    if how == "odd_even":
        gorder = gorder.with_columns((pl.col("gi") % 2).alias("half"))
    else:  # first vs second half of the player's games
        gorder = gorder.with_columns((pl.col("gi") >= pl.col("ng") / 2).cast(pl.Int32).alias("half"))
    return df.join(gorder.select("nfl_id", "game_id", "half"), on=["nfl_id", "game_id"])


def sb(r):
    return 2 * r / (1 + r) if np.isfinite(r) and r > -1 else np.nan


def half_corr(m0, m1, cols, players):
    j = m0.join(m1, on="nfl_id", suffix="_1").filter(pl.col("nfl_id").is_in(players.implode()))
    out = {}
    for c in cols:
        a, b = j[c].to_numpy().astype(float), j[c + "_1"].to_numpy().astype(float)
        ok = np.isfinite(a) & np.isfinite(b)
        a, b = a[ok], b[ok]
        r = float(np.corrcoef(a, b)[0, 1]) if len(a) > 5 and a.std() > 0 and b.std() > 0 else np.nan
        bs = []
        for _ in range(500):
            i = RNG.integers(0, len(a), len(a))
            if a[i].std() > 0 and b[i].std() > 0:
                bs.append(np.corrcoef(a[i], b[i])[0, 1])
        lo, hi = np.percentile(bs, [2.5, 97.5]) if bs else (np.nan, np.nan)
        out[c] = dict(n_players=int(len(a)), r_half=r, rel_SB=sb(r), rel_SB_lo=sb(lo), rel_SB_hi=sb(hi))
    return out


def matched_half_corr(df, cols, players, n_match=None, reps=30, fn=metrics):
    """Subsample routes so both halves of a player have the same count (min of halves, or a fixed n_match)."""
    rs = {c: [] for c in cols}
    d = df.filter(pl.col("nfl_id").is_in(players.implode()))
    cnt = d.group_by("nfl_id", "half").len().pivot(index="nfl_id", on="half", values="len").fill_null(0)
    cnt = cnt.with_columns(pl.min_horizontal("0", "1").alias("m"))
    if n_match:
        cnt = cnt.filter(pl.col("m") >= n_match).with_columns(pl.lit(n_match).alias("m"))
    keep = cnt.select("nfl_id", "m")
    dd = d.join(keep, on="nfl_id")
    for _ in range(reps):
        sub = (dd.with_columns(pl.lit(RNG.random(dd.height)).alias("u"))
               .with_columns(pl.col("u").rank("ordinal").over("nfl_id", "half").alias("rk"))
               .filter(pl.col("rk") <= pl.col("m")))
        m0, m1 = fn(sub.filter(pl.col("half") == 0)), fn(sub.filter(pl.col("half") == 1))
        res = half_corr(m0, m1, cols, keep["nfl_id"])
        for c in cols:
            rs[c].append(res[c]["r_half"])
    return dict(n_players=keep.height, routes_per_half_median=float(keep["m"].median()) if keep.height else np.nan,
                **{c: dict(r_half_mean=float(np.nanmean(v)), rel_SB=sb(float(np.nanmean(v)))) for c, v in rs.items()})


def game_cluster_ci(df, players, col="A85", B=400):
    """Per-player 95% CI of a share metric by bootstrapping that player's games; pairwise separability."""
    d = df.filter(pl.col("nfl_id").is_in(players.implode()) & pl.col("R").is_not_null())
    q = int(col[1:]) / 100
    per = d.group_by("nfl_id", "game_id").agg(pl.len().alias("n"), (pl.col("R") >= q).sum().alias("k"))
    ests, cis = {}, {}
    for (nid,), g in per.group_by("nfl_id"):
        n, k = g["n"].to_numpy(), g["k"].to_numpy()
        ests[nid] = k.sum() / n.sum()
        idx = RNG.integers(0, len(n), (B, len(n)))
        bs = k[idx].sum(1) / n[idx].sum(1)
        cis[nid] = np.percentile(bs, [2.5, 97.5])
    ids = list(ests)
    lo = np.array([cis[i][0] for i in ids]); hi = np.array([cis[i][1] for i in ids]); est = np.array([ests[i] for i in ids])
    sep = sum((hi[a] < lo[b]) or (hi[b] < lo[a]) for a in range(len(ids)) for b in range(a + 1, len(ids)))
    pairs = len(ids) * (len(ids) - 1) // 2
    # rank uncertainty: bootstrap ranks jointly
    return dict(metric=col, n_players=len(ids), median_estimate=float(np.median(est)), median_ci_width=float(np.median(hi - lo)),
                share_pairs_separable=float(sep / pairs), between_player_sd=float(est.std(ddof=1)))


def rank_interval(df, players, col="A85", B=300):
    d = df.filter(pl.col("nfl_id").is_in(players.implode()) & pl.col("R").is_not_null())
    q = int(col[1:]) / 100
    per = d.group_by("nfl_id", "game_id").agg(pl.len().alias("n"), (pl.col("R") >= q).sum().alias("k")).sort("nfl_id")
    groups = [(g["n"].to_numpy(), g["k"].to_numpy()) for _, g in per.group_by("nfl_id", maintain_order=True)]
    P = len(groups); ranks = np.empty((B, P))
    for b in range(B):
        v = []
        for n, k in groups:
            i = RNG.integers(0, len(n), len(n)); v.append(k[i].sum() / n[i].sum())
        ranks[b] = np.argsort(np.argsort(-np.array(v))) + 1
    w = np.percentile(ranks, 97.5, axis=0) - np.percentile(ranks, 2.5, axis=0)
    return dict(n_players=P, median_rank_95_width=float(np.median(w)), share_width_gt_half_of_players=float(np.mean(w > P / 2)))


def top_play_dominance(df, players):
    d = df.filter(pl.col("nfl_id").is_in(players.implode()) & pl.col("R").is_not_null())
    out = {}
    for q in QS:
        k = d.group_by("nfl_id").agg((pl.col("R") >= q).sum().alias("k"), pl.len().alias("n"))
        out[f"exceedances_q{int(q*100)}"] = dict(median=float(k["k"].median()), p10=float(k["k"].quantile(0.1)), p90=float(k["k"].quantile(0.9)),
                                                 share_players_le3=float((k["k"] <= 3).mean()), share_players_0=float((k["k"] == 0).mean()))
    # p90 / top5 after dropping each player's 3 fastest routes
    base = metrics(d)
    drop = d.with_columns(pl.col("R").rank("ordinal", descending=True).over("nfl_id").alias("rk")).filter(pl.col("rk") > 3)
    alt = metrics(drop)
    j = base.join(alt, on="nfl_id", suffix="_d")
    for c in ("R_top5", "R_p90", "A85"):
        a, b = j[c].to_numpy(), j[c + "_d"].to_numpy()
        out[f"drop_top3_{c}"] = dict(median_change=float(np.median(b - a)), rank_corr=float(pl.DataFrame({"a": a, "b": b}).select(pl.corr("a", "b", method="spearman")).item()))
    return out


def mix_dependence(df, players, cols):
    """Descriptive Spearman correlations of player metrics with route mix, time-to-throw and route count (game-only covariates)."""
    d = df.filter(pl.col("nfl_id").is_in(players.implode()))
    dep = d.group_by("nfl_id").agg((pl.col("ctx") == "deep").mean().alias("deep_share"), (pl.col("k_pf") / 10).mean().alias("mean_ttt"),
                                   pl.col("R").is_not_null().sum().alias("n_routes"))
    m = metrics(d).join(own_top_share(d), on="nfl_id").join(dep, on="nfl_id")
    out = {}
    for c in cols:
        out[c] = {v: float(m.select(pl.corr(c, v, method="spearman")).item()) for v in ("deep_share", "mean_ttt", "n_routes")}
    return out


# ---------------------------------------------------------------------------------------------- main
def main():
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "experiments" / "speed_profile_feasibility" / run; out.mkdir(parents=True)
    R = {"run": run, "status": "EXPLORATORY feasibility audit; not registered; no model fitted; no Combine x outcome association reported"}
    d = wr_routes()

    # ---- coverage / missingness
    has_x = d.filter(pl.col("x_peak").is_not_null())
    R["coverage"] = dict(
        wr_combine=int(pl.read_parquet(INT / "combine_results.parquet").filter(pl.col("combine_position") == "WR").height),
        wr_with_valid_tracked_40=int(pl.read_parquet(JOIN / "predictors.parquet").filter((pl.col("pos") == "WR") & pl.col("x_peak").is_not_null()).height),
        wr_with_REG_routes=int(d["nfl_id"].n_unique()), wr_with_routes_and_x=int(has_x["nfl_id"].n_unique()),
        routes_all=d.height, routes_with_x=has_x.height,
        routes_with_tracking=int(has_x["vmax_play"].is_not_null().sum()),
        routes_with_pass_forward=int(has_x["k_pf"].is_not_null().sum()),
        routes_with_valid_prepass_speed=int(has_x["v"].is_not_null().sum()),
        share_missing_pass_forward_by_result={k: float(v) for k, v in has_x.group_by("pass_result").agg(pl.col("k_pf").is_null().mean()).iter_rows()},
        routes_by_context={k: int(v) for k, v in has_x.filter(pl.col("v").is_not_null()).group_by("ctx").len().iter_rows()},
        routes_by_route={k: int(v) for k, v in has_x.filter(pl.col("v").is_not_null()).group_by("route_ran").len().sort("len", descending=True).iter_rows()})
    per = has_x.filter(pl.col("v").is_not_null()).group_by("nfl_id").agg(pl.len().alias("n"), (pl.col("ctx") == "deep").sum().alias("deep"),
                                                                       (pl.col("ctx") == "short").sum().alias("short"), pl.col("game_id").n_unique().alias("games"),
                                                                       pl.col("season").n_unique().alias("seasons"))
    elig = per.filter(pl.col("n") >= MIN_ROUTES)
    players = elig["nfl_id"]
    R["sample"] = dict(players_ge_1_route=per.height, players_ge_100_routes=elig.height, players_ge_50=int((per["n"] >= 50).sum()), players_ge_200=int((per["n"] >= 200).sum()),
                       eligible_routes=dict(min=int(elig["n"].min()), median=float(elig["n"].median()), max=int(elig["n"].max())),
                       eligible_deep=dict(min=int(elig["deep"].min()), median=float(elig["deep"].median()), max=int(elig["deep"].max())),
                       eligible_short=dict(min=int(elig["short"].min()), median=float(elig["short"].median()), max=int(elig["short"].max())),
                       eligible_games=dict(min=int(elig["games"].min()), median=float(elig["games"].median()), max=int(elig["games"].max())),
                       eligible_seasons={int(k): int(v) for k, v in zip(*np.unique(elig["seasons"], return_counts=True))})

    # ---- measurement compatibility
    e = has_x.filter(pl.col("nfl_id").is_in(players.implode()) & pl.col("v").is_not_null())
    R["measurement"] = dict(
        s_vs_displacement=s_vs_displacement(),
        share_routes_R_gt_1=float((e["R"] > 1).mean()), share_routes_R_gt_0_95=float((e["R"] > 0.95).mean()),
        player_max_R=dict(median=float(e.group_by("nfl_id").agg(pl.col("R").max())["R"].median()),
                          max=float(e["R"].max()), share_players_max_gt_1=float((e.group_by("nfl_id").agg(pl.col("R").max())["R"] > 1).mean())),
        time_to_throw_s_by_ctx={k: dict(median=float(m), p90=float(p)) for k, m, p in e.group_by("ctx").agg((pl.col("k_pf") / 10).median().alias("m"), (pl.col("k_pf") / 10).quantile(0.9).alias("p")).iter_rows()},
        share_max_at_throw_frame_by_ctx={k: float(v) for k, v in e.group_by("ctx").agg((pl.col("s_pf") >= pl.col("v") - 1e-9).mean()).iter_rows()},
        median_R_by_ctx={k: float(v) for k, v in e.group_by("ctx").agg(pl.col("R").median()).iter_rows()},
        share_R_ge_q_by_ctx={f"q{int(q*100)}": {k: float(v) for k, v in e.group_by("ctx").agg((pl.col("R") >= q).mean()).iter_rows()} for q in QS},
        prepass_vs_whole_play=dict(median_v=float(e["v"].median()), median_v_play=float(e["v_play"].median()),
                                   share_whole_play_higher=float((e["v_play"] > e["v"] + 0.05).mean())))

    # ---- reliability
    ratio_cols = ["A80", "A85", "A90", "R_p90", "R_top5"]
    game_cols = ["V_p90", "V_top5"]
    rel = {}
    contexts = {"all_routes": e, "deep_frozen": e.filter(pl.col("ctx") == "deep"), "go_post": e.filter(pl.col("route_ran").is_in(["GO", "POST"])),
                "short_frozen": e.filter(pl.col("ctx") == "short")}
    med_x = float(e.group_by("nfl_id").agg(pl.col("x_peak").first())["x_peak"].median())
    R["median_x_peak_eligible"] = med_x
    for how in ("odd_even", "first_second"):
        for cname, cd in contexts.items():
            sd = split(cd, how)
            ok = sd.group_by("nfl_id", "half").len().group_by("nfl_id").agg(pl.col("len").min().alias("m"), pl.len().alias("h")).filter((pl.col("h") == 2) & (pl.col("m") >= 15))["nfl_id"]
            m0, m1 = metrics(sd.filter(pl.col("half") == 0)), metrics(sd.filter(pl.col("half") == 1))
            res = half_corr(m0, m1, ratio_cols + game_cols, ok)
            c0, c1 = metrics(sd.filter(pl.col("half") == 0), xconst=med_x), metrics(sd.filter(pl.col("half") == 1), xconst=med_x)
            resc = half_corr(c0, c1, ["A80", "A85", "A90"], ok)
            o0, o1 = own_top_share(sd.filter(pl.col("half") == 0)), own_top_share(sd.filter(pl.col("half") == 1))
            reso = half_corr(o0, o1, ["O80", "O85", "O90"], ok)
            rel[f"{how}|{cname}"] = dict(n_players=int(len(ok)), ratio=res, constant_denominator=resc, own_top_game_only=reso)
    R["reliability_unmatched"] = rel
    sd = split(e, "odd_even")
    R["reliability_matched"] = {"min_of_halves": matched_half_corr(sd, ratio_cols + game_cols, players),
                                **{f"n{n}": matched_half_corr(sd, ratio_cols + game_cols, players, n_match=n) for n in (25, 50, 100)}}
    sdd = split(e.filter(pl.col("ctx") == "deep"), "odd_even")
    R["reliability_matched_deep"] = {f"n{n}": matched_half_corr(sdd, ratio_cols + game_cols, players, n_match=n) for n in (25, 50)}
    # whole-play definition (includes sacks/scrambles and post-throw running)
    ew = has_x.filter(pl.col("nfl_id").is_in(players.implode()) & pl.col("R_play").is_not_null()).with_columns(pl.col("R_play").alias("R"), pl.col("v_play").alias("v"))
    sw = split(ew, "odd_even")
    okw = sw.group_by("nfl_id", "half").len().group_by("nfl_id").agg(pl.col("len").min().alias("m")).filter(pl.col("m") >= 15)["nfl_id"]
    R["reliability_whole_play_definition"] = half_corr(metrics(sw.filter(pl.col("half") == 0)), metrics(sw.filter(pl.col("half") == 1)), ratio_cols, okw)

    # ---- individual comparisons, dominance, mix dependence
    R["individual"] = {c: game_cluster_ci(e, players, c) for c in ("A80", "A85", "A90")}
    R["individual"]["rank_A85"] = rank_interval(e, players, "A85")
    R["individual"]["rank_A90"] = rank_interval(e, players, "A90")
    R["dominance"] = top_play_dominance(e, players)
    R["mix_dependence_all_routes"] = mix_dependence(e, players, ["A80", "A85", "A90", "R_top5", "V_top5", "O90"])
    R["mix_dependence_deep_only"] = mix_dependence(e.filter(pl.col("ctx") == "deep"), players, ["A85", "A90", "R_top5", "V_top5"])

    # ---- deployment descriptors (game-only, pre-outcome labels) and their stability
    dep = split(e, "odd_even").group_by("nfl_id", "half").agg(
        (pl.col("ctx") == "deep").mean().alias("deep_share"), (pl.col("ctx") == "short").mean().alias("short_share"),
        (pl.col("route_ran") == "GO").mean().alias("go_share"), pl.col("in_motion_at_ball_snap").fill_null(False).cast(pl.Float64).mean().alias("motion_share"),
        (pl.col("receiver_alignment").is_in(["3x1", "3x2", "4x1"])).mean().alias("trips_plus_share"),
        (pl.col("k_pf") / 10).mean().alias("mean_ttt"))
    d0, d1 = dep.filter(pl.col("half") == 0).drop("half"), dep.filter(pl.col("half") == 1).drop("half")
    R["deployment_stability"] = half_corr(d0, d1, ["deep_share", "short_share", "go_share", "motion_share", "trips_plus_share", "mean_ttt"], players)
    deep_t = e.filter(pl.col("ctx") == "deep")
    tg = split(deep_t, "odd_even").group_by("nfl_id", "half").agg(pl.col("target").fill_null(False).cast(pl.Float64).mean().alias("deep_target_rate"))
    R["deep_target_rate_stability_descriptive"] = half_corr(tg.filter(pl.col("half") == 0).drop("half"), tg.filter(pl.col("half") == 1).drop("half"), ["deep_target_rate"], players)
    R["in_motion_values"] = {str(k): int(v) for k, v in e.group_by("in_motion_at_ball_snap").len().iter_rows()}
    R["target_values"] = {str(k): int(v) for k, v in e.group_by("target").len().iter_rows()}

    json.dump(R, open(out / "summary.json", "w"), indent=1, default=float)
    (ROOT / "experiments" / "speed_profile_feasibility" / "LATEST").write_text(run)
    print("done", out)


if __name__ == "__main__":
    main()
