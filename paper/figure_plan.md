# Figure plan: Big Data Bowl 2027 writeup

**Budget:** fewer than 10 tables + figures (competition rule). The writeup uses **7 figures + 2 tables = 9**.

**Sources and build:**
- Every figure is drawn from `paper/registered_results.json`. That file is built from the registered run outputs by `scripts/build_registered_results.py`.
- Rendering: `scripts/build_submission_figures.py`, using `src/nfl_bdb/visualization/submission_figures.py`.
- No figure fits a model or computes a new association.

**Display transforms only:**
- yards → inches;
- proportions → percentages;
- Wald intervals ρ ± 1.96·SE, from Wald SEs already stored by the registered secondary run.

## Accessibility rules applied to every figure

- **Colour:** Okabe–Ito colour-blind-safe palette, fixed per position: WR blue, TE sky blue, DB green, DL vermillion, OL reddish purple.
  - Colour is never the only cue: every series also has a text label, a marker shape or a row position.
- **Labelling:** direct labels next to the data; legends only where unavoidable. Text is ≥ 8.5 pt at 200 dpi.
- **Axes:**
  - units on every axis (yd/s, inches, %, lb, correlation);
  - correlation axes span −1 to 1 or include 0, with an explicit zero line;
  - bar charts start at 0;
  - no truncated axis exaggerates a difference.
- **Uncertainty** is shown wherever a sampling interval exists. Where only a point estimate exists (Fig 2B, Fig 3), the caption says so and gives the n.
- **Writeup:** each figure has alt text and a one-sentence takeaway in its title.

## Figures

| # | file | message (title) | data / source run | uncertainty shown | layer |
|---|---|---|---|---|---|
| 1 | `figures/fig1_framework.png` | Four things that are easy to confuse | schematic; sample sizes from join validation 20261121T135032Z | n/a | all four layers |
| 2 | `figures/fig2_tracking_vs_forty.png` | Tracking measures top speed reliably; for WR/DB it is not the same as the 40 | A: `forty_reliability/20261121T134306Z` (ICC(3,1) with 95 % CI, best-of-2 by Spearman–Brown). B: `phase3_screening/20261121T010253Z/predictor_structure` (1 − r²) | A: 95 % CI. B: point estimates (n given) | capacity |
| 3 | `figures/fig3_speed_demand.png` | Top speed is a deep-route tool | `phase3_screening/.../speed_demand` (game data only) | descriptive shares (plays given) | movement |
| 4 | `figures/fig4_translation.png` | Combine top speed shows up in game speed for WR and DL, much less for DB/OL | ρ_c: secondary run 20261122T015315Z `wald` block. Contrasts: H1-WR run 20261121T223645Z and the Holm family | Wald 95 % for ρ_c; registered bootstrap 95 % CIs for contrasts | capacity → movement |
| 5 | `figures/fig5_h2_separation.png` | Tracked top speed did not add detectable information about deep separation | H2 run 20261122T012339Z: REML bootstrap CIs (`reml_bootstrap`) and player-grouped CV (`cv_frozen`) | bootstrap 95 % CI; CV point estimates with the 90 % LB quoted in the text | capacity → performance |
| 6 | `figures/fig6_reliability.png` | Raw separation reflects use, not only the player | `phase3_screening/.../outcome_reliability` (outcome-blind); H2 reliability 0.44 in the caption | bootstrap 95 % CI (the short-route lower limit −0.66 is marked, not hidden) | performance vs deployment |
| 7 | `figures/fig7_dl_role_weight.png` | For DL, "combine speed" is largely body type and role | `secondary/.../dl_role_weight_diagnostics.json` (descriptive audit) and the registered H1-DL(b) result | mean ± SD (A); Wald 95 % (B, descriptive); registered bootstrap CI and Holm p in the title | capacity ↔ deployment |

## Tables (in the writeup text)

| # | content | source |
|---|---|---|
| T1 | analysed sample sizes per position (§2) | join validation + run outputs |
| T2 | evaluator guidance: finding, layer, practical use (§8) | registered results above |

## Deliberately not shown

These are excluded because they would add unregistered or misleading content:
- **player-level scatter plots of combine speed against game outcomes:** new associations, invites cherry-picking;
- **subgroup or season splits:** descriptive only, and could be read as findings;
- **BCa intervals:** a bootstrap artefact (registered diagnostic);
- **any DB coverage-performance chart:** no such outcome exists in the data.
