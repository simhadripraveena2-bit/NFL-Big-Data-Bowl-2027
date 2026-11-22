# H2: tracked peak speed beyond the official 40 (secondary, estimation-focused)

**Question.** Does combine tracking-derived peak speed provide additional information about WR **deep-route separation** beyond the official 40-yard dash?

**Answer from these data.** **No incremental information was detected, and no prediction gain.**
- The incremental effect is estimated near zero and slightly negative.
- Neither the official 40 nor peak speed predicts held-out players' deep-route separation better than the position mean.
- The registered criteria pattern is "inconclusive". The interval for the registered falsification metric (the true-scale partial correlation) is degenerate, so it cannot be evaluated (§6).

## Status and provenance

**Status (D4).** H2 was registered as the **second primary confirmatory test** (protocol §2, §9). Before any combine × outcome association was inspected, it was demoted to a **secondary, estimation-focused** analysis, because Phase 4 showed:
- severe power limits: full registered support ≤ 0.035 at any plausible effect;
- vulnerability to measurement error in the official 40.

The registered hypothesis, variables, 57-WR sample, model, measurement-error grid, player-grouped CV, season-forward check and decision criteria are all preserved below. **The criteria are evaluated descriptively. Nothing in this note is confirmatory evidence.**

**Provenance:**
- Run `experiments/h2_estimation/20261122T012339Z/` (`h2_result.json`, `bootstraps.npz`), run once, from code commit `e6e1ad4`.
- Runner: `scripts/run_h2_estimation.py`. It re-uses the frozen `confirmatory` H2 functions. Additions are in `src/nfl_bdb/models/h2_extensions.py`, unit-tested on synthetic data.
- Data: the single join `20261121T135032Z`.
- Bootstrap CI, seeds and criteria were declared in the runner before the run.
- A synthetic-outcome dry run (15 players) preceded it.
- Display: `notebooks/09_h2_estimation_analysis.ipynb`.
- **One post-run fix** (§5): the tipping-point helper. It changes no estimate.

## 1. Registered specification (unchanged)

| element | registration |
|---|---|
| sample | 57 WRs: valid tracked 40, official 40, ≥ 100 REG routes, ≥ 30 deep and ≥ 20 short routes with separation |
| outcome | `separation_at_pass_forward` (yd), deep routes (GO/POST/CORNER/WHEEL), thrown passes |
| predictors | F = official 40 (sign-reversed, higher = faster); x = tracked 40 peak speed (max over valid attempts); both standardised within the sample |
| model | REML: s_ij = μ + γ'w_ij + κ·NFL year + β_F F_i + β_P x_i + b_i + τ_team-season + ε. Covariates w: route, coverage type, down, distance bin, formation, motion, time-to-throw bin, season |
| estimand | β_P: deep separation per SD of peak speed at a fixed 40. Also β_P*, the true-scale partial correlation and ΔR² of the true player level |
| CI | player-cluster percentile bootstrap, B = 2,000 (REML refit). Wald and two-stage WLS-HC3 as checks |
| prediction | held-out **players**: 10-fold × 20; M0 mean, M1 F, M2 F + x, M2s F + spline(x), M3 F + 10-yd split (reference); bootstrap of the whole CV (B = 500); leave-one-player-out |
| season-forward | fit 2023–24, predict 2025 player levels |
| measurement error | EIV refit at R_F = 0.95 (criterion) + grid R_F {0.85, 0.90, 0.95, 0.99} × R_x {0.94, 0.987} (D3) |
| negative control N3 | the same model on short routes; β_P^deep − β_P^short (descriptive) |

**Sample:**
- 57 WRs; 9,935 deep plays (median 140 per player, range 46–575); 10,032 short plays; 70 team-seasons.
- By season: 2023 1,884 plays (24 WRs); 2024 3,464 (39); 2025 4,587 (51).
- corr(official 40, peak speed) = 0.85 within these 57.

## 2. Incremental effect estimate (deep routes)

| quantity | estimate | uncertainty |
|---|---|---|
| **β_P** (yd of deep separation per SD of peak speed, 40 fixed) | **−0.020** | **95 % CI [−0.101, 0.063]** (REML bootstrap); 90 % [−0.084, 0.049]; SE 0.042; p = 0.71 |
| β_P, Wald check | −0.020 | SE 0.057, z = −0.35, p = 0.73 (t, df 54) |
| β_P, two-stage WLS-HC3 (Phase-4-validated) | −0.015 | 95 % bootstrap CI [−0.101, 0.068] |
| β_F (official 40, per SD faster) | 0.054 | 95 % CI [−0.048, 0.161] |
| β_P* (true-level SD units) | −0.15 | not estimable (see below) |
| **true-scale partial correlation r_P·F** | **−0.08** | bootstrap interval [−1, 1]: **degenerate** |
| **ΔR² of the true between-player level** | **0.006** | bootstrap interval [0.000, 0.96]: degenerate |
| R² of the true level: F alone / F + x | 0.075 / 0.081 | — |

