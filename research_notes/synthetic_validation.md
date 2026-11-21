# Synthetic validation of the registered confirmatory pipeline (Phase 4)

**Status:** complete. **No combine measurement has been joined to any NFL game outcome. No real confirmatory model has been fitted.** The frozen protocol (`preregistration.md` v1.0) is unchanged, and its deviations log is still empty. Every change recommended below is a **proposed deviation awaiting approval**, and none is implemented in the confirmatory code path.

Companion notes: `demand_measure_validation.md` and `selection_bias_analysis.md`. Notebook: `notebooks/07_synthetic_pipeline_validation.ipynb`.

## 0. Design and reproduction

**Semi-synthetic design.** Every dataset uses the real design: the actual eligible players, their REG plays per context, team-seasons, routes, coverages, downs, seasons and NFL experience. Only the outcome and the combine predictors are synthetic. Nuisance parameters come from outcome-only REML fits.

**Calibration values:**

| | between-player Σ_b | corr_b | s2_team | s2_resid (hi, lo) | players (pool / eligible) | team-seasons |
|---|---|---|---|---|---|---|
| WR | [[0.0616, 0.0557], [0.0557, 0.0849]] | 0.77 | 0.0104 | 0.761, 1.455 | 69 / 57 | 76 |
| DB | — | +0.36 | 0.0053 | 2.35, 1.87 | 67 / 52 | — |

H2 (WR deep separation): s2b 0.0159, s2_team 0.0175, s2 2.98; 57 players and 9,935 plays; mean player reliability 0.43.

**Code:**
- `src/nfl_bdb/models/{reml,confirmatory,validation_summary}.py`
- `src/nfl_bdb/simulation/confirmatory_sim.py`
- `src/nfl_bdb/features/demand.py`
- `scripts/run_synthetic_validation.py` and `scripts/phase4_stages.py`

**Run order** (run id `20261121T023847Z`):
1. `skeleton`
2. `h1 h1_db h2 selection family selection_real demand_real demand_reliability demand_sim h1_s8fix h1_warp h1_direct h1_warp_db family_reml h1_warp_extra`
3. `scripts/db_correlation_decomposition.py`
4. `scripts/build_notebook_07.py`, then execute the notebook.

**Seeds:** `SeedSequence([4004, scenario, replicate])`. The bootstrap streams use `seed + 1` (warp) and `seed + 7` (direct). BLAS runs single-threaded.

**Monte Carlo error:** every rate is reported with its binomial MC SE, and every bias with its MC SE.

**Tests:** 25 unit tests pass (`tests/test_confirmatory.py`, `tests/test_phase4_helpers.py`, `tests/test_power.py`).

**Two inference procedures are evaluated for H1.** The spec (§1.3) contains both.
- **Registered primary.** REML point estimate, plus a player-cluster percentile bootstrap that refits the full REML model in every resample (B = 2,000).
- **Registered fallback** ("if REML is too slow for B = 2,000, use the moment estimator inside the bootstrap"). REML Δ̂ for the sign, and a moment-estimator bootstrap CI (pooled residualisation, spec §1.2).
  - All 400-replicate runs in §2.2 use the fallback, because it is fast.
  - The 4.5 % null rejection rate reported earlier is the fallback's.

The full REML bootstrap was evaluated two ways:
- **Warp-speed Monte Carlo** (Giacomini, Politis & White 2013): 10 REML resamples per replicate, pooled within the scenario. Same datasets, 400 replicates.
- **Direct check:** B = 400 REML resamples per replicate. 60 replicates of S1 and 40 of S5a, on identical datasets.

**Timing:** a full REML fit takes about 0.4 s, so the real analysis with B = 2,000 takes about 13 min. The fallback's trigger condition is therefore **not met**.

## 1. H1-WR under the registered primary (full REML bootstrap)

### 1.1 Null scenarios (true Δ = 0; nominal directional size α/2 = 0.025)

| scenario | full REML bootstrap: reject ± MC SE | coverage | bias of REML Δ̂ (± 0.006) |
|---|---|---|---|
| S1 null (ρ 0.3 / 0.3) | **0.0075 ± 0.0043** | 0.993 | +0.005 |
| S1b null, no association (0 / 0) | 0.000 (≤ 0.0075 at 95 %) | 1.000 | +0.002 |
| S5a deployment-only confounding | 0.000 | 1.000 | −0.003 |
| S5b selection on outcome | 0.005 ± 0.0035 | 0.995 | +0.019 |
| S6 differential reliability (registered ≥ 20/ctx after thinning) | 0.000 (≤ 0.0075) | 1.000 | +0.009 |
| S1 with empirical (non-normal) residuals | 0.0125 ± 0.0056 | 0.988 | +0.004 |

