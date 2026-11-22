# H1-WR: bootstrap interval diagnostics and the Wald check

**The registered primary interval is unchanged:** the ordinary percentile interval **[−0.089, 0.400]**. Everything in this note is an **exploratory diagnostic**. It explains the intervals; it does not replace any of them.

**Provenance:**
- `scripts/run_h1_wr_bootstrap_diagnostics.py` → `experiments/h1_wr_robustness/20261121T233918Z/bootstrap_diagnostics.json`.
- Inputs: the primary run's saved arrays (2,000 bootstrap Δ*, 57 jackknife Δ₍₋ᵢ₎), the robustness run's cluster deletions, and the Phase 4 warp-speed simulation (the same bootstrap on the real WR design with synthetic outcomes).
- Wald: `h1_extensions.wald_delta`. Its synthetic calibration is in `scripts/validate_wald_synthetic.py`.

## 1. The two intervals

| interval | 95 % | 90 % | status |
|---|---|---|---|
| **percentile (registered primary)** | **[−0.089, 0.400]** | [−0.045, 0.333] | primary; decides H1 |
| BCa (registered "also reported") | [−0.284, 0.283] | [−0.179, 0.235] | reported |
| Wald, delta method (registered "check"; §5 below) | [−0.114, 0.294] | [−0.081, 0.261] | check |

All three include 0 and the SESOI. The decision would be "inconclusive" under any of them.

## 2. Bootstrap distribution

| | value |
|---|---|
| mean / median of Δ* | 0.134 / 0.125 (estimate 0.090) |
| share of Δ* below Δ̂ | **0.357** (a symmetric, centred bootstrap would give 0.5) |
| SD / IQR-based SD | 0.122 / 0.103 |
| skewness / excess kurtosis | 0.10 / **2.34** |
| 2.5 % and 97.5 % quantiles relative to Δ̂ | −0.179 / **+0.310** |

**Reading:** the distribution is almost symmetric about its own centre (skewness 0.10). But it is **shifted to the right of the estimate** (median − Δ̂ = +0.035) and **heavy-tailed** (kurtosis 2.3). Relative to Δ̂, the upper tail is therefore much longer than the lower tail.

## 3. Why BCa moves the interval down

**BCa parameters:**
- Bias correction: z₀ = Φ⁻¹(0.357) = **−0.368**.
- Acceleration (jackknife): a = **0.013**.

**Decomposing the BCa interval:**

| variant | quantile levels used | 95 % interval |
|---|---|---|
| percentile (z₀ = 0, a = 0) | 0.025 / 0.975 | [−0.089, 0.400] |
| acceleration only (z₀ = 0) | 0.028 / 0.978 | [−0.078, 0.406] |
| bias correction only (a = 0) | 0.0035 / 0.890 | [−0.310, 0.278] |
| full BCa | 0.0043 / 0.896 | [−0.284, 0.283] |

**The whole difference comes from the bias correction z₀.** Because the bootstrap median exceeds Δ̂, BCa infers that Δ̂ is biased *downward relative to the bootstrap world*. It therefore reads the interval from the 0.4 % and 89.6 % bootstrap quantiles instead of 2.5 % and 97.5 %. The acceleration is negligible.

**Is that bias real? Phase 4 says no.** The registered bootstrap was evaluated on the real WR design with synthetic outcomes:

| truth Δ | REML bias | bootstrap median shift | implied z₀ | sampling SD | bootstrap SD |
|---|---|---|---|---|---|
| 0 (S1) | +0.005 | +0.014 | −0.12 | 0.112 | 0.159 |
| 0.10 (S2) | −0.009 | +0.031 | −0.25 | 0.111 | 0.159 |
| **0.20 (S3)** | **−0.000** | **+0.042** | **−0.37** | 0.113 | 0.147 |
| 0.35 (S4) | −0.005 | +0.055 | −0.49 | 0.107 | 0.147 |

**The z₀ in the real data (−0.368) is exactly what this bootstrap produces at a true Δ ≈ 0.2, where the REML estimator is unbiased (−0.0004).**

The median shift is an artefact of the resampling scheme, not a bias of Δ̂. Under D2, duplicated players share team-season columns, so resampled fits shrink Σ_b and push ρ* outward. That mechanism is documented in `synthetic_validation.md` §1.3 and in D2.

**Replay of both intervals in the Phase 4 simulation** (warp-speed approximation; pooled z₀ per scenario, a = 0.013):

