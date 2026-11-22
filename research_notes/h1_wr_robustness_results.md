# H1-WR: registered robustness checks

**What this note is.** Registered sensitivity analyses for the sole primary hypothesis.
- **The confirmatory result is unchanged:** Δ̂ = 0.090, 95 % CI [−0.089, 0.400], p = 0.211, **INCONCLUSIVE** (`h1_wr_confirmatory_results.md`).
- Nothing here re-decides H1. Sensitivity analyses can only describe the stability of that result.

**Provenance:**
- Run `experiments/h1_wr_robustness/20261121T233918Z/` (`robustness.json`, `bootstraps.npz`), code commit `a18a1d8`. Frozen pipeline files are unchanged; the hash test passes.
- Runner: `scripts/run_h1_wr_robustness.py`. New registered model variants are in `src/nfl_bdb/models/h1_extensions.py`, unit-tested on synthetic data.
- Seeds were declared in the runner before the run.
- **Aborted first attempt:** run `20261121T230849Z` deadlocked at start-up (forked worker pool after polars use). It produced no estimates and its empty directory was removed. The relaunch used spawned workers, with identical inputs and seeds.

**Data.** All frames come from the single join (`20261121T135032Z`):
- Variants that need other plays or players (R1, R2, R4, R9) were built with the frozen join functions from that join's `predictors.parquet`. No new predictor values were created.
- Unless stated, every estimate uses the registered estimator and inference: REML, plus full REML player-cluster percentile bootstrap, B = 2,000 (`h1_registered_test`).

## 1. Registered sensitivity analyses (registry: preregistration §3.4, §5, §7, §10, §13; spec §1.4, §4)

**Primary, for reference:**

| | Δ̂ | ρ_deep / ρ_short | 95 % CI | 90 % CI | SE | p | players | plays deep / short |
|---|---|---|---|---|---|---|---|---|
| **Primary (confirmatory)** | **0.090** | 0.576 / 0.486 | **[−0.089, 0.400]** | [−0.045, 0.333] | 0.122 | 0.211 | 57 | 9,961 / 9,999 |

**Sensitivity analyses:**

| # | Registered check | Δ̂ | ρ_deep / ρ_short | 95 % CI | 90 % CI | SE | p | players | plays deep / short |
|---|---|---|---|---|---|---|---|---|---|
| R1 | eligibility ≥ 50 opportunities | 0.082 | 0.564 / 0.482 | [−0.101, 0.344] | [−0.067, 0.300] | 0.121 | 0.305 | 61 | 10,077 / 10,085 |
| R2 | eligibility ≥ 200 | 0.119 | 0.571 / 0.452 | [−0.177, 0.449] | [−0.105, 0.368] | 0.153 | 0.269 | 45 | 9,206 / 9,396 |
| R3 | without time-to-throw | 0.100 | 0.565 / 0.466 | [−0.160, 0.373] | [−0.065, 0.323] | 0.131 | 0.247 | 57 | 9,961 / 9,999 |
| R4 | REG + POST (911 POST plays from 29 WRs) | 0.081 | 0.575 / 0.494 | [−0.119, 0.393] | [−0.069, 0.339] | 0.130 | 0.256 | 57 | 10,415 / 10,456 |
| R5 | leave-one-team-out (29 teams with an eligible WR; point estimates) | 0.035 to 0.125 | — | — | — | — | — | 53–57 | — |
| R6 | ceiling-robust outcome (top-10 % upper speed expression, ME model, player bootstrap) | 0.102 | 0.594 / 0.492 | [−0.144, 0.351] | [−0.106, 0.310] | 0.124 | — | 57 | ≥ 31 per context |
| R7 | natural cubic spline (3 df): average-derivative difference | −0.020 yd/s per SD (linear: −0.004) | — | [−0.100, 0.041] | — | 0.037 | — | 57 | as primary |
| R8 | mean-of-attempts combine peak speed | 0.110 | 0.565 / 0.455 | [−0.081, 0.409] | [−0.038, 0.364] | 0.128 | 0.158 | 57 | as primary |
| R9 | IN / CROSS assigned to short routes | 0.073 | 0.564 / 0.491 | [−0.148, 0.256] | [−0.099, 0.226] | 0.106 | 0.401 | 57 | 9,961 / 16,069 |
| R10 | inverse-probability-of-eligibility weights | **not computed** (see §3) | | | | | | | |
| R11 | playing-time sensitivity model (log routes × context added) | 0.116 | 0.623 / 0.507 | [−0.082, 0.413] | [−0.025, 0.364] | 0.127 | 0.144 | 57 | as primary |
| R12a | draft class 2023 | 0.094 | 0.475 / 0.381 | [−0.328, 0.631] | [−0.185, 0.536] | 0.242 | 0.365 | 24 | 5,479 / 5,571 |
| R12b | draft class 2024 | −0.068 | 0.547 / 0.615 | [−0.337, 0.381] | [−0.223, 0.305] | 0.169 | 0.860 | 19 | 3,085 / 3,396 |
| R12c | draft class 2025 (also the §13 new-player subset) | 0.262 | 0.625 / 0.363 | [−0.210, 0.857] | [−0.135, 0.743] | 0.272 | 0.263 | 14 | 1,397 / 1,032 |
| R13a | season-forward: 2023 + 2024 fit | −0.051 | 0.360 / 0.411 | [−0.953, 0.460] | [−0.797, 0.334] | 0.332 | 0.724 | 40 | 5,371 / 5,717 |
| R13b | season-forward: 2025 fit | 0.219 | 0.668 / 0.449 | [0.013, 0.705] | [0.061, 0.643] | 0.176 | 0.039 | 46 | 4,516 / 4,229 |

