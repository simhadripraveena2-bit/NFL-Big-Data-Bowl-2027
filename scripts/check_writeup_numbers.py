"""Phase 9B quality check: every key number in paper/final_writeup.md must match the registered results.

For each claim, the expected text is formatted from paper/registered_results.json (built from the registered
run outputs) and must appear verbatim in the writeup. Also checks the word and visual limits and the
mandatory statistical wording. Exit code 1 on any failure.
Usage: python scripts/check_writeup_numbers.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = json.loads((ROOT / "paper/registered_results.json").read_text())
W = (ROOT / "paper/final_writeup.md").read_text()
f2 = lambda v: f"{v:.2f}".replace("-", "−")  # noqa: E731  (writeup uses the typographic minus)
f3 = lambda v: f"{v:.3f}".replace("-", "−")  # noqa: E731

h1, h2, con, dl, cm = R["h1_wr"], R["h2"], R["contrasts"], R["dl_b"], R["combine_measurement"]
rel = {r["pos"]: r for r in cm["reliability"]}
uv = {r["pos"]: r for r in cm["vs_forty"]}
sd = {(r["pos"], r["context"]): r["share_plays_ge90pct_own_top"] for r in R["speed_demand"]["rows"]}
orl = {(r["outcome"], r["kind"]): r["split_half_sb"] for r in R["outcome_reliability_wr"]["rows"]}
orl_ci = {(r["outcome"], r["kind"]): (r["sb_lo"], r["sb_hi"]) for r in R["outcome_reliability_wr"]["rows"]}
orl_n = [r for r in R["outcome_reliability_wr"]["rows"] if r["outcome"] == "separation_at_pass_forward"][0]["players_eligible"]
mat = {r["pos"]: r for r in R["samples"]["matching_by_position"]}
an = R["samples"]["analysis"]
checks = [
    # mandatory wording (H1-WR, H2, DL(b))
    ("H1-WR mandatory", f"Primary test: INCONCLUSIVE. Δ = ρ_deep − ρ_short = {f3(h1['delta'])}, 95% CI [{f3(h1['ci95'][0])}, {f3(h1['ci95'][1])}]"),
    ("H2 mandatory (inches)", "Deep separation: INCONCLUSIVE. With the official 40 held fixed, each extra standard deviation (SD) of tracked peak speed went with "
                     + f"{h2['beta_P_in_per_sd']:.1f}".replace("-", "−") + " inches of separation, 95% CI "
                     + f"{h2['beta_P_ci95_in'][0]:.1f}".replace("-", "−") + f" to +{h2['beta_P_ci95_in'][1]:.1f} inches"),
    ("H2 yd (appendix)", f"β_P = {f3(h2['beta_P_yd_per_sd'])} yd per SD, 95% CI [{f3(h2['beta_P_ci95_yd'][0])}, {f3(h2['beta_P_ci95_yd'][1])}] yd"),
    ("H2 upper limit ~ half SD", "The upper limit, +" + f"{h2['beta_P_ci95_in'][1]:.1f}" + " inches, is about half of the between-player SD of deep separation ("
                     + f"{h2['between_player_sd_yd']:.2f} yd, about {h2['between_player_sd_yd'] * 36:.1f} inches)"
                     if 0.45 <= h2['beta_P_ci95_yd'][1] / h2['between_player_sd_yd'] <= 0.55 else "H2 ratio mismatch"),
    ("H2 moderate effects", "Moderate effects remain possible"),
    ("H2 not zero", "The data do not establish that the added effect is zero"),
    ("H2 no-incremental wording", "No incremental predictive value was detected for tracked peak speed beyond the official 40 for deep-route separation"),
    ("H2 not-no-effect wording", "This does not show that speed has no effect on separation"),
    ("H2 reliability", f"player-level reliability is **{f2(h2['reliability_deep_level'])}**"),
    ("H2 demotion preserved", "demoted to a secondary, estimation-focused analysis before any Combine-to-game association was examined"),
    ("DL(b) mandatory", f"This secondary test was supported after a Holm correction for testing several secondary comparisons (adjusted p = {f3(con['H1-DL(b)']['p_holm'])})"),
    ("DL(b) sensitivity wording", "substantially sensitive to role and weight adjustment"),
    ("DL(b) not causal", "This is not a causal statement"),
    # H1 numbers
    ("rho deep/short", f"ρ = {f2(h1['rho_deep'])} on deep routes and {f2(h1['rho_short'])} on short routes"),
    ("H1 p", f"(p = {h1['p']:.2f})"),
    ("WR sample", f"| WR | {an['H1-WR']['players']} | {an['H1-WR']['plays']:,} |"),
    ("DL sample", f"| DL | {an['H1-DL']['players']} | {an['H1-DL']['plays']:,} |"),
    ("OL sample", f"| OL | {an['H1-OL']['players']} | {an['H1-OL']['plays']:,} |"),
    ("DB sample", f"| DB | {an['H1-DB']['players']} | {an['H1-DB']['plays']:,} |"),
    ("TE sample", f"| TE (descriptive only) | {an['H1-TE']['players']} | {an['H1-TE']['plays']:,} |"),
    ("H2 sample", f"({an['H2-WR']['players']} WRs, {an['H2-WR']['deep_plays']:,} deep routes on thrown passes)"),
    ("valid tracked 40", f"{sum(r['valid_tracked_40'] for r in mat.values())} have at least one valid tracked 40"),
    ("matched", f"{sum(r['matched_REG_and_valid_40'] for r in mat.values())} of them also have regular-season game rows"),
    # H2 numbers
    ("H2 CV", f"lowered out-of-sample R² by {abs(h2['cv_frozen']['dr2']):.3f} (90% lower bound {f3(h2['cv_frozen']['lb90'])})"),
    ("H2 season-forward", "RMSE change " + f"{h2['season_forward']['dRMSE']:.4f}".replace("-", "−") + " yd"),
    ("H2 between-player SD", f"between-player SD is {f2(h2['between_player_sd_yd'])} yd"),
    # DL
    ("DL pooled", f"falls from {f2(dl['base_pooled'])} to {f2(dl['adjusted_pooled'])}"),
    ("DL diff", f"registered difference {f2(con['H1-DL(b)']['estimate'])}, 95% CI [{f2(con['H1-DL(b)']['ci95'][0])}, {f2(con['H1-DL(b)']['ci95'][1])}]"),
    ("DL role alone", f"role alone ({f2(dl['variants'][1]['pooled'])})"),
    ("DL weight alone", f"weight alone ({f2(dl['variants'][2]['pooled'])})"),
    ("DL within EDGE", f"within EDGE ({f2(dl['within_role']['EDGE']['pooled'])})"),
    ("DL within interior", f"within interior linemen ({f2(dl['within_role']['INTERIOR_LINE']['pooled'])})"),
    ("speed-weight r", f"speed–weight r = {f2(dl['corr_eligible']['matrix'][0][1])}"),
    # combine measurement
    ("rel WR best2", f"is 0.94 (WR) to {f2(rel['DL']['best_of_2'])} (DL)" if f2(rel['WR']['best_of_2']) == "0.94" else "WR rel mismatch"),
    ("unique WR/DB", f"(WR {round(100 * uv['WR']['unique_var'])}%, DB {round(100 * uv['DB']['unique_var'])}%)"),
    ("unique DL", f"only {round(100 * uv['DL']['unique_var'])}% of peak-speed variance is not explained by the 40"),
    ("WR peak vs split", f"(ρ = {f2([r for r in cm['vs_ten_yd_split'] if r['pos'] == 'WR'][0]['spearman'])})"),
    # demand
    ("demand WR deep/short", f"**WR deep routes do so on {round(100 * sd[('WR', 'deep')])}% of snaps, short routes on {round(100 * sd[('WR', 'short')])}%.**"),
    # separation reliability
    ("sep raw + CI", f"(reliability {f2(orl[('separation_at_pass_forward', 'raw')])}, 95% CI {f2(orl_ci[('separation_at_pass_forward', 'raw')][0])}–{f2(orl_ci[('separation_at_pass_forward', 'raw')][1])})"),
    ("sep adj + CI", f"it falls to {f2(orl[('separation_at_pass_forward', 'adj')])} ({f2(orl_ci[('separation_at_pass_forward', 'adj')][0])}–{f2(orl_ci[('separation_at_pass_forward', 'adj')][1])})"),
    ("short sep + CI", f"Short-route reliability is also low after adjustment ({f2(orl[('separation_short', 'adj')])}), but very uncertain (95% CI {f2(orl_ci[('separation_short', 'adj')][0])} to {f2(orl_ci[('separation_short', 'adj')][1])})"),
    ("reliability population", f"use {orl_n} receivers with at least 100 regular-season routes; the registered analyses use {an['H1-WR']['players']}"),
]
# Phase 9B.1 mandatory headlines (writeup and figure source)
FIGSRC = (ROOT / "src/nfl_bdb/visualization/submission_figures.py").read_text()
H3 = "Players reach near-top game speed more often on deep routes than on short routes"
H7 = "The pooled defensive-line speed association is substantially sensitive to role and body-weight adjustment"
F7 = "Figure 7. Defensive-line speed, weight and role travel together"
checks += [("Fig 3 headline in writeup (section 4)", "## 4. " + H3),
           ("Fig 3 descriptive caveat", "not a direct measurement of opportunity, and it is not evidence that Combine speed has a stronger effect on deep routes"),
           ("Section 7 heading", "## 7. " + H7)]
# Phase 20 additions: power (source text must also contain the numbers), provenance, eligibility, framing
PA = (ROOT / "research_notes/power_analysis.md").read_text()
src_fails = [n for n, t in [("MDE source", "**0.27–0.33**"), ("power 0.2 source", "Power is **0.44** at Δ = 0.2"), ("central 0.30 source", "| WR | 0.33 | **0.30** |")] if t not in PA]
checks += [("Title", "# What Combine Tracking Can and Cannot Tell Us About NFL Game Movement"),
           ("H1-WR MDE", "80% power only for a difference of **0.27–0.33** (central scenario about 0.30). Power at a true difference of 0.20 was only about 0.44"),
           ("H1-WR not equivalence", "This is **not** evidence that the two contexts are equivalent"),
           ("separation provenance", "competition-supplied Next Gen Stats field `separation_at_pass_forward`. We did **not** rebuild nearest-defender distance"),
           ("separation coverage", "The field exists for every route on a thrown pass, targeted or not, and is missing on sacks and scrambles"),
           ("consistency check scope", "That is a consistency check on a subset, not proof of every defender assignment"),
           ("eligibility", "**at least 100 qualifying regular-season opportunities**"),
           ("no bust claim", "Nothing here predicts draft busts or career success"),
           ("no distinct capacity", "we do **not** claim tracked peak speed is a separate athletic capacity"),
           ("DL joint imprecise", "is not evidence that speed hurts linemen"),
           ("DL supported contrast", "What was supported is the *change* between the pooled and adjusted estimates"),
           ("follow-up not fitted", "that model was never fitted to real data. It supports no conclusion either way")]
FORBIDDEN = ["not the same thing as the 40", "distinct athletic capacity", "equally predictive", "tracking does not add information",
             "significantly", "Phase 19", "commit", "novel algorithm", "rule out a large", "rules out a gain", "negligible",
             "We make no novelty claim", "full texts not read", "alongside the 40", "H5(b)", "H1-DL(b)", " REG ", "(REG)", "Wald",
             "ICC(3,1)", "Spearman–Brown", "less spread in short", "negative control", "noise-free"]
H1SRC = (ROOT / "research_notes/h1_wr_confirmatory_results.md").read_text()
src_fails += [n for n, t in [("slopes source", "**0.110 yd/s** higher on deep routes and **0.113 yd/s** higher on short routes"),
                             ("Sigma_b source (deep < short)", "[[0.0353, 0.0301], [0.0301, 0.0600]]")] if t not in H1SRC]
checks += [("slopes", "0.110 (deep) and 0.113 (short) yd/s of game speed per 0.25 yd/s of Combine speed"),
           ("variance direction", "the model estimates less between-player variation in game-speed level on deep routes than on short routes"),
           ("rho defined", "ρ (from −1 to 1; 0 means no linear relationship)"),
           ("contribution", "This study combines a pre-registered analysis of how Combine peak speed relates to NFL game movement with a systematic reliability assessment"),
           ("eligibility direction", "Eligible receivers were drafted much higher than ineligible receivers but were only about 0.02 seconds faster on the official 40"),
           ("table tracked peak", "its incremental value beyond the official 40 for game outcomes remains unresolved"),
           ("table separation CV", "official 40 alone and 40 + tracked peak both failed to beat the position average; adding tracked peak lowered R² by " + f"{abs(h2['cv_frozen']['dr2']):.3f}"),
           ("table WR game speed", "not compared with the official 40"),
           ("model sentence", "A mixed model estimates each player's underlying game-speed level in each context")]
R14 = (ROOT / "research_notes/h1_wr_robustness_results.md").read_text()
src_fails += [n for n, t in [("R14 source", "| eligible (≥ 100 routes) | 57 | 4.465 ± 0.090 s | 11.12 yd/s | 3.8 | 12 % |"),
                             ("R14 source inel", "| ineligible | 37 | 4.485 ± 0.088 s | 11.10 yd/s | 5.4 | 46 % |")] if t not in R14]
forb_fails = [f for f in FORBIDDEN if f.lower() in W.lower()]
forb_fails += [f"figure source: {f}" for f in ["noise-free game-speed level"] if f in FIGSRC]
fig_checks = [("Fig 3 title in figure", "Figure 3. " + H3), ("Fig 7 title in figure", F7), ("Fig 4 caption wording", "each player's underlying game-speed level"), ("Fig 5 descriptive label", "Short routes\\n(descriptive comparison)"), ("Fig 2 panel B labels shown", "a2.set_yticklabels"), ("Fig 6 short CI in caption", "short-route adjusted reliability")]
fails = [(n, e) for n, e in checks if e not in W] + [(n, e) for n, e in fig_checks if e not in FIGSRC] + \
        [(n, "source text missing") for n in src_fails] + [("forbidden phrase", f) for f in forb_fails]
checks += fig_checks
for n, e in checks:
    print(("OK  " if (n, e) not in fails else "FAIL"), n, "::", e)
for n, e in fails:
    if (n, e) not in checks:
        print("FAIL", n, "::", e)


def wc(s):
    s = re.sub(r"\]\([^)]*\)", "]", s); s = re.sub(r"[|#*`>-]+", " ", s)
    return len([w for w in s.split() if re.search(r"[A-Za-z0-9]", w)])


words = wc(W); figs = len(re.findall(r"!\[", W))
tables = sum(1 for blk in re.split(r"\n\s*\n", W) if re.search(r"^\s*\|.*\|\s*$", blk, re.M) and "---" in blk)
print(f"\nwords (whole writeup incl. appendix, captions and alt text): {words}  | figures: {figs}  | tables: {tables}  | visuals: {figs + tables}")
lim_ok = words <= 2000 and figs + tables < 10
if not lim_ok:
    print("FAIL limits")
sys.exit(1 if fails or not lim_ok else 0)