| truth Δ | percentile coverage / power | BCa-type coverage / power | BCa-type misses above the truth |
|---|---|---|---|
| 0 | 0.993 / 0.007 | 0.998 / 0.003 | 0.000 |
| 0.10 | 0.993 / 0.072 | 0.990 / 0.000 | 0.010 |
| 0.20 | 0.958 / 0.448 | 0.988 / 0.115 | 0.013 |
| 0.35 | 0.948 / 0.935 | 0.968 / **0.455** | **0.033** |

**In this design BCa over-corrects downward:**
- It loses most of its power (0.455 vs 0.935 at Δ = 0.35).
- Its upper limit falls below the truth (3.3 % at Δ = 0.35, against a nominal 2.5 %; the percentile interval never does).

This supports the registered choice of the percentile interval on statistical grounds, independently of which interval is "more favourable". **The BCa interval stays reported, with this caveat.**

## 4. Jackknife influence and cluster sensitivity

**Players** (57 leave-one-out REML fits):
- Δ₍₋ᵢ₎ ranges **0.051 to 0.121**. The largest single-player change is 0.039, and no sign changes.
- The five most influential players (anonymised by rank) move Δ̂ to 0.051, 0.121, 0.060, 0.061 and 0.113.
- **No single receiver drives the estimate.**
- Jackknife SE: **0.092**. The bootstrap SD (0.122) is 1.33× larger, matching the Phase 4 over-dispersion ratio of about 1.4.

**Teams** (29 teams with an eligible WR, leave-one-out):
- Δ̂ ranges **0.035 to 0.125**; the largest change is 0.055, with no sign change.
- All fits converged. Cluster-jackknife SE: 0.103.

**Team-seasons** (71, leave-one-out):
- Δ̂ ranges **0.045 to 0.123**; the largest change is 0.045, with no sign change.
- Cluster-jackknife SE: 0.103.

**Interpretation:**
- The estimate is not fragile to any single player, team or team-season.
- Three independent precision estimates agree with each other: the jackknife (0.092), the team-season cluster jackknife (0.103) and the Wald interval (0.104). All are smaller than the registered bootstrap SE (0.122). This is the documented, accepted conservativeness of the registered bootstrap (D2).
- **Even with the smallest of these SEs, the 95 % interval would include 0:** 0.090 ± 1.96 × 0.092 = [−0.09, 0.27]. The inconclusive verdict does not depend on the bootstrap's conservativeness.

## 5. The Wald check (Part 4)

**Why it was not produced in the confirmatory run.** Δ depends on the fixed slopes β *and* on the between-player covariance Σ_b. A Wald interval needs the sampling covariance of the variance parameters θ.
- `reml.fit_reml` returns θ̂, `neg2ll` and `cov_beta` (the GLS covariance of β given θ).
- It does **not** return Cov(θ̂).
- Its REML criterion is an internal closure that is not exposed. The frozen file could not be changed.

**Can it be computed without changing the estimator or model? Yes.**
1. `h1_extensions.reml_criterion` re-implements the **identical** criterion: same parametrisation (Cholesky of Σ_b, log SDs), same Woodbury algebra. At the fitted θ̂ it reproduces the frozen `neg2ll` to **7 × 10⁻¹²**.
2. The numerical Hessian H of −2 l_R at θ̂ is positive definite: eigenvalues 63 to 39,583.
3. Cov(θ̂) = 2 H⁻¹. Cov(β̂_x) is taken from the fit. β and θ are asymptotically independent under REML.
4. The delta method uses numerical gradients of Δ(β_x, θ).
5. The REML estimate itself (Δ̂ = 0.0900, identical to the primary) and the model are unchanged.

**Result:**
- **Wald SE = 0.104.** Of the variance, 73 % comes from β and 27 % from θ.
- **95 % CI [−0.114, 0.294]; 90 % CI [−0.081, 0.261].**

**Synthetic calibration** (exploratory; same real WR design, synthetic outcomes, Phase 4 seeds, 100 replicates each):
- At Δ = 0: the mean Wald SE is 0.108 against a sampling SD of 0.113; coverage 0.95; directional rejection 0.030 (nominal 0.025).
- At Δ = 0.2: coverage 0.93.
- The Wald interval is therefore close to calibrated here. Unlike the registered bootstrap, it is not conservative.

**Status:**
- The Wald interval is the registered *check*, now produced. It does not replace the primary interval and does not change the decision.
- Its 90 % upper bound (0.261) is still above the SESOI, so H1 remains **inconclusive, not falsified**, under the Wald check too.
