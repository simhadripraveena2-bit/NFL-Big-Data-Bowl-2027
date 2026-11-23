"""Figures for the Big Data Bowl 2027 writeup (Phase 9B).

Every function takes the registered-results dictionary (paper/registered_results.json, built by
scripts/build_registered_results.py from the registered run outputs) and returns a matplotlib Figure.
No function fits a model or computes an association; they only draw registered numbers.

Accessibility choices:
  * Okabe-Ito colour-blind-safe palette; colour is never the only cue (labels, markers, positions);
  * direct labels instead of legends where possible; >= 9 pt text; units on every axis;
  * zero / reference lines drawn explicitly; axes start at meaningful values (no truncated bars).
"""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OKABE = {"blue": "#0072B2", "sky": "#56B4E9", "green": "#009E73", "orange": "#E69F00",
         "vermillion": "#D55E00", "purple": "#CC79A7", "yellow": "#F0E442", "black": "#000000"}
POS_COLOR = {"WR": OKABE["blue"], "TE": OKABE["sky"], "DB": OKABE["green"], "DL": OKABE["vermillion"], "OL": OKABE["purple"]}
POS_NAME = {"WR": "Wide receivers", "TE": "Tight ends", "DB": "Defensive backs", "DL": "Defensive linemen", "OL": "Offensive linemen"}
CTX_NAME = {"deep": "deep routes", "short": "short routes", "man": "man coverage", "deep_zone": "deep zone",
            "under_zone": "underneath zone", "pass_rush": "pass rush", "run": "run plays", "pass_block": "pass block",
            "pass": "pass plays", "other": "other routes"}
GREY, DARK = "#6b6b6b", "#222222"


def apply_style() -> None:
    mpl.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "axes.labelsize": 10, "xtick.labelsize": 9.5, "ytick.labelsize": 9.5,
        "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": GREY, "axes.labelcolor": DARK,
        "xtick.color": DARK, "ytick.color": DARK, "axes.grid": True, "grid.color": "#e5e5e5", "grid.linewidth": 0.7,
        "axes.axisbelow": True, "legend.frameon": False, "figure.dpi": 110, "savefig.dpi": 200,
    })


def _note(fig, text, y=0.01):
    fig.text(0.01, y, text, fontsize=8.5, color=GREY, ha="left", va="bottom", wrap=True)


# ------------------------------------------------------------------------------------------------------
def fig1_framework(R: dict):
    """Four measurement layers and which analysis links them (schematic with registered sample sizes)."""
    fig, ax = plt.subplots(figsize=(10, 4.9))
    ax.set_axis_off(); ax.set_xlim(0, 10); ax.set_ylim(0, 4.9)
    n_wr = R["samples"]["analysis"]["H1-WR"]["players"]
    boxes = {
        "cap": (0.2, 2.2, 2.8, 1.6, "COMBINE CAPACITY", "Tracked 40-yd peak speed\n(sensor data, best valid attempt)\n510 prospects, 2023–25", OKABE["blue"]),
        "mov": (3.6, 2.2, 2.8, 1.6, "GAME MOVEMENT", "Max speed on each REG play\n(10 Hz game tracking)\nby route / coverage / alignment", OKABE["orange"]),
        "perf": (7.0, 2.2, 2.8, 1.6, "FOOTBALL PERFORMANCE", "WR separation at the throw\n(distance to nearest defender)\ndeep routes", OKABE["green"]),
        "dep": (3.6, 0.15, 2.8, 1.25, "DEPLOYMENT & BODY TYPE", "route mix, coverage, DL alignment\n(EDGE / interior), body weight", OKABE["purple"]),
    }
    for _, (x, y, w, h, title, body, col) in boxes.items():
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.12", fc="white", ec=col, lw=2.2))
        ax.text(x + w / 2, y + h - 0.25, title, ha="center", va="top", fontsize=9.8, fontweight="bold", color=DARK)
        ax.text(x + w / 2, y + h - 0.6, body, ha="center", va="top", fontsize=9, color=DARK, linespacing=1.35)

    def arrow(p, q, label, col=DARK, rad=0.0, dy=0.12):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=16, lw=1.8, color=col,
                                     connectionstyle=f"arc3,rad={rad}"))
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + dy, label, ha="center", va="bottom", fontsize=8.8, color=col)

    arrow((3.02, 3.0), (3.58, 3.0), "H1", dy=0.08)
    ax.add_patch(FancyArrowPatch((1.6, 3.82), (8.4, 3.82), arrowstyle="-|>", mutation_scale=16, lw=1.8, color=DARK,
                                 connectionstyle="arc3,rad=-0.12"))
    ax.text(5.0, 4.62, f"H2: does tracked top speed add anything beyond the official 40?  (WR, n = {n_wr})",
            ha="center", va="center", fontsize=9, color=DARK)
    arrow((6.42, 3.0), (6.98, 3.0), "", col=GREY)
    for xq in (4.3, 7.6):
        ax.add_patch(FancyArrowPatch((5.0 if xq == 4.3 else 6.0, 1.42), (xq, 2.18), arrowstyle="-|>", mutation_scale=13,
                                     lw=1.4, color=OKABE["purple"], ls="--"))
    ax.text(1.6, 1.0, "Deployment shapes both movement\nand performance. It must be\nadjusted for, or the analysis\nmistakes usage for ability.",
            ha="center", va="center", fontsize=8.8, color=DARK)
    ax.set_title("Figure 1. Four things that are easy to confuse", pad=6)
    return fig