All rows are warp runs with 400 replicates each, on the same datasets as the fallback runs in §2.1. A rejection count of 0/400 bounds the rate at 0.0075 (95 % rule of three). In S6, 40 of 4,000 bootstrap refits failed and were dropped; the bootstrap SD there was 0.36 against a sampling SD of 0.19.

**Direct check (B = 400 per replicate, identical datasets):**

| | S1 null (60 reps) | S5a deployment (40 reps) |
|---|---|---|
| reject (direct) | 0/60 | 0/40 |
| coverage (direct) | 0.983 | 0.975 |
| mean bootstrap SE | 0.156 | 0.160 |
| true sampling SD of Δ̂ | 0.112 | 0.104 |
| pooled warp bootstrap SD | 0.159 | 0.171 |
| corr(direct, warp lower bound) | 0.85 | 0.68 |
| mean lower-bound difference (direct − warp) | +0.015 | +0.021 |

**The warp approximation reproduces the direct bootstrap,** with the same width and the same decisions within MC error.

### 1.2 Answer to priority 1

**The full registered REML bootstrap removes the 4.5 % false-positive rate.** Under every null scenario its rejection rate is ≤ 0.0125 (≤ 0.0075 in five of six), against a nominal 0.025. Coverage is 0.975–1.00.

**This is a calibration failure in the conservative direction.** Type I error is controlled, but the test is too wide near the null: its SE is about 1.4 times the true sampling SD.

### 1.3 Mechanism (diagnosed, reproducible)

The registered resampling scheme treats resampled players as distinct units and **shares team-season columns**.

A player drawn twice contributes two identical copies of his plays on the same team-season. REML cannot attribute that perfect co-movement to the player effect, because the copies are separate random-effect units. It moves it into the team-season effect instead.

Diagnostic (`ps.bootstrap_mechanism_diagnostic`, S1, 3 replicates × 40 resamples):

| | full data | bootstrap mean |
|---|---|---|
| s2_team | 0.008–0.014 | **0.015–0.043** (2–3×) |
| Σ_b, high-demand context | 0.038–0.072 | **0.017–0.050** (shrunk) |

Because ρ_c = β_c / √(β_c² + Σ_b,cc), shrinking Σ_b magnifies the variability of ρ̂* across resamples. This is the familiar failure of a one-factor cluster bootstrap in a crossed random-effects design. It is not a coding error: the point estimates and the REML fit itself are unbiased (§2.1).

**Where it bites hardest:**
- Small between-player variance relative to residual variance.
- DB: bootstrap SD 0.37 vs sampling SD 0.21 (§3).

### 1.4 Power of the registered primary (WR, 400 reps, warp)

| true Δ (observed scale) | 0.10 (small) | 0.20 (moderate) | 0.35 (large) |
|---|---|---|---|
| full REML bootstrap | 0.073 ± 0.013 | **0.448 ± 0.025** | **0.935 ± 0.012** |
| fallback (moment CI) | 0.140 | 0.468 | 0.898 |
| coverage (REML) | 0.993 | 0.958 | 0.948 |

The REML bootstrap distribution is right-skewed and narrows as Δ grows: its centred 2.5 % quantile is −0.28 at the null, −0.20 at moderate and −0.17 at large.

**Its conservativeness is therefore concentrated near Δ = 0.** At and above the SESOI-relevant effects (Δ ≥ 0.2), its power equals or exceeds the fallback's. The loss is confined to effects below the SESOI (Δ = 0.15).

## 2. H1-WR estimation (REML point estimate) and the registered fallback

### 2.1 REML Δ̂ bias and fallback decisions (400 replicates each)

