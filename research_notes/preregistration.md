# Pre-registration Protocol (Phase 3.5)

## Task-Conditioned Translation of Athletic Capacity: Connecting NFL Combine Sensor Tracking to Regular-Season Football Performance

| | |
|---|---|
| Version | 1.0 (frozen at the git commit that adds this file on branch `claude/jolly-ptolemy-7wx6do`) |
| Date | 2026-11-21 |
| Status | **Written before any combine measurement was joined to any NFL game outcome** |
| Companion documents | `statistical_model_specification.md` (mathematics), `power_analysis.md` (power), `notebooks/06_power_analysis.ipynb` |
| Code | `src/nfl_bdb/data/play_table.py` (contexts and covariates, frozen), `src/nfl_bdb/models/power.py`, `scripts/run_power_analysis.py` |

**What has and has not been seen (transparency statement):**
- **Seen:**
  - Combine measures among themselves (Phase 2–3).
  - Combine peak speed vs game *maximum speed over all plays*, by position (Phase 2, ρ 0.13–0.73). This is a speed-expression quantity, **not** a context-specific one.
  - Outcome-only nuisance statistics: reliabilities, variance components, play counts, deployment mix (Phases 3–3.5).
- **Not seen:**
  - Any context-specific capacity–speed association (the H1 estimand).
  - Any combine × separation association (H2).
  - Any OL context contrast (H5).
  - Any career-success outcome.

---

## 1. Research question
Does the association between combine-measured top speed and NFL regular-season game behaviour depend on how much the football task demands near-maximal speed? Does combine *tracking* add information about wide-receiver separation beyond the official 40-yard time?

All conclusions are **associational**. The protocol never interprets a coefficient as the causal effect of speed (§7).

## 2. Hypotheses
| ID | Statement | Status |
|---|---|---|
| **H1-WR** | For wide receivers, the standardised association between tracked combine peak speed and covariate-adjusted game speed is **larger on deep routes than on short routes**: Δ_WR = ρ_deep − ρ_short > 0 | **Primary, confirmatory** (test 1 of a fixed sequence) |
| **H2** | Among wide receivers, tracked combine peak speed is positively associated with covariate-adjusted **separation at pass forward on deep routes**, holding the official 40 time fixed: β_P > 0 | **Primary, confirmatory** (test 2 of the fixed sequence; tested only if H1-WR is rejected, §9) |
| H1-DB | Defensive backs: ρ_man − ρ_underneath-zone > 0 | Secondary (demoted from primary because of power, §11 and `power_analysis.md`) |
| H1-DL | Defensive linemen: (a) ρ_pass-rush − ρ_run > 0; (b) the pooled DL translation shrinks after alignment (EDGE / interior) and combine weight are adjusted for | Secondary |
| H1-TE | Tight ends: ρ_deep − ρ_short > 0 | Descriptive only (n = 17) |
| H1-global | Across the 11 position-context cells, standardised translation increases with the cross-fitted speed demand D: λ > 0 | Secondary, descriptive (11 cells, 5 positions) |
| **H5** | Offensive linemen as a comparison group: (a) the OL pass-block vs run contrast Δ_OL; (b) Δ_WR − Δ_OL; (c) OL overall translation vs the value predicted for OL by the demand model fitted without OL | **Secondary.** No direction is assumed for (a) or (c); (b) is predicted > 0 |

**Exploratory (labelled as such and never confirmatory):**
- spline shapes;
- pooled receivers (WR + TE);
- DB role interactions;
- OL pass-protection performance (peak pressure probability);
- anything not listed above.

## 3. Variables