# ------------------------------------------------------------------------------------------------------
def fig2_tracking_vs_forty(R: dict):
    """Reliability of tracked peak speed and share of its variance not explained by the official 40."""
    cm = R["combine_measurement"]
    order = ["WR", "DB", "OL", "TE", "DL"]
    rel = {r["pos"]: r for r in cm["reliability"]}
    uv = {r["pos"]: r for r in cm["vs_forty"]}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.9), gridspec_kw={"wspace": 0.55})
    ys = range(len(order))[::-1]
    for y, p in zip(ys, order):
        r = rel[p]; c = POS_COLOR[p]
        a1.plot(r["icc_single_ci95"], [y, y], color=c, lw=2.2)
        a1.plot(r["icc_single"], y, "o", color=c, ms=7, mfc="white", mew=2)
        a1.plot(r["best_of_2"], y, "D", color=c, ms=6.5)
        a1.text(1.005, y, f"n = {r['n']}", va="center", fontsize=8.5, color=GREY)
        u = uv[p]
        a2.barh(y, 100 * u["unique_var"], color=c, height=0.6, edgecolor=DARK, linewidth=0.6)
        a2.text(100 * u["unique_var"] + 1, y, f"{100 * u['unique_var']:.0f}%", va="center", fontsize=9.5, color=DARK)
        a2.text(-1.5, y, f"n = {u['n']}", va="center", ha="right", fontsize=8.5, color=GREY)
    for a in (a1, a2):
        a.set_yticks(list(ys)); a.set_yticklabels([POS_NAME[p] for p in order])
    a1.set_xlim(0.8, 1.0); a1.set_xlabel("Test–retest reliability of tracked 40 peak speed\n(within position; 1 = perfectly repeatable)")
    a1.set_title("A. Tracked top speed is highly repeatable", fontsize=11)
    a1.plot([], [], "o", color=GREY, mfc="white", mew=2, label="one attempt (95% CI)")
    a1.plot([], [], "D", color=GREY, label="best of two attempts (used)")
    a1.legend(loc="lower left", fontsize=8.5)
    a2.set_xlim(0, 45); a2.set_xlabel("% of tracked-peak-speed variance NOT\nexplained by the official 40 time (1 − r²)")
    a2.set_title("B. What tracking adds beyond the 40", fontsize=11)
    a2.tick_params(axis="y", labelleft=False)
    fig.suptitle("Figure 2. Combine tracking measures top speed reliably, and for WR and DB it is not the same as the 40",
                 x=0.01, ha="left", fontsize=12, fontweight="bold", y=1.02)
    _note(fig, "Combine data only (no game outcome). Panel B: point estimates; n = combine participants with both measures. "
               "Reliability: same-session repeat 40s; within-position ICC(3,1); best-of-two by Spearman–Brown.", y=-0.2)
    return fig