**Why the true-scale quantities have no usable interval.** Players differ very little in deep-route separation once context is adjusted:

| | value |
|---|---|
| between-player SD | **0.13 yd** |
| team-season SD | 0.12 yd |
| play-level residual SD | 1.73 yd |
| mean reliability of a player's deep-separation level | 0.44 |

In about 60 % of bootstrap resamples, REML puts the between-player variance at its boundary (≈ 0). The partial correlation β_P/√(β_P²(1 − r²) + σ_b²) then becomes ±1.

**The raw-scale β_P is well behaved and is the informative estimate.** Its 95 % interval rules out an increment larger than about **0.06 yd (≈ 2 inches) of deep separation per SD of peak speed** at a fixed 40.

## 3. Prediction on held-out players

**Registered criterion engine** (frozen `h2_cv`, player-grouped 10-fold × 20):

| | R²_CV |
|---|---|
| M1 (40) | −0.020 |
| M2 (40 + peak) | −0.044 |
| **ΔR²_CV** | **−0.024** |
| 90 % bootstrap lower bound (B = 500 player bootstraps of the whole CV) | −0.036 |

**Extended CV** (folds stratified by draft class, as protocol §13 specifies) and the leave-one-player-out check:

| model | R²_CV | RMSE (yd) | Spearman | mean log pred. density | R² (leave-one-player-out) |
|---|---|---|---|---|---|
| M0 position mean | 0 | 0.1069 | — | 0.768 | 0 |
| M1 official 40 | −0.018 | 0.1079 | 0.09 | 0.760 | −0.017 |
| **M2 40 + peak** | **−0.039** | 0.1090 | 0.02 | 0.751 | −0.036 |
| M2s 40 + spline(peak) | −0.134 | 0.1138 | −0.10 | 0.704 | −0.129 |
| M3 40 + 10-yd split (reference) | −0.045 | 0.1093 | −0.02 | 0.745 | −0.049 |

**Increments of M2 over M1:**
- ΔR² −0.021 (SD across repeats 0.008);
- ΔRMSE +0.0011 yd;
- ΔSpearman −0.08;
- Δ log predictive density −0.009.

**No model beats the position mean on held-out players.** Adding peak speed (linear or spline) or the 10-yd split makes held-out prediction worse.

**Season-forward** (fit 2023–24 with 40 WRs; predict the 2025 levels of 30 WRs with ≥ 20 deep plays in both periods):
- RMSE M1 0.1383 vs M2 0.1380, so **ΔRMSE −0.0003 yd**.
- Spearman 0.09 vs 0.10.
- This is no meaningful gain.

## 4. Registered decision criteria, evaluated descriptively (D4)

| registered criterion (§12) | result | met? |
|---|---|---|
| β̂_P > 0 | −0.020 | no |
| 95 % CI excludes 0 | [−0.101, 0.063] | no |
| ΔR²_CV ≥ 0.02 | −0.024 | no |
| 90 % bootstrap lower bound of ΔR²_CV > 0 | −0.036 | no |
| season-forward ΔRMSE ≤ 0 | −0.0003 | yes, trivially (no material difference) |
| β̂_P > 0 survives the R_F = 0.95 EIV refit | −0.019, CI [−0.129, 0.079] | no |
| **"Supported" pattern** | | **no** |
| **"Falsified" pattern:** 90 % CI of the true-scale partial entirely < 0.10 | interval [−1, 1], degenerate | **not evaluable** |
| **Registered label** | | **inconclusive** |

**Plain reading.** By its registered labels, H2 is "inconclusive", because the falsification metric cannot be estimated precisely enough. Every registered indicator of incremental value points the same way, though:
- the estimate is ≤ 0;
- there is no held-out prediction gain;
- there is no season-forward gain;
- it does not survive errors-in-variables (EIV) correction.

The data provide **no evidence that tracked peak speed adds information about deep-route separation beyond the official 40**. The interval excludes increments above about 0.06 yd per SD.

## 5. Measurement error: genuine information vs improved precision

**EIV grid** (two-stage regression calibration):

