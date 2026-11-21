# H1-WR confirmatory result (sole primary hypothesis)

**Decision: INCONCLUSIVE.** H1-WR is **not supported**, and it is **not falsified**.

## Provenance

| | |
|---|---|
| Analysis run | `experiments/h1_wr_confirmatory/20261121T223645Z/` (`h1_wr_result.json`, `bootstrap_delta.npy`, `jackknife_delta.npy`) |
| Code | commit `8674e80`. Frozen pipeline files are unchanged since the freeze `955d94d` (hash test passes). Runner: `scripts/run_h1_wr_confirmatory.py`; display: `notebooks/08_h1_wr_confirmatory_analysis.ipynb` |
| Data | the single validated join `20261121T135032Z` (`h1_WR.parquet`); pre-model audit passed |
| Inference | `confirmatory.h1_registered_test`: REML + full REML player-cluster percentile bootstrap, **B = 2,000** (D1). The retired fallback was not used. |
| Seed | 4004, declared in the runner before the run. **The analysis was run once.** A synthetic-outcome dry run on 15 players preceded it, to check code paths only. |

No preregistration text, decision rule, threshold or analysis code was changed after the run.

## 1. Registered hypothesis and decision rule

**Hypothesis:** Δ_WR = ρ_deep − ρ_short > 0.
- ρ_c is the correlation between tracked combine 40 peak speed and the player's true, covariate-adjusted mean play maximum speed (snap to pass forward) in route context c.
- deep = GO / POST / CORNER / WHEEL; short = HITCH / SLANT / OUT / FLAT / SCREEN / ANGLE.

**Decision rule (§12, α = 0.05, sole primary test after D4):**
- **Supported** iff Δ̂ > 0, the 95 % CI excludes 0, **and** the 2025 season-forward estimate has the same sign.
- **Falsified** iff the 90 % CI upper bound is < 0.15 (SESOI), or the 95 % CI lies entirely below 0.
- **Otherwise inconclusive.**

## 2. Primary result

| quantity | value |
|---|---|
| **Δ̂ (REML)** | **0.090** |
| ρ̂_deep / ρ̂_short | 0.576 / 0.486 |
| **95 % bootstrap percentile CI** | **[−0.089, 0.400]** |
| 90 % bootstrap percentile CI | [−0.045, 0.333] |
| **bootstrap SE** | **0.122** |
| **two-sided bootstrap p** (CI inversion) | **0.211**; share of Δ* ≤ 0 is 0.106 |
| Δ̂ > 0 | yes |
| 95 % CI excludes 0 | **no** → not supported |
| 2025 season-forward Δ̂ (46 WRs, 8,745 plays) | 0.219, same sign (not sufficient on its own) |
| 90 % upper bound < 0.15? / 95 % CI < 0? | no / no → not falsified |
| **Decision** | **INCONCLUSIVE**: compatible with Δ from **−0.09 to 0.40** |

## 3. Effect size and practical interpretation

**Both correlations are moderately large and similar.** Combine peak speed is associated with in-game speed expression on deep routes (ρ ≈ 0.58) **and** on short routes (ρ ≈ 0.49).

**Raw slopes:**
- Per 0.25 yd/s of combine peak speed (≈ 0.8 within-WR SD; the sample SD is 0.30 yd/s), the average play-maximum speed is **0.110 yd/s** higher on deep routes and **0.113 yd/s** higher on short routes.
- The *slopes are essentially identical*. The small difference in ρ comes from the smaller true between-player spread on deep routes (Σ_b deep 0.035 vs short 0.060), not from a steeper speed translation.

**Disattenuated estimates** (D3 reporting; the decision uses the observed-x scale):

| R_x used | ρ_deep | ρ_short | Δ |
|---|---|---|---|
| 0.987 (registered, pooled) | 0.580 | 0.489 | 0.091 |
| 0.94 (within-WR, D3) | 0.594 | 0.501 | 0.093 |

**What the data can and cannot say:**
- **Cannot be claimed:** that combine speed "matters more" on deep routes. The point estimate is below the SESOI (0.15).
- **Cannot be excluded:** a deep-route advantage of up to Δ ≈ 0.40, or a small deep-route disadvantage (down to −0.09).
- **Registered precision statement:** at n = 57 WRs, effects of Δ < 0.27–0.33 could not be reliably detected (80 % power, §11). Phase 4 gave power 0.45 at Δ = 0.2 under this exact procedure.
- **Never to be read as "no effect".** The result is inconclusive, not null.