| scenario | true Δ | REML bias (± ≈ 0.006) | moment bias | fallback reject (± MC SE) | fallback coverage | raw-contrast reject |
|---|---|---|---|---|---|---|
| S1 null | 0 | +0.005 | +0.010 | **0.045 ± 0.010** | 0.928 | 0.052 |
| S1b null 0/0 | 0 | +0.002 | +0.016 | 0.042 ± 0.010 | 0.942 | 0.042 |
| S2 small | 0.099 | −0.009 | −0.006 | 0.140 | 0.920 | 0.175 |
| S3 moderate | 0.199 | 0.000 | −0.009 | 0.468 | 0.932 | 0.507 |
| S4 large | 0.348 | −0.005 | −0.020 | 0.898 | 0.915 | 0.930 |
| S5a deployment only | 0 | −0.003 | **−0.058** | 0.005 | 0.938 | 0.008 |
| S5b selection on outcome | 0 | +0.019 | +0.023 | 0.045 ± 0.010 | 0.932 | 0.058 |
| S6 differential reliability (≥ 20/ctx re-applied) | 0 | +0.009 | −0.003 | 0.030 ± 0.009 | 0.920 | **0.070** |
| S6b combine R_x = 0.80 | 0.179 | −0.003 | −0.012 | 0.368 | 0.940 | 0.408 |
| null, empirical residuals | 0 | +0.004 | +0.011 | 0.042 ± 0.010 | 0.920 | 0.048 |
| moderate, empirical residuals | 0.199 | −0.006 | −0.011 | 0.458 | 0.945 | 0.507 |

**Notes:**
- S6 initially kept players whose thinned context fell below 20 plays. Re-applying the registered rule after thinning gives the row above. Before the fix, the raw contrast had a spurious rejection rate of 0.158.
- REML converged in ≥ 99.8 % of fits.
- Supported replicates had a same-sign 2025 season-forward estimate in 94–100 % of cases. The season-forward criterion almost never vetoes a true support, and it removes almost no false ones.

**Findings:**
1. **The REML point estimator is unbiased** (|bias| ≤ 0.02) under every scenario: deployment confounding, selection, differential reliability, measurement error and non-normal residuals.
2. **The fallback is liberal at the null** (0.042–0.045, about 2 MC SE above 0.025). Coverage is 0.92–0.94.
3. **The fallback's moment estimator is biased under deployment confounding** (−0.058). The registered model's context-specific covariates absorb route mix; the moment estimator's pooled residualisation does not.
4. **Measurement error** in combine peak speed (R_x 0.80) only attenuates Δ. The target is defined on the observed-x scale; disattenuation is reported after division by √R_x.
5. **The registered contrast is protected against differential reliability; the raw contrast is not** (0.070 vs 0.030 false positives). This is why the disattenuated contrast was registered.

### 2.2 Answer to priority 2: can the fallback be removed?

**Yes, and it should not be used.** The evidence:
- **Feasibility:** the fallback's trigger condition (REML too slow) is not met. B = 2,000 takes about 13 min.
- **Validity:** the fallback is liberal for WR (0.045) and grossly invalid for DB (false positives 0.225–0.28, bias +0.28, coverage 0.72–0.74). Its pooled-residualisation estimator is a different, misspecified model (§3).
- **Multiplicity:** the fallback inflates Holm's family-wise error to 0.14 (§5).

**Proposed deviation D1 (not implemented).** State in the deviations log that the fallback is not triggered, because full REML is feasible, so the registered primary (full REML bootstrap) is used for all H1 tests.
- This is arguably not a deviation at all: the spec makes the fallback conditional on infeasibility.
- It is listed for transparency, because the fallback was the fast engine for most of these simulations.
- The moment estimator remains the registered cross-check (spec §1.2), reported as such.

## 3. H1-DB (secondary) and the man/zone correlation sign change

**Decision behaviour (200 replicates each):**

| | null | moderate (Δ 0.2) |
|---|---|---|
| full REML bootstrap (warp): reject | 0.000 | **0.025 ± 0.011** |
| full REML bootstrap: coverage | 1.000 | 1.000 |
| REML bootstrap SD vs sampling SD | 0.37 vs 0.21 | 0.31 vs 0.21 |
| REML Δ̂ bias | +0.009 | +0.007 |
| fallback reject | **0.225 ± 0.030** | 0.560 |
| fallback (moment) bias | **+0.285** | +0.247 |
| fallback coverage | 0.74 | 0.76 |

**Why the player correlation between man and underneath zone moved from −0.33 (Phase 3.5) to +0.36 (Phase 4 calibration).** This is an outcome-only decomposition on real data, 52 players. It is identical with or without nullified plays.

