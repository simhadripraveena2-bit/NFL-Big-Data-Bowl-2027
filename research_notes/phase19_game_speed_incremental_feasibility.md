# Phase 19: does Combine tracking add information beyond the official 40 for NFL game speed? (feasibility only)

**Status:** feasibility and synthetic power study only.
- **No Combine-predictor × game-outcome association was computed, and no model was fitted to real joined outcome data.**
- Pre-registration v1.0, every registered H1/H2 result and every frozen file are unchanged (§9).

**Decision: NO-GO** under the criteria committed before the simulation (`configs/phase19_feasibility_criteria.json`, commit 4ca1678):
- central power is 0.474 against a required ≥ 0.50;
- the "distinct construct" reading is not identifiable from these data.

**Recommendation:** stop. Do not run the real analysis on the existing cohort.

**This is a proposed exploratory question, not a registered one.** It is not H2:
- H2 (registered, secondary, estimation) asked whether peak speed adds to the 40 for WR **deep-route separation**, and found β_P −0.020 yd/SD [−0.101, 0.063].
- This phase asks the same incremental question for **game speed**, which is the H1 outcome.

**Code and outputs:**
- `src/nfl_bdb/simulation/game_speed_incremental.py`;
- `scripts/run_phase19_power.py`;
- `tests/test_phase19_game_speed.py`;
- run `experiments/phase19/20261126T011739Z/` (git-ignored; seed 1919, 2,000 replicates per cell, ~100 s).

## 1. Research question

> Among WRs in the registered H1 population, does tracked Combine peak speed improve out-of-sample prediction of context-adjusted regular-season game speed beyond the official 40-yard time?

Candidate models:
- **M1:** official 40 only;
- **M2:** tracked peak only;
- **M3:** 40 + peak.

The primary contrast is M3 vs M1.

**Outcome.** The H1 outcome, unchanged. For each play, the maximum speed from snap to pass forward, adjusted by the registered H1 REML covariates (context-specific route, coverage, down, distance, formation, time-to-throw, season, NFL year), with a team-season random effect. Contexts are the frozen deep / short route sets. The player's **composite** level is the equal-weight mean of the deep and short player effects. A single composite avoids re-opening the H1 deep–short contrast.

## 2. Existing data availability (Task A)

| item | value | source |
|---|---|---|
| registered H1-WR players | **57**; all 57 have both an official 40 and a valid tracked peak | `predictors.parquet`, `eligibility_h1_WR.parquet` (Combine fields and flags only) |
| valid tracked-40 attempts | 2 for 47 players, 1 for 10 | Combine only |
| plays (deep / short) | 9,961 / 9,999; 71 team-seasons | design counts of `h1_WR.parquet` (no outcome column read) |
| draft classes | 2023 / 2024 / 2025 = 24 / 19 / 14 | Combine only |
| corr(tracked peak, official 40) | **−0.851** within the 57 (−0.814 over all 94 tracked WR) | Combine only |
| predictor SDs in the 57 | peak 0.301 yd/s; 40 0.090 s | Combine only |

**Other positions** were assessed from counts and Combine-only correlations, and were **not simulated** (no automatic expansion):

| position | H1-eligible with both | corr(peak, 40) | assessment |
|---|---|---|---|
| DL | 53 | −0.978 | no defensible design: one dimension (CLAUDE.md), R_F lower bound ≈ 0.978² / 0.99 ≈ 0.97, no room for incremental information |
| OL | 53 | −0.883 | game "speed" in pass blocking is not a speed-expression task (H5 role); weak transfer already known (Phase 2) |
| DB | 52 | −0.780 | contexts negatively correlated (Phase 3.5 / 4); peak ↔ game max ρ 0.13 already seen (Phase 2) |
| TE | 17 | −0.916 | too few players |

**What is already known about these predictors and this outcome.** This question is not fully outcome-blind.
- The **M2 marginal association** has been seen several times:
  - H1-WR: ρ deep 0.576 / short 0.486;
  - Phase 2: WR peak ↔ game max ρ 0.585.
- **M1 (40 × game speed) and M3 have never been computed.** A search of all scripts found no fit of the official 40 against any game-speed outcome.
- Given corr(P, F) = 0.851 and ρ(P, Y) ≈ 0.53, the unseen ρ(F, Y) is only weakly constrained, to about [0.01, 0.90].
- The simulation is **not** calibrated to any of these associations (§5).