**For a scout:** in this cohort, a faster combine 40 peak goes with faster game speed on short routes about as much as on deep routes. Combine speed shows up in-game regardless of route depth. Whether it shows up *more* on deep routes is not resolved by 57 receivers.

## 4. Sample and observations per context

- **Players:** 57 WRs. **Plays:** 19,960. **Team-seasons:** 71, of which 36 contain a single cohort WR.
- **Deep:** 9,961 plays from 57 players; plays per player min 47, median 141, max 575.
- **Short:** 9,999 plays from 57 players; plays per player min 31, median 144, max 528.
- **By season:** 2023: 3,851 plays (24 WRs); 2024: 7,245 (39); 2025: 8,864 (51).
- **Combine peak speed in the sample:** mean 11.12 yd/s, SD 0.30.

## 5. Convergence and diagnostics

**Full-data REML fit:**
- Converged.
- 56 fixed-effect columns: context-specific intercepts, route, coverage, down, distance, formation, time-to-throw, season and NFL-year effects.

**Variance components:**

| | value |
|---|---|
| Σ_b | [[0.0353, 0.0301], [0.0301, 0.0600]]; between-player correlation 0.66 |
| team-season variance | 0.0099 |
| residual variance, deep / short | 0.763 / 1.453 |
| mean reliability of player-context means, deep / short | 0.85 / 0.82 |

These are consistent with the outcome-only Phase 4 calibration: team-season 0.0104, residuals 0.761 / 1.455.

**Bootstrap:**
- **2,000 / 2,000 refits succeeded** (0 failures).
- Δ* mean 0.134, median 0.125 (median − Δ̂ = +0.035), SD 0.122.
- Quantiles: 0.5 % −0.263, 99.5 % 0.541.
- The right skew and the positive median shift match the Phase 4 behaviour of this bootstrap.
- Phase 4 (D2, documented) showed this registered bootstrap is **conservative**: it is wider than the true sampling distribution near Δ = 0, with simulated null size ≤ 0.0125. That property was accepted before the run, and it does not change the decision rule.
- **Season-forward fit:** 2025 only, players with ≥ 20 plays per context; 46 WRs; converged.
- **Run time:** 656 s for the primary test.

## 6. Registered accompanying reports (none affects the decision)

| report | result |
|---|---|
| BCa interval (§10; jackknife over 57 players) | 95 % [−0.284, 0.283]; 90 % [−0.179, 0.235]. z₀ = −0.37 (the bootstrap median lies above Δ̂), a = 0.013. **BCa and percentile intervals both include 0.** BCa shifts the interval down. |
| Moment-estimator cross-check (spec §1.2) | Δ = 0.072 (ρ 0.526 / 0.455). It differs from REML by less than ½ bootstrap SE, so it does not disagree. Never used for decisions (D1). |
| Bayesian sensitivity (§12.5; skeptical prior Δ ~ N(0, 0.15²), normal likelihood with the bootstrap SE) | posterior mean 0.054, SD 0.095; P(Δ > 0) = 0.72; **P(Δ > 0.15) = 0.16** |
| Model-based Wald interval (§10 "as a check") | **not produced.** The REML engine does not return the covariance of the variance parameters needed for a delta-method Δ interval. Listed as an open reporting item; it cannot change the decision. |

## 7. Caveats for interpretation

**Selection (Phase 4, `selection_bias_analysis.md`).** The estimand refers to WRs with ≥ 100 REG routes. If playing time selected on deep-route speed level, the target Δ would be inflated by about 0.04. That would push in favour of H1, and H1 is still not supported.

**Associational only (§1, §7).** Route assignment, defender quality and play-call intent are not observed.

**Not yet run:** the §13 robustness grid and negative controls (permuted contexts, thresholds 50/200, without time-to-throw, REG + POST, leave-one-team-out, ceiling-robust outcome, splines, mean-of-attempts peak, IN/CROSS as short, eligibility weights). These are registered for H1-WR as sensitivity analyses and await your approval. They cannot turn this result into "supported".

**Next steps, only after your review:** H2 (secondary, estimation), then the Holm secondary family (H1-DB, H1-DL(a/b), H5(b)), then the H5/H1-global estimates and the TE descriptives, all under the registered hierarchy. None of these has been run.
