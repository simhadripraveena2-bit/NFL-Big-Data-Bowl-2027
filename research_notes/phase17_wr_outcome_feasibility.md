# Phase 17: WR route-launch outcome-study feasibility and power audit

**Status:** feasibility and power only. **No new combine × outcome association was computed.**
**Verdict:** NO-GO for a confirmatory study on the current data; CONDITIONAL GO only for an optional, pre-registered, estimation-only exploratory analysis (§9).

## Scope and firewall

What this phase read:
- eligibility inputs: combine identifiers, official 10-yd and 40 presence, and Phase 16 valid-route counts;
- per-player **counts** of REG thrown routes with a non-null `separation_at_pass_forward` (a null flag only), plus team-season counts;
- the `nfl_id` / eligibility-flag columns of the registered H1/H2 eligibility files, used to measure cohort overlap;
- previously published aggregate reports (Phase 3, Phase 3.5, Phase 4, H2, Phase 16).

What this phase did **not** do:
- no separation, target or other outcome value was read, aggregated or inspected;
- no outcome model was fitted;
- no frozen file and no Phase 11–16 result was changed;
- the study design was not chosen from any outcome association.

Code and outputs:
- `src/nfl_bdb/simulation/outcome_power.py` (simulator);
- `scripts/run_phase17_power.py`;
- `tests/test_phase17_power.py`;
- run `experiments/phase17/20261125T122831Z/` (`power_grid.csv`, `mde_summary.csv`, `meta.json`; git-ignored). Seed 1717, 2,000 replicates per cell.

## 1. Research question

> Does WR route-launch acceleration (Phase 16 frozen measure) carry information about context-adjusted separation at pass forward, beyond the official 10-yard split and 40-yard time?

This is a predictive, incremental-information question. It is **not causal**, and the launch score is **not a new capacity**. Phase 16 established it only as a reliable, relative, athlete-level drill score: −12% magnitude bias, so it is used as a rank or z-score only.

## 2. Eligible population (Task A)

| step | WR |
|---|---|
| Combine WR (2023–2025 draft classes) | 107 |
| ≥ 1 valid Phase 16 launch route | 107 |
| ≥ 8 valid launch routes | 101 |
| plus official 10-yd split **and** 40 (9 missing) | **92** (pre-selection population) |
| any REG thrown route | 70 |
| ≥ 50 separation-defined routes (sensitivity) | 59 (draft 2023 / 2024 / 2025: 24 / 22 / 13) |
| **≥ 100 separation-defined routes (main)** | **54** (24 / 18 / 12) |
| ≥ 200 separation-defined routes (sensitivity) | 40 (18 / 14 / 8) |

For the main cohort of 54:
- separation-defined thrown routes per player: min 120, median 385, max 1,300. Every thrown route by an eligible player has a defined separation (coverage share 1.0).
- team-seasons per player: 1 / 2 / 3 / 4 for 14 / 21 / 17 / 2 players; 69 distinct team-seasons.
- launch routes per athlete: 9 / 10 / 11 / 12 for 1 / 7 / 22 / 24 athletes.

Attrition: 38 of the 92 (41%) lack enough NFL exposure. This drop is outcome-relevant selection, because playing time is earned (modelled in §6 as λ).

**Cohort reuse.** 53 of the 54 (and 39 of the 40 at the 200 threshold) are in the registered H1-WR and H2 eligible sets (57 players each). Separation for this cohort has therefore already been analysed: H2 found no information in combine peak speed beyond the 40. A new study would not be an independent sample (§7, §8).

## 3. Reconciling the separation reliabilities (Task B)

| source | value | estimator | routes | population | team-season variance |
|---|---|---|---|---|---|
| Phase 3 screening | 0.61 (all), 0.61 (deep), 0.22 (short) | Spearman split-half on **alternating games within player**, Spearman–Brown corrected; play-level OLS residual on route, coverage, down, ytg, formation, motion, ttt, season | all / deep / short | all cohort WR with ≥ min_opp/2 per half | **counted as player signal**: both halves share the same team-seasons |
| Phase 3.5 power | 0.45 deep (0.65 short) | moment variance ratio var_between / var(mean): 0.0216 vs 1.73² / 140 | deep | 57 tracked-40 WR, frozen H1 covariates | not separated |
| Phase 4 / H2 | 0.44 (0.43) | REML route-level model with a team-season random effect: s2b 0.0159, s2_team 0.0175, residual 2.98 | deep | 57 H2 WR | **separated out** (s2_team ≈ 1.1 × s2b) |