| specification | corr(man, under-zone player level) |
|---|---|
| A: pooled residualisation over 3 contexts, moment estimator (Phase 3.5) | −0.326 |
| B: A without lined-up position | −0.331 |
| C: pooled residualisation over 2 contexts | −0.250 |
| D: context-specific residualisation, moment estimator | **+0.357** |
| E: REML with context-specific covariates, no team effect | +0.426 |
| **F: registered REML (context-specific covariates + team-season)** | **+0.361** |
| G: REML with common covariate effects + team-season | −0.230 |

**Explanation:**
- The sign is set entirely by whether the covariates (down, distance, time-to-throw, alignment, season…) have **common or context-specific effects**. Nullified plays, lined-up position and the team-season effect play no role.
- With common effects, context differences in covariate effects remain in the residuals. They load oppositely on man and zone, which creates a spurious negative player correlation.
- The registered model (F) is context-specific, so the Phase-4 value +0.36 is the correct calibration. The Phase 3.5 value was an artefact of the pooled residualisation in the power simulations.
- **The same misspecification makes the fallback moment estimator biased by +0.28 for DB.**

**Consequences:**
- **H1-DB stays secondary**, as registered.
- Under the registered primary, H1-DB has essentially **no power** (0.025 at Δ = 0.2), because of the bootstrap over-dispersion (§1.3).
- An H1-DB "not supported" will be uninformative. It must be reported as inconclusive, with its CI.

## 4. H2: tracked peak speed beyond the official 40

### 4.1 Size, power and criteria (57 WRs; 400 replicates for partial 0–0.4, 300 otherwise)

| true partial (peak \| 40) | β_P test reject ± MC SE | Holm level | all registered H2 criteria | mean partial̂ (SD) | P(ΔR²_CV ≥ 0.02) | P(90 % LB > 0) | P(EIV β_P > 0) |
|---|---|---|---|---|---|---|---|
| 0 | **0.028 ± 0.008** | 0.010 | 0.000 | 0.015 (0.32) | 0.06 | 0.000 | 0.49 |
| 0.1 | 0.065 | 0.028 | 0.005 | 0.094 (0.28) | 0.08 | 0.005 | 0.62 |
| 0.2 | 0.140 | 0.050 | 0.002 | 0.209 (0.29) | 0.16 | 0.008 | 0.74 |
| 0.3 | 0.290 | 0.150 | 0.015 | 0.342 (0.29) | 0.33 | 0.028 | 0.86 |
| 0.4 | 0.365 | 0.198 | 0.035 | 0.403 (0.27) | 0.41 | 0.050 | 0.91 |
| 0, empirical residuals | 0.030 | 0.013 | 0.000 | 0.005 | 0.07 | 0.000 | 0.45 |
| 0.3, empirical residuals | 0.250 | 0.157 | 0.020 | 0.323 | 0.28 | 0.027 | 0.85 |

**Other checks:**
- Partial-correlation bias ≤ 0.04.
- REML and two-stage WLS agree on the sign in 89–98 % of replicates.
- Season-forward ΔRMSE ≈ 0 throughout.

### 4.2 Answer to priority 3: increment or precision?

**The data-generating process makes the two explanations explicit.** Separation depends on the true 40-speed construct F with validity a, plus (when partial > 0) on the part of peak speed orthogonal to F. At partial = 0, any detected "increment" is therefore pure precision: tracked peak (R_x 0.987) is a better measure of F than the official 40 (R_F < 1).

**Simulation (partial = 0):**

| R_F | corr(40, sep) | β_P reject | all criteria | P(EIV β_P > 0) |
|---|---|---|---|---|
| 0.99 | 0.3 | 0.027 | 0.000 | 0.50 |
| 0.95 (registered) | 0.3 | 0.028 | 0.000 | 0.49 |
| 0.90 | 0.3 | 0.040 | 0.000 | 0.50 |
| 0.90 | **0.6** | **0.067 ± 0.014** | 0.007 | 0.61 |

**Population calculation** (notebook 07 §2). The spurious partial correlation of peak speed given the observed 40, when peak has **no** new information:

| R_F | 40 validity a = 0.3 | a = 0.6 |
|---|---|---|
| 0.99 | 0.004 | 0.011 |
| 0.95 | 0.023 | 0.053 |
| 0.90 | 0.046 | **0.108** |
| 0.85 | 0.071 | 0.164 |
| 0.80 | 0.098 | 0.223 |