**Reuse of frozen components** without modification. All of these are library calls with a new outcome, and none needs an edit:
- `confirmatory.h1_reml` accepts an arbitrary fixed-effect design (`Xw` can carry ctx × F columns, with `x_player` = peak);
- `confirmatory.h2_reml` is the single-context M3 fit;
- `wls_two_stage` (player-level WLS + HC3);
- `eiv_two_stage` (regression calibration);
- `player_folds` / `h2_cv` (player-grouped CV of M1 vs F + x).

The simulator re-implements `wls_two_stage` and `eiv_two_stage` in batched form. Tests assert equality with the frozen functions to 1e-10.

## 3. Predictor and outcome reliability

| quantity | value | status |
|---|---|---|
| tracked peak, single attempt, within WR | 0.889 (0.82–0.94) | measured (D3, Combine only) |
| tracked peak, best of 2 (registered x) | **0.94** (Spearman–Brown); 0.89 for the 10 single-attempt players; mean 0.931 | derived (D3) |
| official 40, R_F | **not identified**: no per-attempt official times; the tracked 0–40 is not the electronic 40 | unknown |
| R_F lower bound (true peak ≡ true 40 speed) | r² / R_P = 0.851² / 0.931 = **0.78** (0.70 over all 94 WR) | derived |
| R_F under a stronger assumption (flying split) | ≈ 0.86 (all WR) | context only (D3) |
| outcome-only between-player Σ_b, deep / short (cov) | 0.0616 / 0.0849 (0.0557; r 0.77) | Phase 4 outcome-only REML |
| team-season variance; residuals deep / short | 0.0104; 0.761 / 1.455 | Phase 4 outcome-only REML |
| composite true SD | 0.254 yd/s | derived |
| **reliability of the composite player level** | **0.85** including team-season noise; 0.93 sampling only | derived (real play counts and team-season structure) |

**For comparison:**
- deep-route separation (H2): 0.44;
- H1 player-context means: deep 0.85 / short 0.82.

**Outcome reliability is not the binding constraint here.** The binding constraint is the **predictor collinearity** together with n = 57. With true corr(peak, 40) ρ* = 0.89–0.96 over the admissible R_F, only 8–22% of true peak variance is independent of the true 40.

## 4. Estimand (Task B)

**Unit:** the player (57). All folds and resamples are by player; plays of one player are never split across training and test.

| estimand | definition | estimable here? |
|---|---|---|
| **E1 incremental association** | observed-scale coefficient β_P of standardised tracked peak in the player-level regression of the composite level on standardised official 40 + peak (WLS, HC3) | yes, with imprecision (§6) |
| **E2 incremental out-of-sample prediction** | ΔR²_CV = R²(M3) − R²(M1) on held-out **players'** shrunken composite levels (10-fold × 5, player-grouped; training-fold shrinkage as in the frozen `h2_cv`) | yes, but unstable (§6) |
| **E3 improved measurement precision** | the part of E1 that exists even if peak and 40 measure the **same** speed, because the official 40 is measured with more error (R_F < R_P) | not separable from E4 |
| **E4 distinct athletic construct** | true partial correlation π of true peak with the true composite level, given the true 40 | **not identified**: requires R_F, which is unknown in [0.78, 1] |

Key point: **E1 ≠ E4.** The data identify only the observed-scale E1/E2. Any non-zero E1 can be produced either by a distinct construct (π > 0) or by pure measurement precision (π = 0, R_F near 0.78). The two worlds give the same observed predictor distribution (corr −0.851), so they cannot be told apart. A positive E1 would therefore support "the tracked peak is a more informative measurement", **not** "the tracked peak captures a different capacity". No causal reading is possible.

## 5. Synthetic design (Task C)

The criteria were committed before any simulation output existed (4ca1678).

**Latent model:**
- standardised true scores S_F (true 40 speed) and S_P (true peak), corr ρ* = 0.851 / √(R_F · 0.931);
- true composite L = a·S_F + π√(1 − a²)·S_P⊥ + noise, so π is the true partial of S_P given S_F;
- deep / short effects reproduce the outcome-only Σ_b exactly.

**Observed data:**
- F_o and P_o carry error with R_F (grid) and per-player R_P (0.94 / 0.89);
- player × context means use the **real** play counts and **real** player × team-season weights (71 team-seasons, team variance 0.0104) and the outcome-only residual variances.

**Effects are a grid, never calibrated to an observed association:**
- validity of the true 40, a ∈ {0.3, 0.5, 0.7};
- π ∈ {0, 0.1, …, 0.5};
- R_F ∈ {0.78 (single-construct world, π undefined → 0), 0.85, 0.90, 0.95, 0.99}.