**Resolution (partly resolved).** The main deep-route gap is explained by team-season variance and the estimator.
- Using the H2 components at the Phase 3.5 median exposure (n = 140): (s2b + s2_team) / (s2b + s2_team + 2.98/140) = 0.0334 / 0.0547 = **0.61**, which is exactly the Phase 3 value. The player-only share is lower.
- So 0.61 is a "player plus team-season" reliability; 0.44–0.45 is the reliability of the player component.
- For an incremental player-attribute question, the player-only reliability is the relevant one.

**Unresolved.** The short-route values disagree in the opposite direction (Phase 3 0.22 vs Phase 3.5 0.65). The likely cause is the route-type residualisation in Phase 3 versus none within short in Phase 3.5, but reports and code do not settle it.

**All-route value for the proposed study.** It has never been estimated on the player-only scale. Two bounds:
- With the deep-route components at the cohort's median exposure (385 all routes, within-SD 1.85), player-only reliability ≈ 0.0159 / (0.0159 + 0.0175/2 + 3.42/385) ≈ **0.48**.
- The **ceiling** with a team-season variance ratio τ = 1.1 and this cohort's team-season counts is mean(1 / (1 + τ/k)) = **0.63**, however many routes are observed.

Plausible range carried into §6: **R_y ∈ {0.44, 0.53, 0.61}**. 0.70 is simulated only without team variance (τ = 0); with τ = 1.1 it is infeasible.

## 4. Predictor uncertainty

- Phase 16 frozen launch: athlete mean of route × year cell-z scores (p95 of a_t over 1.0 s from onset, SG7).
- G-study components (cell z): s2p 0.182, s2pr 0.316, s2e 0.510.
- **G(8) = 0.64** (primary: minimum eligible route count); **G(10) = 0.69** (sensitivity); per-athlete **actual** G(n_routes) (cohort mean ≈ 0.71).
- Official 10-yd and 40 reliability R_F = 0.90 (sensitivity 0.80). The admissible WR range from D3 is R_F ≥ 0.70; the 40's within-WR test-retest is 0.94.
- Launch is nearly independent of the official sprint times (Phase 16: |r| ≤ 0.15; 11% of athlete variance). The simulation uses corr(T, F10) = −0.20, corr(T, F40) = −0.15, corr(F10, F40) = 0.85.

## 5. Model and estimand (Task C)

| element | specification |
|---|---|
| unit of analysis | player (n = 54 main; 59 / 40 sensitivity) |
| predictor | Phase 16 frozen launch score: route × year cell z, athlete mean over ≥ 8 valid routes; relative scale only; standardised within the cohort |
| outcome | context-adjusted separation at pass forward on **all REG thrown routes**, targeted or not; IN/CROSS included (no depth split); route-level residual on the H2 frozen context set (route_ran, coverage type, down, ytg bin, formation, motion, ttt bin, season), with the context model fitted on all cohort WR routes; player mean of residuals |
| population | §2: WR with ≥ 8 valid launch routes, official 10-yd split and 40, ≥ 100 separation-defined REG routes |
| covariates | official 10-yd split and 40 (standardised); draft-year indicators as registered sensitivity |
| primary coefficient | standardised β (equivalently the partial correlation) of launch given the 10-yd split and 40; two-sided α = 0.05 |
| team-season clustering | primary: player-level OLS with HC3 SE (team-season variance enters the player-mean error); sensitivity: route-level REML with player and team-season random effects (H2 engine). Team-season fixed effects are weakly identified with 1–4 team-seasons per player |
| player-level uncertainty | HC3 + player-cluster bootstrap; report the observed-scale partial r and an EIV-disattenuated version r / √(R_x R_y) with R_x, R_y declared in advance |
| interpretation | incremental predictive association, not causal; no capacity claim; a null result does not show that launch is irrelevant to separation |

## 6. Power (Task D)

**Simulator** (`outcome_power.simulate_cell`):
- Latent model: (T, F10, F40) for the 92 pre-selection players; true separation ability b = g·F40 + ρ·T⊥ + e, so ρ is the true partial correlation.
- Selection: top 54 on E = λb + noise, with larger exposure going to higher E when λ > 0.
- Observed y = b + team-season noise (τ·s2b/k_i) + sampling noise (1.85²/n_i), using the real exposure and team-season counts. s2b is solved for the mean reliability R_y.
- Launch observed with R_x; sprint times with R_F.
- Analysis: OLS + HC3, t-test on df n − 4.