**Bootstrap success.** All 2,000 refits succeeded in every run except R12c (1,979 of 2,000; 14 players). All point fits converged.

**R7 spline details:**
- Average derivative is 0.127 (deep) vs 0.147 (short) yd/s per SD of peak speed; linear slopes are 0.132 vs 0.136.
- Knots: tertiles of all 94 WR combine participants' peak speeds (10.99, 11.22 yd/s), with boundaries at the sample range.
- **Player-grouped CV (10-fold × 20, stratified by draft class):** the spline's held-out RMSE is **higher** than the linear model's in all 20 repeats (mean +0.0022 yd/s, SD 0.0006). As registered, the linear model is preferred, and the spline is not selected on in-sample fit.

**R14: eligible vs ineligible WRs** (§5; combine and draft data only). These are the 94 WRs with a valid tracked 40:

| | n | official 40 (mean ± SD) | tracked peak | mean draft round | undrafted |
|---|---|---|---|---|---|
| eligible (≥ 100 routes) | 57 | 4.465 ± 0.090 s | 11.12 yd/s | 3.8 | 12 % |
| ineligible | 37 | 4.485 ± 0.088 s | 11.10 yd/s | 5.4 | 46 % |

Eligibility selects strongly on draft capital and only weakly on speed: about 0.02 s on the official 40, 0.02 yd/s on peak speed. This matches the Phase 4 finding that range restriction on speed is mild. The target population is "WRs who earned ≥ 100 routes", as stated in `selection_bias_analysis.md`.

## 2. Consistency with the primary estimate

**Direction.** All full-sample variants (R1–R4, R6, R8, R9, R11) keep Δ̂ > 0, in the range **0.073 to 0.119**, against the primary 0.090. Leave-one-team-out never changes the sign (0.035–0.125).

**Magnitude.** All are within ±0.03 of the primary, which is about ¼ of the bootstrap SE. **Every full-sample interval includes 0**, and every one also includes the SESOI of 0.15. None reaches support or falsification.

**Specific variants:**
- **Outcome definition:** the ceiling-robust outcome (0.102) shows the result is not driven by short routes capping the play-maximum outcome.
- **Covariates:** removing time-to-throw (0.100) shows the potentially post-treatment covariate does not drive the estimate.
- **Predictor and play set:**
  - Mean-of-attempts peak gives 0.110.
  - Adding POST plays gives 0.081.
  - Adding IN/CROSS to short gives 0.073. This reassignment also narrows the CI (SE 0.106), because it adds 6,070 short plays.
- **Selection (R1, R2, R11):**
  - Δ̂ is 0.082 at ≥ 50, 0.090 at ≥ 100 and 0.119 at ≥ 200.
  - That slight rise with the threshold is the direction Phase 4 flagged for selection on deep-route level (≈ +0.04). It is far inside the uncertainty.
  - Conditioning on playing time (R11) raises both ρ and Δ̂ slightly (0.116). Playing time is a potential collider, so this model is a sensitivity analysis only.
- **Spline (R7):** there is no evidence of nonlinearity that the linear contrast misses. The slope difference is near 0 on either scale, and cross-validation prefers the linear model.
- **Subsets (R12, R13):** these are heterogeneous, as expected with 14–46 players.
  - The class estimates (0.094, −0.068, 0.262) straddle the primary, with SEs of 0.17–0.27.
  - **Season-forward splits:** the 2023 + 2024 fit gives Δ̂ = −0.051 (CI −0.95 to 0.46; 40 WRs, few plays per player). The 2025 fit gives Δ̂ = 0.219 (CI 0.013 to 0.705).
  - The 2025 CI excludes 0. But it is a one-season subset, one of 15 sensitivity analyses, unadjusted. It is the same estimate whose *sign* the registered decision rule already used. **It is not evidence for H1.**
  - The opposite-signed point estimates in the two season splits show how unstable Δ is in subsets: the subsets are not precise enough to say whether the deep–short contrast changes over time.

**Overall.** The primary estimate is stable in direction and magnitude across every registered full-sample perturbation. The inconclusive verdict is **robust**: no variant comes close to the SESOI-based falsification bound (90 % upper bounds 0.23–0.37 vs 0.15), and none of the full-sample variants supports H1.

## 3. Checks that could not be run as registered

**R10 eligibility weights.**
- The frozen REML engine (`reml.fit_reml`) has no observation or cluster weights.
- A weighted analysis would need a new estimator, such as pseudo-likelihood-weighted REML. That changes the registered estimator, so it was **not** implemented.
- R14 documents what the weights would correct for: draft capital, and very little speed.
- If you want R10, it needs an approved deviation (new estimator plus synthetic validation).

**Absolute-threshold demand** (§13 grid). This applies to the H1-global demand meta-regression, not to the H1-WR contrast, so it is not applicable here.

## 4. Registered vs exploratory

**Everything in §1 is registered** (or the registered §5 comparison).

**Exploratory diagnostics are kept separate** in `h1_wr_bootstrap_diagnostics.md`:
- leave-one-team-season-out;
- jackknife influence;
- BCa decomposition;
- the Phase 4 coverage replay;
- the synthetic Wald calibration.

They are also kept apart in `h1_wr_negative_controls.md` (where the permutation percentile is labelled as not a test).