# ------------------------------------------------------------------------------------------------------
def fig3_speed_demand(R: dict):
    """Share of plays on which a player reaches >= 90 % of his own top game speed (no combine data)."""
    rows = R["speed_demand"]["rows"]
    keep = [("WR", "deep"), ("WR", "short"), ("TE", "deep"), ("TE", "short"), ("DB", "man"), ("DB", "deep_zone"),
            ("DB", "under_zone"), ("DL", "pass"), ("DL", "run"), ("OL", "pass"), ("OL", "run")]
    lut = {(r["pos"], r["context"]): r for r in rows}
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    ys = list(range(len(keep)))[::-1]
    for y, (p, c) in zip(ys, keep):
        r = lut[(p, c)]; v = 100 * r["share_plays_ge90pct_own_top"]
        ax.barh(y, v, color=POS_COLOR[p], height=0.62, edgecolor=DARK, linewidth=0.6)
        ax.text(v + 0.3, y, f"{v:.1f}%   ({r['plays']:,} plays)", va="center", fontsize=9, color=DARK)
    ax.set_yticks(ys); ax.set_yticklabels([f"{p}: {CTX_NAME[c]}" for p, c in keep])
    ax.set_xlim(0, 25); ax.set_xlabel("% of plays on which the player reaches ≥ 90% of his own top game speed")
    ax.set_title("Figure 3. Top speed is a deep-route tool: most NFL snaps never ask for it")
    _note(fig, "REG 2023–25, cohort players. Own top speed = mean of the player's 5 fastest REG plays. Descriptive, game data only "
               "(no combine values). DL / OL 'pass' = pass-rush / pass-block snaps.", y=-0.02)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    return fig


# ------------------------------------------------------------------------------------------------------
def fig4_translation(R: dict):
    """Correlation between combine peak speed and true game-speed level, by position and task context."""
    rows = R["rho_by_context"]["rows"]
    con = R["contrasts"]
    order = [("WR", "deep"), ("WR", "short"), ("TE", "deep"), ("TE", "short"), ("DB", "man"), ("DB", "deep_zone"),
             ("DB", "under_zone"), ("DL", "pass_rush"), ("DL", "run"), ("OL", "pass_block"), ("OL", "run")]
    lut = {(r["pos"], r["ctx"]): r for r in rows}
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    ys = []; y = 0; labels = []; seen = []
    gap_after = {"WR": 0.8, "TE": 0.8, "DB": 0.8, "DL": 0.8}
    for p, c in order:
        if seen and seen[-1] != p:
            y -= gap_after[seen[-1]]
        seen.append(p)
        ys.append(y); labels.append(f"{p}: {CTX_NAME[c]}"); y -= 1
    for yy, (p, c) in zip(ys, order):
        r = lut[(p, c)]; col = POS_COLOR[p]
        ax.plot(r["ci95_wald"], [yy, yy], color=col, lw=2.4, solid_capstyle="butt")
        ax.plot(r["rho"], yy, "o", color=col, ms=8, mec="white", mew=1)
    ax.axvline(0, color=DARK, lw=1)
    ax.set_yticks(ys); ax.set_yticklabels(labels); ax.set_xlim(-1, 1.62)
    ax.set_xticks([-1, -0.5, 0, 0.5, 1])
    ax.set_xlabel("Correlation between combine tracked peak speed and the player's game-speed level (95% interval)")
    txt = {
        "WR": f"Deep − short Δ = {con['H1-WR']['estimate']:.2f}\n[{con['H1-WR']['ci95'][0]:.2f}, {con['H1-WR']['ci95'][1]:.2f}]  INCONCLUSIVE\n(primary test)",
        "TE": "Descriptive only\n(too few players to test)",
        "DB": f"Man − underneath Δ = {con['H1-DB']['estimate']:.2f}\n[{con['H1-DB']['ci95'][0]:.2f}, {con['H1-DB']['ci95'][1]:.2f}]  inconclusive",
        "DL": f"Pass rush − run Δ = {con['H1-DL(a)']['estimate']:.2f}\n[{con['H1-DL(a)']['ci95'][0]:.2f}, {con['H1-DL(a)']['ci95'][1]:.2f}]  no ≥0.15 gap",
        "OL": f"Pass block − run Δ = {con['H5(a) OL']['estimate']:.2f}\n[{con['H5(a) OL']['ci95'][0]:.2f}, {con['H5(a) OL']['ci95'][1]:.2f}]  uninformative",
    }
    npl = {r["pos"]: r["players"] for r in rows}
    for p in ["WR", "TE", "DB", "DL", "OL"]:
        yy = [y_ for y_, (q, _) in zip(ys, order) if q == p]
        ax.text(1.06, sum(yy) / len(yy), txt[p] + f"\nplayers = {npl[p]}", va="center", fontsize=8.6, color=DARK)
    ax.axvline(1.02, color="#dddddd", lw=0.8)
    ax.set_title("Figure 4. Combine top speed shows up in game speed for WR and DL, much less for DB and OL")
    _note(fig, "Dots: REML estimates of the correlation with each player's noise-free game-speed level (play maximum speed, "
               "pre-throw for WR/TE), adjusting for pre-snap context. Bars: Wald 95% intervals (registered check output). "
               "Right: registered contrasts with bootstrap 95% CIs. Associations, not causal effects.", y=-0.03)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    return fig