Grid: R_x {0.64, 0.69, actual} × R_y {0.44, 0.53, 0.61, 0.70} × g {0, 0.3} × λ {0, 0.3} × τ {0, 1.1} × ρ {0, …, 0.7}.

**Validation against published H2 power.** The simulator was configured as H2: n 57, one covariate, R_F 0.95, R_x 0.987, implied R_y 0.50, directional test.
- Power at ρ = 0.3: **0.26** (0.28 with g = 0.3); MDE **0.61** (0.60).
- Published Phase 3.5 / Phase 4 values: power 0.26–0.30 at 0.3, MDE 0.58–0.66, size 0.020–0.039.
- **The simulator reproduces the registered power calculations.**

**Primary scenario** (n 54, R_x = G(8) 0.64, τ 1.1, g 0, λ 0, R_F 0.90; two-sided):

| R_y | size | power ρ=0.2 | power ρ=0.3 | power ρ=0.5 | power ρ=0.7 | MDE (80%) | mean r̂ at ρ=0.3 | disattenuated mean (cov.) at 0.3 |
|---|---|---|---|---|---|---|---|---|
| 0.44 | 0.056 | 0.11 | 0.18 | 0.40 | 0.69 | **> 0.70** | 0.15 | 0.28 (0.94) |
| 0.53 | 0.048 | 0.12 | 0.21 | 0.49 | 0.81 | **0.69** | 0.16 | 0.27 (0.95) |
| 0.61 | 0.042 | 0.13 | 0.23 | 0.57 | 0.87 | **0.66** | 0.17 | 0.28 (0.95) |
| 0.70 | — | infeasible with τ = 1.1 (ceiling 0.63) | | | | (τ = 0: 0.60) | | |

**MDE across all nuisance settings** (threshold 100; R_y 0.53 / 0.61 / 0.70 at τ = 0):
- R_x 0.64: 0.69 or not reached / 0.66–0.69 / 0.60–0.64.
- R_x 0.69: 0.68–0.70 or not reached / 0.62–0.67 / 0.59–0.61.
- actual G: 0.67–0.70 or not reached / 0.61–0.66 / 0.58–0.59.
- At R_y = 0.44, no setting reaches 80% power by ρ = 0.7.
- Power at ρ = 0.3 is **0.14–0.29** in every cell.

**Other properties:**
- **Type-I error:** 0.036–0.063 over all feasible null cells (mean 0.046; Monte Carlo SE 0.005 per cell). HC3 is approximately nominal.
- **Bias:** the observed partial r is attenuated by about 50% (mean r̂ 0.15–0.17 at true 0.3; 0.24–0.29 at 0.5). Naive 95% CI coverage falls to 0.81–0.85 at ρ = 0.3 and 0.43–0.60 at ρ = 0.5. The disattenuated estimate is approximately unbiased with coverage 0.94–0.96 when R_x and R_y are correct.
- **Selection** (λ = 0.3, g = 0.3) leaves size nominal (0.050) but biases the disattenuated estimate downward (0.25 at true 0.3, 0.34 at 0.4) and lowers power slightly.
- **Sensitivity:**
  - threshold 50 (n 59): power at 0.3 is 0.17 / 0.27 (R_y 0.44 / 0.61); MDE 0.61 at R_y 0.61.
  - threshold 200 (n 40): 0.14 / 0.17; MDE not reached.
  - R_F 0.80 with g 0.3: MDE 0.67 (R_y 0.61). Residual 40-yd confounding does not inflate size here because corr(T, F) is small.

**Number of players needed** (R_y 0.61, R_x 0.64, τ 1.1):

| players | power ρ=0.1 | power ρ=0.2 | power ρ=0.3 |
|---|---|---|---|
| 54 | 0.06 | 0.12 | 0.22 |
| 100 | 0.09 | 0.22 | 0.42 |
| 150 | 0.11 | 0.31 | 0.59 |
| 250 | 0.16 | 0.47 | **0.82** |
| 400 | 0.22 | 0.68 | 0.95 |