| R_F \ R_x | 0.94 (within-WR, D3) | 0.987 (registered) |
|---|---|---|
| 0.85 | −0.083 | −0.054 |
| 0.90 | −0.042 | −0.031 |
| **0.95** | −0.023 | **−0.019** (criterion) |
| 0.99 | −0.015 | −0.012 |

**Tipping point.**
- EIV is defined only where the corrected predictor covariance stays positive definite: **R_F > r(F, x)²/R_x**, that is R_F > 0.733 (R_x 0.987) or R_F > 0.770 (R_x 0.94). This bound is close to the D3 data-based lower bound for WR R_F (≥ 0.70).
- On that whole admissible range, the EIV β_P is negative, between −1.8 and −0.011.
- **There is no R_F at which the increment becomes positive.**
- **Post-run fix:** the run stored 0.733 and 0.770 as "tipping points". Those values are the singularity, where β_P flips sign through infinity, not a zero crossing. The helper was corrected to search only the admissible range (`h2_extensions.tipping_point`, with a unit test), and the corrected value is "none". No estimate changed.

**How to tell increment from precision.**
- If deep separation depended only on true 40 speed, a noisy official 40 would make the more precise peak speed look incremental, with a **positive** spurious partial correlation.
- With the observed validity of the 40 (corr with the true deep-separation level ≈ 0.27–0.30) and corr(F, x) = 0.85, that artefact would be:

| R_F | 0.80 | 0.85 | 0.90 | 0.95 | 0.99 |
|---|---|---|---|---|---|
| expected spurious partial (peak \| 40), a ≈ 0.28–0.30 | +0.11 | +0.08 | +0.05 | +0.02 | +0.005 |

- **The observed partial is −0.08 and the raw β_P is −0.020.** There is no sign even of the precision artefact.
- So the question "increment or precision?" does not arise: **neither genuine incremental information nor a measurement-precision advantage of tracked peak speed is visible in deep-route separation**.
- The official 40 itself is only weakly related to deep separation: β_F 0.054, CI [−0.048, 0.161]; true-level R² 0.075.

## 6. Registered negative control N3: short-route separation

**What it detects.** If peak speed "predicted" separation as much on short routes (low speed demand) as on deep routes, an H2 association would more likely reflect general player quality or a measurement artefact than deep-route speed.

**What would indicate a problem.** A short-route β_P as large as or larger than the deep-route β_P, while the deep β_P is positive.

**Result:**

| | β_P | 95 % CI |
|---|---|---|
| short routes | +0.153 (Wald SE 0.079) | [−0.109, 0.365] (bootstrap) |
| **contrast β_P^deep − β_P^short** | **−0.173** | [−0.392, 0.088]; 90 % [−0.354, 0.052] |

- β_F on short routes is −0.100.
- The short-route true-scale partial is degenerate too (60 % of resamples at ±1).

**Reading:**
- There is no deep-route H2 association for N3 to explain away.
- The short-route point estimate is *larger* than the deep one, the opposite of a task-conditioned (deep-specific) speed effect. Its CI includes 0, and so does the contrast's.
- Short-route separation also had low context-adjusted reliability in Phase 3 (0.22).
- This is descriptive only. A short-route association is **not** a finding. It would need its own registered test.

## 7. Uncertainty and limitations

1. **Player-level signal in deep separation is tiny and partly team-driven.**
   - Between-player SD is 0.13 yd, against a play-level SD of 1.73 yd.
   - Player-level reliability is 0.44.
   - Team-season variance is about equal to player variance.
   - At n = 57, the true-scale partial correlation and ΔR² cannot be estimated with usable precision. That is why the registered falsification criterion is not evaluable.
2. **Power.** Phase 4 power for β_P at a true partial of 0.3 was 0.29. A null-like result is expected even if a modest effect existed. **"No evidence of an increment" is not "evidence of no increment"** beyond the raw-scale interval (≤ 0.06 yd per SD).
3. **Measurement error.** The official 40's reliability is not identified (D3: WR R_F ≥ 0.70). The conclusion holds for every admissible R_F.
4. **Selection.** These are WRs with ≥ 100 routes and ≥ 30 deep routes with separation.
5. **Associational only.** Defender identity and quality, coverage leverage and route stem are unobserved.
6. **Scope.** This applies only to separation at pass forward on thrown deep passes. Sacks and scrambles have no separation value.

## 8. Not run

DB, DL, OL and TE analyses (H1-DB, H1-DL, H5, TE descriptives) and the remaining registered negative control (N2, the OL contrast) await review.