### 3.1 Independent variables (combine)
| Symbol | Definition | Source |
|---|---|---|
| x_i (primary) | **Tracked 40 peak speed** (yd/s) = maximum, over the player's *valid* 40 attempts, of the attempt's maximum provided speed `s`. **Valid attempt:** mono-exponential fit R² > 0.95 and max `s` ≤ 12.5 yd/s | `combine_tracking`, Phase 2 pipeline (`scripts/run_real_capacity.py`) |
| x_i (sensitivity) | mean of attempt peaks over valid attempts | same |
| F_i | **official electronic 40-yard time** (s), sign-reversed for modelling (higher = faster) | `combine_results.forty` |
| Standardisation | within position, using **all combine participants** of that position (not only eligible players), so the scale does not depend on game eligibility | — |

**Not used as primary predictors:** combine A0, τ, S0 (unreliable or redundant; Phase 2), drill execution cost (invalid), and D99/C99 (not capacities).
**Used only in secondary models:** combine weight; the 10-yd split (H2 reference model M3).

### 3.2 Dependent variables (REG-season games)
| Test | Outcome | Definition |
|---|---|---|
| H1, H5 | y_ijc, **play maximum speed** (yd/s) | WR/TE: max provided `s` from the `ball_snap` frame to the `pass_forward`/`pass_shovel` frame (`vmax_prepass`). DB/DL/OL: max `s` from the snap to the end of the tracked play (`vmax_play`) |
| H1 (sensitivity) | upper speed expression | mean of the top 10% of play maxima per player-context (≥ 20 plays) |
| H2 | s_ij, **separation at pass forward** (yd) | `separation_at_pass_forward`. Defined on every route of a thrown pass (C/I/IN). Shown in Phase 3 to equal the tracked nearest-defender distance |
| H2 (descriptive) | short-route separation | same, on short routes |

### 3.3 Task contexts and speed demand
- **Route depth** (route-tree definition from `route_ran`, fixed in `play_table.py`):
  - **Deep:** GO, POST, CORNER, WHEEL.
  - **Short:** HITCH, SLANT, OUT, FLAT, SCREEN, ANGLE.
  - **Ambiguous, excluded from the contrast:** IN, CROSS. A dig and a shallow cross share a label.
  - The Phase 3 screening had put IN with short routes. This was changed **before any association**, on football grounds.
- **DB coverage role** (`coverage_assignment`):
  - **man** = MAN;
  - **deep zone** = DEEP_* or QUARTERS_*;
  - **underneath zone** = any other assignment except NO_ASSIGNMENT and PREVENT, which are excluded.
- **DL contexts:** pass rush (`player_get_off` non-null) vs run play (`pass_result == ""`).
- **OL contexts:** pass block (`pass_rushers_encountered` non-null) vs run play.
- **Operational definition of near-top-speed demand** D(p, c):
  1. For each player, compute **T_i**, the mean of that player's 5 largest REG play maxima (`vmax_play`) over all plays.
  2. For each player-context, compute the share of plays with `vmax_play` ≥ 0.90 · T_i.
  3. **D(p, c)** is the median of that share across eligible players of position p.
  4. **Cross-fitting:** players are split at random into two halves (seed 3503). D is estimated on one half and used with the other half's ρ estimates, then the halves are swapped and the two meta-regressions averaged. Using the same players for D and ρ would make the demand–translation relation partly mechanical.
  5. **Sensitivity definition:** the share of plays with `vmax_play` ≥ 7.5 yd/s. This is absolute and does not depend on player-specific maxima.
  6. **Phase 3 descriptive values** (non-cross-fitted, 90% threshold): WR deep 0.17 / short 0.01; TE deep 0.19 / short 0.03; DB man 0.07 / deep zone 0.03 / underneath 0.02; DL 0.03 / 0.01; OL 0.01 / 0.01.

### 3.4 Covariates (pre-snap or exogenous only; one-hot; missing → "NA" level)
| Model | Play-level covariates **w** | Other |
|---|---|---|
| H1 WR/TE | route_ran (nested in depth), team_coverage_type, down, distance bin (≤ 3 / 4–7 / ≥ 8), offense_formation, time-to-throw bin (< 2.5 / 2.5–3.5 / ≥ 3.5 s / none), season | NFL year a_ij; team-season random effect |
| H1 DB | context, team_coverage_type, lined_up_position, down, distance bin, time-to-throw bin, season | same |
| H1 DL / OL (H5) | context, lined_up_position, down, distance bin, offense_formation, season | same |
| H2 | route_ran, team_coverage_type, down, distance bin, offense_formation, in_motion_at_ball_snap, time-to-throw bin, season | same, plus F_i |