Players, not routes, limit power:
- Cohort exposure is already high (median 385 routes), and the team-season ceiling caps R_y at 0.63.
- Even with R_y = 1, attenuation √0.64 = 0.8 leaves an observed partial of about 0.24 at true 0.3.

**Is a detectable effect plausible?** The study is powered only for true partial r ≈ 0.65 (observed ≈ 0.33). A combine drill score would have to explain about 40% of the residual true between-player variance in separation that the 10-yd split and 40 do not explain. For context:
- H2 found combine peak speed adds nothing beyond the 40 (β −0.020 yd/SD);
- between-player separation variance is small (SD 0.13 yd) compared with team-season variance.

An effect that large is implausible a priori.

## 7. Selection and confounding

- **Cohort reuse:** 53 of 54 players were analysed in H1-WR / H2 on the same separation variable. Their aggregate separation results (H2 null; dRMSE ≈ 0) are known to the analysts, so a new test is not blind to the outcome distribution of this cohort.
  - The launch predictor itself was never joined to outcomes, so the specific association remains untested.
  - Any p-value would still sit in a garden of forking paths over the same 54 players: after the H2 null, this would be the second combine predictor tested on the same outcome. The registered H2 family did not include it.
- **Exposure selection:** 41% of the pre-selection WR are excluded for lack of exposure. Playing time depends on ability (and plausibly on separation), so the eligible cohort is range-restricted. Simulated λ = 0.3 attenuates the disattenuated estimate by about 15%.
- **Confounding of separation by context:** team-season, scheme and quarterback effects are as large as the player variance (τ ≈ 1.1). The cohort-only tracking has no defenders or ball, so there is no defender-quality adjustment.
- **Draft-year composition:** 24 / 18 / 12 by draft class. Rookies (2025) have one season at most, so exposure and team-season counts depend on draft year. Draft-year indicators are a necessary sensitivity, and they cost another 2 df.
- **Predictor scale:** relative score only (−12% bias). The route × year standardisation removes layout drift but also removes any true year-level difference.

## 8. Classification (Task E)

| option | assessment |
|---|---|
| confirmatory | **No.** Power at plausible effects (ρ ≤ 0.3) is 0.14–0.29; MDE 0.61–0.70 or not reached; cohort reused from H1/H2; no independent replication sample |
| pre-registered secondary / estimation | possible only as an **estimation-only** analysis with a pre-declared expectation of "inconclusive". Value: a confidence interval for one more drill measure, with an expected 95% CI half-width of about ±0.27 on the observed partial-r scale (SD r̂ 0.13–0.14) |
| exploratory | appropriate label if run at all; must be reported with the disattenuated interval and the cohort-reuse caveat |
| not worthwhile | defensible: the expected result is uninformative in either direction |

**External data needed for a confirmatory test.** About 250 eligible WR, i.e. 80% power at true partial 0.3. Current yield is about 18 eligible WR per draft class, so this means:
- roughly **11–14 combine classes** with WR route-drill tracking, each followed by ≥ 1 NFL season of thrown-route tracking (or pooled across several data releases); and
- **league-wide tracking** (all 22 players + ball) to model defender assignment and quarterback / team effects. That would lower τ and raise the player-only ceiling on R_y. More routes per current player would not help.

A smaller but useful step: future combine classes alone could give an **independent replication sample** of about 50–60 WR per 3 classes, avoiding cohort reuse even though it would still be underpowered.

## 9. Decision

**NO-GO** for a confirmatory, or any hypothesis-testing, WR route-launch × separation study on the current data:
- MDE true partial r 0.61–0.70 (not reached at the H2 reliability 0.44); power at ρ = 0.3 is 0.14–0.29;
- 53 / 54 players were reused from H1/H2;
- separation reliability is capped at 0.63 by team-season variance.

**CONDITIONAL GO** for an optional exploratory, estimation-only analysis, and only if the lead considers a single wide interval worth reporting. It would need all of the following:
- a new pre-registration written before any join, with the §5 estimand, R_x = G(8) and R_y bounds declared in advance, HC3 + REML sensitivity, and "inconclusive" as the expected label;
- reporting as exploratory, with the cohort-reuse caveat;
- no further subgroups or route-depth splits.

The recommended alternative is to keep launch as a validated combine measurement result (Phase 16), and to defer outcome validation until an independent cohort or league-wide tracking is available.

No pre-registration was drafted; no outcome analysis was run. **Awaiting lead review.**