# ------------------------------------------------------------------------------------------------------
def fig5_h2(R: dict):
    """H2: tracked peak speed and WR deep-route separation, holding the official 40 fixed."""
    h = R["h2"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 4.0), gridspec_kw={"width_ratios": [1.35, 1], "wspace": 0.45})
    items = [("Deep routes\n(registered H2 estimate)", h["beta_P_in_per_sd"], h["beta_P_ci95_in"], OKABE["blue"], "o"),
             ("Short routes\n(negative control, descriptive)", h["short_beta_P_in"], h["short_beta_P_ci95_in"], GREY, "s")]
    for y, (lab, est, ci, col, m) in zip([1, 0], items):
        a1.plot(ci, [y, y], color=col, lw=2.6)
        a1.plot(est, y, m, color=col, ms=9, mec="white")
        a1.text(ci[1] + 0.4, y, f"{est:+.1f} in [{ci[0]:+.1f}, {ci[1]:+.1f}]", va="center", fontsize=9.2, color=col)
    a1.axvline(0, color=DARK, lw=1)
    a1.set_yticks([1, 0]); a1.set_yticklabels([i[0] for i in items]); a1.set_ylim(-0.6, 1.6)
    a1.set_xlim(-6, 20)
    a1.set_xlabel("Change in separation at the throw per 1 SD of tracked peak speed\n(inches; official 40 held fixed; 95% CI)")
    a1.set_title("A. No added separation detected on deep routes", fontsize=11)
    cv = h["cv_frozen"]
    names = ["Position average\n(reference)", "Official 40\nonly", "40 + tracked\npeak speed"]
    vals = [0.0, cv["r2_m1"], cv["r2_m2"]]
    cols = [GREY, OKABE["sky"], OKABE["blue"]]
    a2.bar(range(3), vals, color=cols, width=0.6, edgecolor=DARK, linewidth=0.6)
    for i, v in enumerate(vals):
        a2.text(i, v - 0.003 if v < 0 else v + 0.002, f"{v:+.3f}", ha="center", va="top" if v < 0 else "bottom", fontsize=9.5)
    a2.axhline(0, color=DARK, lw=1)
    a2.set_xticks(range(3)); a2.set_xticklabels(names); a2.set_ylim(-0.08, 0.08)
    a2.set_ylabel("Out-of-sample R² for held-out receivers\n(0 = as good as the position average)")
    a2.set_title("B. Predicting unseen receivers", fontsize=11)
    fig.suptitle("Figure 5. Tracked top speed did not add detectable information about deep-route separation (H2)",
                 x=0.01, ha="left", fontsize=12, fontweight="bold", y=1.03)
    _note(fig, f"WR, n = {R['samples']['analysis']['H2-WR']['players']} players, {R['samples']['analysis']['H2-WR']['deep_plays']:,} deep routes on thrown passes. "
               "A: REML coefficient with player-cluster bootstrap (B = 2,000). B: player-grouped 10-fold cross-validation × 20. "
               "Secondary, estimation-focused analysis (status fixed before any association was examined). Label: INCONCLUSIVE.", y=-0.2)
    return fig