**Excluded by design (post-snap or outcome-like):**
- `pass_length`, `target`, `dropback_duration`;
- pressure variables;
- playing-time and exposure totals. These are potential colliders, and appear only in a sensitivity model.

**Time to throw** is borderline: it is partly caused by coverage. Primary models include it; a sensitivity model removes it.

## 4. Eligibility
**Seasons.**
- REG games of the 2023–2025 seasons, from each player's draft year onward. No season precedes a combine (verified: 0 rows).
- PRE excluded; POST used only as robustness.

**Plays.**
- Exclude the faulty game 2025101205 (plays 1289, 1314) and any player-play containing `s` > 12.5 yd/s.
- Exclude plays without a `ball_snap` frame and plays nullified by penalty (`play_nullified_by_penalty == "Y"`).
- WR/TE H1 plays must have a `route_ran` in the deep or short set.
- H2 plays must also have a separation value.

**Players** (counts at the time of freezing; the confirmatory run reports its own counts and any difference):
| Test | Inclusion | n |
|---|---|---|
| all | combine participant at that combine position; valid tracked 40; ≥ 100 primary REG opportunities (routes, coverage snaps, pass rushes, pass blocks) | WR 57, TE 18, DB 56, DL 53, OL 53 |
| H1 / H5 | additionally ≥ 20 plays in each of the two contrast contexts | WR 57, TE 17, DB 52, DL 53, OL 53 |
| H2 | additionally an official 40, ≥ 30 deep routes with separation, and ≥ 20 short | WR 57 |

**Threshold sensitivity:** 50 and 200 opportunities (WR 63 / 45; DB 62 / 50; DL 65 / 37; OL 56 / 48).

## 5. Missing data
| Missingness | Handling |
|---|---|
| No valid tracked 40 (92 of 510 players) | Excluded: the predictor is the object of study. The eligible vs ineligible comparison on official 40 and draft round is reported |
| Official 40 missing | Not applicable: every player with a tracked 40 has one |
| Outcome missing on a play (no tracking 0.3%; no pass-forward frame on sacks/scrambles) | The play is not an opportunity for that outcome. Never imputed |
| Covariate missing | "NA" category |
| Player with too few plays | Excluded by the eligibility rule (§4) |
| Context-specific missingness (e.g. few man snaps) | Eligibility rule. Mixed models use all plays of eligible players |

## 6. Primary estimands
- **H1:**
  - Δ_p = ρ_{p,h} − ρ_{p,l}.
  - ρ_{p,c} is the correlation between tracked peak speed and the player's *true* (noise-free, covariate-adjusted) mean play max speed in context c.
  - It is estimated from the bivariate mixed model in `statistical_model_specification.md` §1.
- **H2:**
  - β_P, the coefficient of standardised tracked peak speed in the deep-route separation mixed model that also contains the official 40 (spec §2).
  - Reported on the true-player-level scale (β_P*) and as a true-scale partial correlation.
- **H5:** Δ_OL; Δ_WR − Δ_OL; OL ρ vs the out-of-position prediction (spec §3).

## 7. Confounding and selection: what can and cannot be measured
Descriptives are outcome-free, computed in Phase 3.5.