**Analyses per dataset:**
- E1: WLS two-stage + HC3, two-sided t test, df 54;
- E2: player-grouped CV;
- E4: EIV calibration with the true R_F and with the registered H2 value 0.95.

**Sample-size scaling:** n ∈ {57, 100, 200, 400}, by resampling the real player designs.

**Pre-specified criteria** (config):

| criterion | rule |
|---|---|
| C1 validity | size at π = 0, R_F = 0.99 ≤ 0.075 for every a; HC3 coverage of the population observed-scale coefficient ≥ 0.92 in every cell |
| C2 central power | power at π = 0.3, R_F = 0.90, a = 0.5 |
| C3 robust power | minimum power at π = 0.3 over R_F ∈ {0.85, …, 0.99}, a ∈ {0.3, 0.5, 0.7} |
| C4 construct identifiability | rejection rate at π = 0 for R_F ∈ {0.78, 0.85} ≤ 0.10 |
| C5 prediction | at π = 0.3 central: mean ΔR²_CV ≥ 0.02 and P(ΔR²_CV > 0) ≥ 0.80 |

- **GO:** C1 and C2 ≥ 0.80 and C3 ≥ 0.70 and C4 and C5.
- **CONDITIONAL GO:** C1 and C2 ≥ 0.50.
- **NO-GO:** C1 fails, or C2 < 0.50.

## 6. Simulation results

**Power of E1** (two-sided α 0.05; Monte Carlo SE ≤ 0.011):

| R_F | a | π = 0 | 0.1 | 0.2 | **0.3** | 0.4 | 0.5 | MDE (80%) |
|---|---|---|---|---|---|---|---|---|
| 0.78 (single construct) | 0.3 / 0.5 / 0.7 | **0.11 / 0.29 / 0.65** | — | — | — | — | — | — |
| 0.85 | 0.3 | 0.08 | 0.14 | 0.23 | 0.34 | 0.50 | 0.64 | > 0.5 |
| 0.85 | 0.5 | 0.17 | 0.26 | 0.37 | 0.52 | 0.67 | 0.79 | > 0.5 |
| 0.85 | 0.7 | 0.32 | 0.46 | 0.59 | 0.70 | 0.84 | 0.90 | 0.38 |
| 0.90 | 0.3 | 0.07 | 0.12 | 0.24 | 0.39 | 0.58 | 0.75 | > 0.5 |
| **0.90** | **0.5** | 0.09 | 0.18 | 0.32 | **0.474** | 0.66 | 0.83 | 0.48 |
| 0.90 | 0.7 | 0.17 | 0.30 | 0.45 | 0.63 | 0.77 | 0.89 | 0.43 |
| 0.95 | 0.3 / 0.5 / 0.7 | 0.05 / 0.06 / 0.07 | 0.10–0.16 | 0.21–0.30 | 0.41 / 0.44 / 0.50 | 0.63–0.67 | 0.81–0.84 | 0.48–0.50 |
| 0.99 | 0.3 / 0.5 / 0.7 | 0.06 / 0.05 / 0.04 | 0.07–0.08 | 0.20–0.22 | 0.39 / 0.41 / 0.39 | 0.60–0.65 | 0.80–0.84 | 0.48 to > 0.5 |

**Bias and coverage:**
- β̂_P is unbiased for its observed-scale population target in every cell (|bias| ≤ 0.003 yd/s per SD).
- HC3 95% coverage is 0.927–0.962.
- The 95% CI half-width is **±0.11–0.14 yd/s per SD of peak**. That is ±0.43–0.55 of the true between-player SD of game speed (0.254 yd/s).
- The SD of the observed partial r is about 0.125.

**The precision artefact (E3 vs E4).** At π = 0:
- the population observed-scale β_P is 0.06–0.14 yd/s per SD at R_F = 0.78, and 0.04–0.09 at R_F = 0.85;
- the test rejects in 11–65% (R_F 0.78) and 8–32% (R_F 0.85) of datasets.
- EIV calibration with the registered R_F = 0.95 then reports a spurious true-score effect of **0.08–0.18** at π = 0 (R_F 0.78), comparable to the true effect at π = 0.3 (0.12–0.26).
- With the correct R_F, EIV is unbiased for R_F ≥ 0.85. But R_F is unknown.

**Out-of-sample prediction (E2)** at π = 0.3, central (R_F 0.90, a 0.5):
- mean ΔR²_CV(M3 − M1) is 0.040 (SD 0.060);
- P(ΔR²_CV > 0) is **0.71**; P(ΔR²_CV ≥ 0.02) is 0.56.
- At π = 0, mean ΔR²_CV is −0.017 to +0.015 and is positive in 15–55% of datasets (55% when R_F = 0.85, a = 0.7: the artefact again).
- M2 alone beats M1 alone mainly when π ≥ 0.3 or R_F is low.