**Interpretation:**
- **The precision artefact is of the same order as the SESOI (0.10)** whenever the official 40 is less reliable than about 0.9 and strongly related to separation.
- The registered EIV refit at R_F = 0.95 removes the artefact only if R_F ≥ 0.95. If the true R_F is 0.90, an EIV-surviving β_P can still be precision.
- At n = 57, the SD of partial̂ is about 0.28–0.32, so the data cannot separate a 0.05 artefact from a 0.10 effect.
- **Registered rule (protocol §12, spec §2):** a β_P that survives only at R_F = 0.99 is reported as "tracked peak speed is a more precise speed measurement", not as a different construct. This simulation shows the rule is necessary.

**Recommended reporting (not a change to the decision rule):** report the EIV β_P at R_F 0.85 / 0.90 / 0.95 / 0.99, and the R_F at which it reaches 0 (the tipping point).

**Proposed addition D3 (an outcome-free, combine-only analysis, needing approval).** Estimate the test–retest reliability of the 40 from the two recorded combine attempts. It informs which EIV row is credible without touching outcomes. The official 40 is a best-of-attempts time, so this gives a bound, not R_F itself.

### 4.3 Cross-validation, leakage and the predictive criterion

- `h2_cv` assigns whole players to folds (unit test `test_cv_holds_out_players_not_plays`).
- Residualisation is done inside each fold from per-player sufficient statistics.
- Under the null, ΔR²_CV is −0.024 with player folds, versus −0.001 for a play-level split on the same replicates. **A play split is optimistic by about 0.02, which equals the registered predictive threshold.** The registered player-level CV is therefore necessary.
- The **predictive criterion** (ΔR²_CV ≥ 0.02 with a 90 % bootstrap LB > 0) is met in ≤ 5 % of replicates even at partial 0.4. Full H2 support is therefore ≤ 0.035 at every effect size.

**Verdict on H2:** at n = 57, H2 is **not suitable for a confirmatory claim**. It is suitable for **estimation**: β_P and the true-scale partial with CIs, plus the EIV sensitivity grid. This matches the protocol's own expectation ("inconclusive is the expected outcome"). The size of the β_P test itself is controlled (0.028), so a reported CI is trustworthy. A "supported" H2 is practically unreachable, and a non-support carries little information.

## 5. Answer to priority 6: multiplicity

The family-wise error rate (FWER) is evaluated from complete simulations: independent replicates paired by index, 200 per configuration. H2 is reached only if H1-WR is rejected (fixed sequence). Holm runs over {H1-WR, H1-DB, H2}.

**Registered primary** (full REML bootstrap p-values for H1; `family_reml.parquet`):

| truth | P(any false rejection), fixed sequence | P(any false rejection), Holm |
|---|---|---|
| global null | **0.010 ± 0.007** | **0.005 ± 0.005** |
| H1-WR large, H2 null (false = H2) | 0.020 ± 0.010 | 0.005 |
| H1-WR null, H2 partial 0.4 (false = H1-WR) | 0.010 | 0.000 |
| H1-WR moderate, DB moderate, H2 null (false = H2) | 0.010 | 0.005 |

**Power** (P that the true hypothesis is rejected):

| truth | H1-WR, fixed sequence | H1-WR, Holm | H2, fixed sequence | H2, Holm | DB, Holm |
|---|---|---|---|---|---|
| H1-WR large, H2 partial 0.3 | 0.945 | 0.850 | 0.240 | 0.165 | — |
| H1-WR large, H2 partial 0.4 | 0.945 | 0.840 | 0.350 | 0.190 | — |
| H1-WR moderate, H2 partial 0.3 | 0.415 | 0.245 | 0.110 | 0.145 | — |
| WR moderate + DB moderate | — | — | — | — | **0.000** |

**Fallback, for comparison** (`family.parquet`):
- global null: fixed sequence 0.045 ± 0.015; **Holm 0.140 ± 0.025**, driven by H1-DB false positives (0.125).
- H1-WR large, H2 null: false H2 rejection 0.020.

**Findings:**
- The registered fixed sequence controls FWER (≤ 0.020 against α = 0.05; directional ≤ 0.025), as do the Holm sensitivity results under the registered primary.
- The gatekeeping works as designed. When H1-WR is null, H2 is effectively never reached (0.005 even at partial 0.4). Holm, by contrast, would test H2 directly (0.160 power at partial 0.4).
- The fallback breaks Holm through H1-DB. This is another reason for D1.