# ------------------------------------------------------------------------------------------------------
def fig6_reliability(R: dict):
    """How much of a WR metric is a stable player trait, before and after route/coverage adjustment."""
    rows = R["outcome_reliability_wr"]["rows"]
    lut = {(r["outcome"], r["kind"]): r for r in rows}
    items = [("vmax_prepass", "Route top speed\n(movement)"), ("target_f", "Targets per route\n(usage / performance)"),
             ("separation_at_pass_forward", "Separation, all routes\n(performance)"),
             ("separation_deep", "Separation, deep routes\n(performance)"), ("separation_short", "Separation, short routes\n(performance)")]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ys = list(range(len(items)))[::-1]
    for y, (k, lab) in zip(ys, items):
        raw, adj = lut[(k, "raw")], lut[(k, "adj")]
        ax.plot([raw["split_half_sb"], adj["split_half_sb"]], [y, y], color="#bbbbbb", lw=2, zorder=1)
        ax.plot([max(adj["sb_lo"], -0.2), adj["sb_hi"]], [y - 0.18, y - 0.18], color=OKABE["blue"], lw=1.6)
        if adj["sb_lo"] < -0.2:
            ax.annotate(f"lower limit {adj['sb_lo']:.2f}", xy=(-0.2, y - 0.18), xytext=(0.02, y - 0.5), fontsize=8.6,
                        color=OKABE["blue"], arrowprops=dict(arrowstyle="->", color=OKABE["blue"], lw=1))
        ax.plot(raw["split_half_sb"], y, "o", color=OKABE["orange"], ms=9, mec=DARK, mew=0.8, zorder=3)
        ax.plot(adj["split_half_sb"], y, "D", color=OKABE["blue"], ms=8, zorder=3)
        ax.text(1.02, y, f"{raw['split_half_sb']:.2f} → {adj['split_half_sb']:.2f}   (n = {adj['players_eligible']})", va="center", fontsize=9)
    ax.plot([], [], "o", color=OKABE["orange"], ms=8, mec=DARK, mew=0.8, label="raw player average")
    ax.plot([], [], "D", color=OKABE["blue"], ms=7, label="after route / coverage / down / formation adjustment (line: 95% CI)")
    ax.legend(loc="upper left", fontsize=8.8, bbox_to_anchor=(0, -0.16), ncol=2)
    ax.set_yticks(ys); ax.set_yticklabels([i[1] for i in items]); ax.set_xlim(-0.2, 1.0); ax.set_ylim(-0.75, len(items) - 0.5)
    ax.axvline(0, color=DARK, lw=0.8)
    ax.set_xlabel("Split-half reliability of the player-level average (0 = pure noise, 1 = stable trait)")
    ax.set_title("Figure 6. Much of a receiver's raw separation reflects how he is used, not who he is")
    _note(fig, f"WR with ≥ 100 routes, REG 2023–25; game-parity split halves, Spearman–Brown corrected; bootstrap 95% CI over players. "
               f"Outcome-blind (no combine data). The registered H2 model gives deep-separation reliability "
               f"{R['h2']['reliability_deep_level']:.2f} (between-player SD {R['h2']['between_player_sd_yd']:.2f} yd).", y=-0.08)
    fig.subplots_adjust(right=0.78, bottom=0.26)
    return fig