| Threat | Measured? | Evidence | Handling | Residual risk |
|---|---|---|---|---|
| **Deployment / route assignment.** Faster WRs may be given more deep routes; faster DBs more man coverage | Partly: route and coverage mix are observed | WR deep share p10–p90 0.41–0.65; DB man share 0.09–0.43 | H1 is a *within-player* contrast, so each player is compared with himself across contexts and the assignment mix does not enter the estimand. The relation between combine speed and deployment share is reported as a diagnostic (exploratory) | Selection of *which* deep routes a player runs (e.g. clear-outs vs targeted) is not observed |
| **Route depth / route geometry** | Yes (label) | Short routes cap speed (1% of short-route plays reach 90% of top speed) | route_ran covariate; ceiling-robust sensitivity outcome | The label does not capture route stem length; IN/CROSS excluded |
| **Coverage type** | Yes | man vs zone separation medians 1.55 vs 3.15 yd | team_coverage_type covariate | Defender quality is not observed |
| **Team and season** (QB, scheme, play-caller) | Partly | 71 WR team-seasons, 36 with a single cohort WR; 14% of WRs changed teams | team-season random effect; season fixed effect; leave-one-team-out | When a team-season has one cohort player, team and player effects cannot be separated |
| **Player experience** | Yes | WR plays by NFL year: 9.5k / 7.2k / 3.2k (years 1/2/3) | a_ij covariate; class-specific sensitivity | Development trajectories may differ by athleticism |
| **Playing time / selection into the sample** | Partly | Eligibility ≥ 100 opportunities removes low-snap players | **No playing-time covariate in primary models**: playing time may be caused by both speed and performance (collider). Sensitivity: thresholds 50/200; inverse-probability-of-eligibility weights from pre-game variables only (position, draft class, combine weight, official 40); eligible vs ineligible comparison | Range restriction on speed among eligible players; unmeasured coach evaluations |
| **Position and role** | Yes | DB primary role: CB 25, slot 11, safety 20; DL: EDGE 25, interior 28 | Models by position. DB: lined_up_position covariate; DL: alignment in H1-DL(b) | Roles partly *result from* speed (role is a mediator); interpretation is stated per model |
| **Opportunity to reach maximum speed** | Yes (it is the moderator) | D(p, c) | It is the hypothesis, not a confounder. Cross-fitted to avoid circularity | Demand is itself a game-behaviour summary |
| **Exposure-dependent maxima** (Phase 2) | Yes | max speed grows with plays | Outcome is a play-level mean, not a player maximum; NFL year and season covariates | — |
| **Measurement error** | Partly | tracked peak r = 0.987; official 40 reliability unknown | Disattenuated ρ; EIV sensitivity for H2 (R_F 0.90 / 0.95 / 0.99) | Official-40 error can make peak speed look "incremental" (§10) |
| **Unmeasured:** opponent players (no tracking of non-cohort players), injuries, play-call intent, effort, ball location | No | — | Stated as limitations | — |

## 8. Statistical models (summary; full specification in the companion note)
- **H1 / H5:** a bivariate-context linear mixed model per position, with:
  - context-specific fixed slopes on x;
  - correlated player random effects across contexts;
  - a team-season random intercept;
  - context-specific residual variance.
  - The estimand is ρ_c = β_c sd(x) / √(β_c² var(x) + Σ_b,cc).
- **H2:** a linear mixed model of deep-route separation on F_i and x_i, with play covariates, NFL year, a player random intercept and a team-season random intercept.
- **Nonlinearity:** natural cubic splines (3 df), as a secondary analysis only.
- **No deep learning.** n ≈ 55 independent players per position.

## 9. Multiple testing
- **Primary family:** {H1-WR, H2}, controlled by a **fixed-sequence (hierarchical) procedure** at FWER α = 0.05.
  - H1-WR is tested at 0.05. Only if it is rejected is H2 tested at 0.05.
  - **Rationale:** H2's deep-route mechanism presupposes H1's task conditioning. H1-WR is also far better powered.
  - **Sensitivity:** Holm over three tests (H1-WR, H1-DB, H2), with a worst step of α = 0.0167, reported alongside.