## 6. Proposed deviations (none implemented; each needs approval)

**D1: retire the fallback.**
- *Change:* use the full REML bootstrap for every H1 test; keep the moment estimator only as a reported cross-check.
- *Why:* the trigger is not met; the fallback is liberal (WR 0.045), invalid for DB (0.225) and inflates Holm (0.14).

**D2: bootstrap calibration (optional; see below).**
- *Change:* replace the shared-team-season player bootstrap with one of the options below, validated on the Phase 4 scenarios **before** the join.
- *Why:* the registered REML percentile bootstrap is valid but conservative (size ≤ 0.0125 vs 0.025), with no power for DB.

**D3: combine-only test–retest of the 40, plus reporting the EIV tipping point R_F.**
- *Change:* adds an outcome-free analysis and extra reporting; the decision rule is unchanged.
- *Why:* the H2 precision artefact is about the SESOI when R_F < 0.9 (§4.2).

**D2 options, ranked:**
- **(a) Copy-specific team-season labels.** Each resampled copy of a player gets its own team-season labels. Duplicates then no longer create spurious team covariance. It is still a nonparametric player bootstrap, and directly targets the diagnosed mechanism.
- **(b) Parametric bootstrap from the fitted REML model.** Simulate y from the fitted fixed effects and variance components, then refit. It is calibrated if the model is right; it does not protect against misspecification.
- **(c) Wald interval for Δ.** Uses the delta method with the REML covariance of (β, θ). It is cheap, but treats a bounded, skewed ratio as normal.

**Recommendation: do not adopt D2 for the primary test now.**
- The registered test is valid.
- At Δ ≥ 0.2 its power already matches a calibrated test.
- Any recalibration can only raise the false-positive rate toward 0.025.
- If D2(a) is approved, it should be validated on the S1–S6 scenarios with the same seeds, and its decisions reported **alongside** the registered ones, not instead of them.

## 7. Limitations

- **Warp-speed MC** assumes the bootstrap distribution's shape is similar across replicates within a scenario. The direct check (100 replicates, B = 400) confirms it for S1 and S5a.
- **Selection-grid REML decisions** borrow the bootstrap shape from the matching warp scenario (labelled approximate in `selection_bias_analysis.md`).
- **Independence across hypotheses.** H2 and H1 data are generated independently and paired by index. In reality the WR samples overlap, and their correlation is unknown, but FWER bounds for fixed sequence do not depend on it.
- **Semi-synthetic realism.** The DGP is linear-Gaussian at the player level. Empirical residuals check the play-level tails only.
- **Monte Carlo precision:** about 0.004 at the null, 0.025 at moderate power.

## 8. Verdict

1. **Is H1 statistically trustworthy?** **Yes, for H1-WR under the registered primary.**
   - The REML estimate is unbiased under all six scenario families.
   - The full REML bootstrap controls Type I error, conservatively (size ≤ 0.0125 across all six null scenarios).
   - Power is 0.45 at Δ = 0.2 and 0.94 at Δ = 0.35.
   - Fixed-sequence FWER is ≤ 0.02.
   - **Conditions:** the fallback must not be used (D1), and a non-significant result at Δ < 0.2 is uninformative.
   - H1-DB is not decision-informative (power ≈ 0.03).
2. **Is H2 confirmatory or estimation-only?** **Estimation only.**
   - Its test is size-correct, but full support is ≤ 0.035 at any plausible effect.
   - The precision artefact from the 40's measurement error is about the SESOI.
3. **Are the demand measure and selection procedure validated?** **Yes, for their registered roles**, with caveats:
   - Demand is threshold-robust, split-stable and free of self-normalisation leakage. OL contexts do not differ.
   - The registered eligibility rule is a sound compromise. REML is unbiased for its selected-population target.
   - Selection on deep-route level can inflate the target Δ by about 0.04. That must be part of the interpretation.
4. **Is the pipeline ready for the real-data join?** **Yes, conditional on deciding D1 first** (and, optionally, D2/D3) and entering it in the deviations log **before** the join.
   - Every registered component has now been exercised on the real design.
   - No registered method failed in the unsafe direction.
   - The fallback failed and must be retired explicitly, not silently.