# ------------------------------------------------------------------------------------------------------
def fig7_dl(R: dict):
    """DL: combine speed, body weight and role travel together; the pooled association depends on adjustment."""
    d = R["dl_b"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.8, 4.3), gridspec_kw={"width_ratios": [1, 1.5], "wspace": 0.75})
    rm = {r["modal"]: r for r in d["role_means"]}
    for i, (key, lab, col) in enumerate([("EDGE", "EDGE rushers", OKABE["vermillion"]), ("INTERIOR_LINE", "Interior linemen", OKABE["purple"])]):
        r = rm[key]
        a1.errorbar(r["combine_weight"], r["x_peak"], xerr=r["w_sd"], yerr=r["x_sd"], fmt="o", color=col, ms=9, capsize=3, lw=1.8)
        a1.text(r["combine_weight"] + (6 if i == 0 else -6), r["x_peak"] + (0.12 if i == 0 else -0.62), f"{lab}\nn = {r['n']}",
                color=DARK, fontsize=9.2, ha="left" if i == 0 else "right")
    a1.set_xlabel("Combine weight (lb), mean ± SD"); a1.set_ylabel("Tracked 40 peak speed (yd/s), mean ± SD")
    a1.set_xlim(230, 340); a1.set_ylim(8.8, 11.2)
    r_sw = d["corr_eligible"]["matrix"][0][1]
    a1.set_title(f"A. Speed, weight and role are one profile\n(speed–weight r = {r_sw:.2f})", fontsize=11)
    labels = ["Registered model\n(no role / weight)", "+ role", "+ weight", "+ role and weight\n(registered adjusted)", "EDGE only", "Interior only"]
    vals = [(v["pooled"], v["ci95_wald"]) for v in d["variants"]] + \
           [(d["within_role"][k]["pooled"], d["within_role"][k]["ci95_wald"]) for k in ("EDGE", "INTERIOR_LINE")]
    ys = [5, 4, 3, 2, 0.6, -0.4]
    for y, (v, ci), lab in zip(ys, vals, labels):
        col = OKABE["vermillion"] if y >= 2 else GREY
        a2.plot(ci, [y, y], color=col, lw=2.3); a2.plot(v, y, "o", color=col, ms=8, mec="white")
        a2.text(1.08, y, f"{v:+.2f}", va="center", fontsize=9.2, color=DARK)
    a2.axvline(0, color=DARK, lw=1)
    a2.set_yticks(ys); a2.set_yticklabels(labels, fontsize=9); a2.set_xlim(-1, 1.25); a2.set_xticks([-1, -0.5, 0, 0.5, 1])
    a2.set_xlabel("Pooled correlation: combine peak speed vs game-speed level (Wald 95%)")
    reg = d["registered"]
    a2.set_title(f"B. The pooled DL association is sensitive to role and weight\n"
                 f"registered test (pooled − adjusted) = {reg['estimate']:.2f} [{reg['ci95'][0]:.2f}, {reg['ci95'][1]:.2f}], Holm p = {reg['p_holm']:.3f}", fontsize=11)
    fig.suptitle("Figure 7. For defensive linemen, 'combine speed' is largely body type and role",
                 x=0.01, ha="left", fontsize=12, fontweight="bold", y=1.06)
    _note(fig, "DL, n = 53 (25 EDGE / 28 interior), REG 2023–25. B: descriptive audit intervals; only the registered pooled-minus-adjusted "
               "test is inferential. Not causal: role partly results from athleticism; the adjusted value is not a speed effect.", y=-0.1)
    return fig


FIGURES = {
    "fig1_framework": fig1_framework, "fig2_tracking_vs_forty": fig2_tracking_vs_forty, "fig3_speed_demand": fig3_speed_demand,
    "fig4_translation": fig4_translation, "fig5_h2_separation": fig5_h2, "fig6_reliability": fig6_reliability, "fig7_dl_role_weight": fig7_dl,
}