- **Secondary family:** {H1-DB, H1-DL(a), H1-DL(b), H5(b)} under Holm at α = 0.05. H5(a), H5(c), H1-global and H1-TE are estimation only.
- **Exploratory analyses:** unadjusted, always labelled, never in the abstract as findings.
- **Directionality:** all tests use two-sided (1 − α) CIs. A hypothesis is *supported* only if the CI excludes 0 **in the predicted direction**. The nominal one-sided size is therefore α/2.

## 10. Confidence intervals and effect sizes
- **CIs:**
  - 95% **player-cluster bootstrap** percentile intervals (B = 2,000; BCa also reported).
  - Model-based Wald intervals as a check.
  - 90% intervals for the decision bands in §12.
- **Bootstrap coverage:** simulated coverage of the percentile interval at n ≈ 55 is 0.92–0.94 (`power_analysis.md`). This slight undercoverage is reported with the results.
- **Effect sizes, always reported with CIs:**
  - **H1:** ρ_h, ρ_l and Δ (correlation units). Also the raw slopes β_h, β_l, in yd/s of game speed per 0.25 yd/s of combine peak speed (≈ 1 within-position SD, ≈ 0.5 mph).
  - **H2:** β_P in yd of separation per 0.25 yd/s of peak speed at a fixed 40; the true-scale partial correlation; ΔR²_CV; ΔRMSE; ΔSpearman.
  - **H5:** Δ_OL, Δ_WR − Δ_OL, and the OL prediction residual.
  - Raw counts: players, plays and team-seasons per estimate.

## 11. Power (summary of `power_analysis.md`)
Simulation-based. Uses the actual eligible n, play counts, reliabilities, within- and between-player variance and cross-context correlation, with a player-cluster bootstrap test.

**Minimum detectable effect, 80% power, α = 0.05, directional:**
- **H1-WR:** Δ ≈ **0.27–0.33** (0.29–0.37 under Holm m = 3).
- **H1-DB:** 0.40 at best; not reached for ρ_low ≤ 0.3. Hence its demotion.
- **H1-DL:** ≈ 0.32.
- **H5(a) OL:** ≈ 0.36. **H5(b):** Δ_WR − Δ_OL ≈ 0.53.
- **H2:** true-scale partial correlation ≈ **0.6**. Power for a partial correlation of 0.3 is about 0.3.

**Players, not plays, limit power:** five times more plays per player raises H1-WR power at Δ = 0.2 from 0.32 to 0.47 (Holm level), while roughly doubling the number of players (to 120) raises it to 0.65.

## 12. Decision criteria (fixed now)
**SESOI** (smallest effect size of interest):
- H1: Δ = 0.15. Below this, task conditioning would not change how a scout reads combine speed.
- H2: a true-scale partial correlation of 0.10 and ΔR²_CV = 0.02.

| Hypothesis | Supported | Falsified (evidence against a meaningful effect) | Inconclusive |
|---|---|---|---|
| **H1-WR** | Δ̂ > 0 and the 95% CI excludes 0, **and** the season-forward 2025 estimate has the same sign (its CI need not exclude 0) | 90% CI upper bound < 0.15 (equivalence-type), **or** 95% CI entirely < 0 (contradicted) | anything else; reported as "compatible with Δ from L to U" |
| **H2** (only if H1-WR is supported) | β̂_P > 0 and its 95% CI excludes 0; **and** ΔR²_CV ≥ 0.02 with a 90% bootstrap lower bound > 0; **and** β̂_P > 0 survives the R_F = 0.95 errors-in-variables refit | 90% CI of the true-scale partial correlation entirely < 0.10 | anything else. **This is the expected outcome.** At n = 57, the 95% CI half-width of the standardised β_P is ≈ 0.66 |
| **H2 if H1-WR is not supported** | not tested confirmatorily; reported as estimation | — | — |
| **H1-DB / H1-DL(a)** (secondary) | Holm-adjusted CI excludes 0 in the predicted direction | 90% CI upper bound < 0.15 | otherwise |
| **H1-DL(b)** | the pooled-minus-adjusted ρ difference > 0, with the 95% CI excluding 0 | the CI includes 0 and its upper bound < 0.10 | otherwise |
| **H5** | **(a)** "consistent with demand model" if the 90% CI of Δ_OL lies within ±0.15. **(c)** "consistent" if the observed OL ρ lies inside the 90% out-of-position prediction interval; "informative departure" if it lies above. **(b)** supported if the CI excludes 0 in the positive direction | (b) falsified if the 90% CI upper bound < 0 | expected for (b) given the MDE of ≈ 0.53. **(a)** cannot reach "consistent" at n = 53: the 90% CI half-width is ≈ 0.24 > 0.15, so (a) is reported as estimation |