**Sample size** (R_F 0.90, a 0.5):

| players | power π = 0.1 | π = 0.2 | π = 0.3 | 95% CI half-width |
|---|---|---|---|---|
| 57 | 0.20 | 0.30 | 0.50 | ±0.12 |
| 100 | 0.30 | 0.53 | 0.76 | ±0.09 |
| 200 | 0.53 | 0.82 | 0.97 | ±0.07 |
| 400 | 0.84 | 0.99 | 1.00 | ±0.05 |

The resampled n = 57 row reproduces the main grid within Monte Carlo error (0.50 vs 0.474). About **110 WR** are needed for 80% power at π = 0.3, and about 190 at π = 0.2.

**Criteria:**

| criterion | result | pass? |
|---|---|---|
| C1 validity | size 0.043–0.055 at R_F 0.99; coverage ≥ 0.927 | **pass** |
| C2 central power | **0.474** (MC 95% ≈ [0.45, 0.50]) | **< 0.50** |
| C3 robust power | 0.34 (R_F 0.85, a 0.3) | fail (< 0.70) |
| C4 construct identifiability | 0.11–0.65 (R_F 0.78), 0.08–0.32 (0.85) | **fail** |
| C5 prediction | mean ΔR² 0.040 ✓, but P(ΔR² > 0) 0.71 | fail |

## 7. Assumptions and limitations

- **Normal, linear latent model.** Covariate adjustment is treated as known: the 56 REML fixed effects are not re-estimated in each replicate. Team-season variance is in the data but not in the analysis weights, as in the frozen two-stage. Each simplification makes the simulation slightly optimistic.
- **Reliabilities:**
  - R_P comes from within-session test–retest (an upper bound for "capacity on another day");
  - R_F is a grid because it is not identified;
  - the 0.78 lower bound assumes classical independent errors.
- **Composite outcome.** Deep- or short-specific incremental effects are not modelled. Choosing one context after H1 would re-open the registered contrast.
- **Selection.** The 57 earned ≥ 100 routes per context, so the cohort is range-restricted. Selection is mild on speed (R14: about 0.02 s on the 40) but strong on draft capital.
- **Prior exposure.** The M2 marginal association is already known (H1, Phase 2). The cohort is the registered H1 cohort, so a real analysis would not be independent of the registered study.
- **Plausible π.** The 40 includes acceleration (0–10 yd), while peak speed and route play-max speed are maximum-velocity measures. A non-zero π is conceptually plausible. However, the identifiable version of that claim needs an independent R_F.

## 8. Decision

**NO-GO**, under the pre-committed rule (C2 < 0.50; C3, C4 and C5 also fail):
- At n = 57, an incremental true partial of 0.3 is detected about half the time. The MDE is 0.43–0.50, or not reached.
- More fundamentally, even a significant E1 could not be attributed to a distinct capacity. The official 40's reliability is unknown, and the precision artefact alone rejects in up to 65% of datasets when R_F is at its admissible bound.
- The question is better posed than H2: outcome reliability is 0.85 vs 0.44, and central power is 0.47 vs about 0.28. But it is still not answerable on this cohort.

**Recommendation:** stop. Do not fit M1–M3 on the real join.

## 9. Would a separate exploratory pre-registration be justified?

**Not on the current data.**
- The registered cohort is already used, and the M2 marginal is known.
- Power is below the pre-set bar.
- The interpretable estimand (E4) is not identified.

A future pre-registration would be justified only with:
1. **Independent athletes:** at least 110 WR from Combine classes not in H1 (2026 onward), with tracked 40 and REG route tracking. About 190 WR are needed for π = 0.2.
2. **An identified R_F:** official per-attempt electronic times (or a second timed session). With that, E4 becomes estimable through EIV and the precision artefact can be removed.
3. **A pre-specified outcome and estimand:**
   - the composite H1 game-speed level;
   - E1 and E2 as stated here;
   - E4 only with a measured R_F;
   - player-grouped CV.

**Integrity checks for this phase:**
- full test suite: 113 passed, including `tests/test_code_freeze.py`;
- frozen-file SHA-256 hashes 12 / 12 unchanged;
- no registered report, result or output was modified;
- the only real-data inputs read were Combine fields, eligibility flags and play counts.

**Awaiting lead review.**