**Interpretation of H2 support:**
- If β̂_P > 0 survives only at R_F = 0.99, the claim is limited to "tracked peak speed is a more precise speed measurement than the official 40".
- It is **not** "a new athletic dimension".

**Meaningful incremental predictive value (H2)** requires all of:
- ΔR²_CV ≥ 0.02 on held-out players (player-grouped 10-fold × 20);
- the 90% bootstrap lower bound of ΔR²_CV > 0;
- ΔRMSE ≤ 0 in the season-forward 2025 evaluation.

A statistically significant β_P **without** these is reported as "an association without a demonstrated predictive gain".

**If power is insufficient** (already known for H1-DB, H2 and H5(b)):
1. Thresholds, α and models are **not** changed after seeing data, and tests are not added until something is significant.
2. Underpowered tests are reported as **estimation**: point estimate, 95% CI, and the largest effect the CI excludes. The phrase "no effect" is never used for an inconclusive result.
3. The pre-registered precision statement is reported next to every result. Example: "at n = 57, effects of Δ < 0.27 could not reliably be detected".
4. Additional players can come only from data outside this protocol (e.g. a future season). Any such extension is a new, separately registered analysis.
5. A **Bayesian sensitivity analysis** is reported as a secondary summary for H1-WR and H2. It uses a skeptical prior, Δ ~ N(0, 0.15²) and β_P* ~ N(0, 0.2²), and reports posterior P(effect > SESOI). It never replaces the frequentist decision.

## 13. Validation strategy
- **Player-grouped CV:** 10 folds by player, repeated 20 times, stratified by draft class. Used for all predictive comparisons:
  - demand-conditioned model vs one slope per position vs one slope per position-context;
  - M1 (40) vs M2 (40 + peak).
  - Residualisation, demand and shrinkage are re-estimated inside the training folds.
- **Season-forward:** estimate on the 2023 + 2024 REG seasons and evaluate on the 2025 REG season. This is a replication of the sign for the H1/H2 estimands and a held-out prediction for H2.
- **New players:** the 2025 draft class, reported descriptively only.
- **Robustness grid:**
  - opportunity thresholds 50 / 100 / 200;
  - without time-to-throw;
  - REG + POST;
  - leave-one-team-out;
  - ceiling-robust outcome; splines;
  - mean-of-attempts peak speed;
  - absolute-threshold demand;
  - IN/CROSS assigned to short (H1-WR);
  - eligibility weights.
- **Negative controls:**
  - context labels permuted within player (expected Δ ≈ 0);
  - WR short-route β_P (descriptive);
  - the OL contrast (H5a).

## 14. Firewall and execution order
1. Commit this protocol, the model specification and the power analysis.
2. Implement the confirmatory pipeline on **simulated data first**: the data-generating process from `power.py`, with planted Δ and β_P, to verify recovery and coverage.
3. **Only then** run the single join of combine predictors to game outcomes. Produce primary results exactly as specified, then secondary results, then exploratory results.
4. Record the commit hash of the code that produced each result in `experiments/`.

## 15. Deviations log
Any change after freezing is listed here with date, reason, and whether it was made before or after outcome data were seen.

| Date | Change | Before or after seeing outcome associations |
|---|---|---|
| — | — | — |
