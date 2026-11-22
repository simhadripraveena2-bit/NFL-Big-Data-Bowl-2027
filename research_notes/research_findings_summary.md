# Research findings summary

**Project:** *Task-Conditioned Translation of Athletic Capacity: Connecting NFL Combine Sensor Tracking to Regular-Season Football Performance* (NFL Big Data Bowl 2027).

**Status (2026-11-22):** all pre-registered analyses are complete.
- **Frozen protocol:** `preregistration.md` v1.0, with deviations D1–D4 in §15, all made before any combine × outcome association was inspected.
- This summary only **consolidates**. It changes no analysis, decision or registration.
- Each section points to the note with full numbers.

## 1. Research questions and original hypotheses

**Questions:**
1. Does the association between combine-measured top speed and NFL regular-season game behaviour depend on how much the football task demands near-maximal speed?
2. Does combine *tracking* add information about wide-receiver separation beyond the official 40-yard time?

| ID | Registered statement | Original status | Final status (after D4) |
|---|---|---|---|
| **H1-WR** | ρ(combine peak speed, true game speed) is larger on deep than on short routes: Δ_WR = ρ_deep − ρ_short > 0 | primary, test 1 of a fixed sequence | **sole primary confirmatory test** |
| H2 | WR deep-route separation rises with tracked peak speed at a fixed official 40 (β_P > 0) | primary, test 2 | **secondary, estimation-focused** (D4) |
| H1-DB | ρ_man − ρ_underneath-zone > 0 | secondary (power) | secondary, Holm family |
| H1-DL(a) | ρ_pass-rush − ρ_run > 0 | secondary | secondary, Holm family |
| H1-DL(b) | the pooled DL translation shrinks after alignment and combine weight are adjusted for | secondary | secondary, Holm family |
| H5(a)/(b)/(c) | OL as a comparison group: Δ_OL; Δ_WR − Δ_OL > 0; OL vs demand-model prediction | secondary | (b) in the Holm family; (a), (c) estimation; (a) is also the OL negative control |
| H1-global | translation increases with cross-fitted demand D across 11 cells | secondary, descriptive | estimation |
| H1-TE | ρ_deep − ρ_short | descriptive (n = 17) | descriptive |

**Primary hierarchy:**
- H1-WR at FWER α = 0.05.
- Secondary family {H1-DB, H1-DL(a), H1-DL(b), H5(b)} under Holm at α = 0.05.
- Everything else is estimation, description or exploratory.

## 2. Data and sample sizes

**Sources:** competition data only.
- 510 combine participants with combine tracking and results.
- 2023–2025 game tracking of those players only (no ball, no other players).
- `player_play`, `games`, `players`.

**Outcomes:** REG season only; POST used only as a robustness check.

**Join:**
- One validated combine × outcome join (`join_validation_report.md`), keyed on exact `nfl_id`.
- 0 duplicate keys, 0 unmatched game players; raw data unchanged (sha256).
- Of the 510 participants:

| group | players |
|---|---|
| matched (REG rows + valid tracked 40) | 332 |
| REG rows, no valid 40 | 69 |
| no REG rows | 109 |

- A valid tracked 40 means R² > 0.95 and peak ≤ 12.5 yd/s. 92 participants lack one.

**Eligible samples** (≥ 100 primary REG opportunities, valid tracked 40, ≥ 20 plays per contrast context). All equal the registered counts:

| analysis | players | plays |
|---|---|---|
| H1-WR | 57 | 19,960 (deep 9,961 / short 9,999) |
| H2-WR | 57 | 9,935 deep (+ 10,032 short for the negative control) |
| H1-DB | 52 | 16,643 |
| H1-DL | 53 (25 EDGE, 28 interior) | 34,154 |
| H5 / OL | 53 | 64,285 |
| H1-TE | 17 | 4,170 |

**Variables:**
- **Predictor x:** tracked 40 peak speed, the maximum over valid attempts.
- **F:** official 40, sign-reversed.
- **Game outcome:** play-maximum speed (pre-pass for WR/TE; whole play otherwise).
- **H2 outcome:** separation at pass forward.

## 3. Methods and validation

**Estimand.** ρ_c is the correlation between combine peak speed and the player's *true* (noise-free, covariate-adjusted) game-speed level in task context c.
- It comes from a bivariate-context REML linear mixed model with context-specific covariates, correlated player random effects and a team-season random effect.
- The H1 contrasts are Δ = ρ_h − ρ_l.

**Inference:**
- REML point estimate with a full REML player-cluster percentile bootstrap, B = 2,000 (D1: the moment-estimator fallback was retired).
- Wald (delta-method, numerical REML Hessian) intervals are reported as a check.

**H2:**
- REML separation model on F and x.
- Prediction is judged on held-out **players** (player-grouped 10-fold × 20; never held-out plays), with season-forward evaluation, an errors-in-variables (EIV) grid and a short-route negative control.

**Phase 4 synthetic validation** (real design, synthetic outcomes; `synthetic_validation.md`):
- The registered REML bootstrap is **valid but conservative**: null size ≤ 0.0125 vs 0.025.
- WR power 0.45 at Δ = 0.2 and 0.94 at Δ = 0.35.
- The REML estimator is unbiased under deployment, selection, measurement-error and non-normal-residual scenarios.
- The fixed-sequence FWER is ≤ 0.02.
- The over-dispersion was diagnosed: duplicated players share team-season columns. D2 (changing the bootstrap) was rejected, and the conservative behaviour is documented.

**Safeguards:**
- Pre-registration before any join.
- Code frozen at `955d94d` (hash-tested).
- Write-once join; pre-model audit.
- Each confirmatory runner refuses a second run.
- Seeds and operational choices declared before every run.
- Synthetic dry runs before real runs.

## 4. H1-WR: primary result and robustness

(`h1_wr_confirmatory_results.md`, `h1_wr_robustness_results.md`, `h1_wr_negative_controls.md`, `h1_wr_bootstrap_diagnostics.md`)

| | value |
|---|---|
| ρ_deep / ρ_short | 0.576 / 0.486 |
| **Δ̂** | **0.090**, 95 % CI **[−0.089, 0.400]**, bootstrap SE 0.122, p = 0.211 |
| season-forward 2025 sign | same (0.219) |
| **decision** | **INCONCLUSIVE.** Not supported (the CI includes 0); not falsified (90 % upper bound 0.333 > SESOI 0.15) |

**Interpretation:** combine peak speed is associated with game speed about equally on short and deep routes. The raw slopes are ≈ 0.11 yd/s per 0.25 yd/s in both.

**Robustness (registered):**
- All full-sample variants give Δ̂ 0.073–0.119, and every CI includes 0. The variants are: eligibility 50/200; without time-to-throw; REG + POST; ceiling-robust outcome; mean-of-attempts peak; IN/CROSS as short; playing-time model.
- Leave-one-team-out: 0.035–0.125.
- Cross-validation preferred the linear model over the spline.
- **Negative control** (context labels permuted within player): centred at 0.003. No mechanical artefact.

**Interval diagnostics:**
- Wald check: 95 % [−0.114, 0.294].
- The BCa interval's downward shift is a property of the registered bootstrap (z₀ matches the Phase 4 bootstrap world, where the estimator is unbiased). The percentile interval stays primary.
- Even the smallest SE estimate (jackknife 0.092) gives an interval that includes 0.

## 5. H2: estimation result

(`h2_estimation_results.md`)

| quantity | estimate |
|---|---|
| **β_P** (deep separation per SD of peak speed, 40 fixed) | **−0.020 yd**, 95 % CI [−0.101, 0.063]. This excludes increments above ≈ 0.06 yd (≈ 2 in) per SD |
| held-out-player ΔR²_CV | −0.024 (90 % lower bound −0.036) |
| season-forward ΔRMSE | −0.0003 yd |

- **No model beats the position mean** on held-out players, not even the 40 alone.
- **EIV:** β_P ≤ 0 at every admissible 40 reliability.
- **No precision artefact either:** the expected spurious partial would be positive; the observed partial is −0.08.
- **Short-route negative control:** β_P +0.153, CI [−0.109, 0.365]; contrast −0.173, CI [−0.392, 0.088]. Descriptive.
- **Registered label: inconclusive.** The true-scale partial correlation is not estimable: between-player SD of deep separation is only 0.13 yd, reliability 0.44, and 60 % of resamples hit the variance boundary.
- **Plain statement:** no incremental information from tracked peak speed was detected.

## 6. DB, DL and OL secondary results

(`secondary_family_results.md`, `db_/dl_/ol_secondary_results.md`)

**Holm family** (m = 4, α = 0.05):

| hypothesis | estimate | 95 % CI | p unadjusted | p Holm | registered decision |
|---|---|---|---|---|---|
| **H1-DL(b)** pooled − adjusted DL ρ | 0.816 | [0.160, 1.538] | 0.008 | **0.032** | **SUPPORTED** |
| H1-DB | 0.139 | [−0.609, 1.050] | 0.691 | 1.00 | inconclusive |
| H5(b) Δ_WR − Δ_OL | 0.007 | [−0.573, 0.627] | 0.833 | 1.00 | inconclusive |
| H1-DL(a) | 0.038 | [−0.229, 0.154] | 0.931 | 1.00 | falsified by the registered equivalence-type rule (90 % upper bound 0.124 < 0.15): a SESOI-sized pass-rush-vs-run difference is not supported; *not* a claim of zero |

**DB:** man ρ 0.29, underneath 0.15, deep zone 0.09. Very imprecise; uninformative.

**OL:** ρ 0.11 (pass block) and 0.03 (run).
- H5(a), the OL negative control: Δ_OL 0.084, CI [−0.46, 0.64]. No spurious contrast is visible, but the result is uninformative. No equivalence is claimed.
- H5(c): observed 0.07 vs predicted 0.33, inside a 90 % prediction interval 0.93 wide. Uninformative.

**H1-global** demand meta-regression: λ is uninformative (cell-bootstrap CIs span ± several units).

**TE (descriptive):** Δ_TE 0.08, Wald 95 % [−0.27, 0.44].

## 7. The H1-DL(b) interpretation audit

(`dl_role_weight_interpretation.md`; descriptive, no tests)

**Registered statistical result (unchanged).** H1-DL(b) is **supported after Holm adjustment** (p = 0.008; Holm-adjusted p = 0.032).
- Definition: pooled DL translation = mean of ρ_pass-rush and ρ_run. This was declared before the run, and the conclusion is insensitive to the weighting (0.75–0.88).
- Pooled ρ falls from 0.549 (registered model) to −0.267 (+ EDGE role × context + combine weight × context).

**Interpretation, as accepted:**
- The pooled DL combine-speed/game-speed association is **substantially sensitive to role and body-weight adjustment**.
- Descriptively, **role alone (pooled ρ −0.05) and weight alone (−0.08) each remove most of the pooled association**.
- Within EDGE (0.05) and within interior (0.01) linemen, the association is near zero.

**Collinearity:** speed–weight r = −0.80, speed–EDGE +0.72, weight–EDGE −0.82; VIF of speed on role + weight 2.9.
- **Correction retained:** the earlier wording "weakly identified" overstated this. The adjusted model is identified but imprecise (SE 0.23 vs 0.10).

**Not claimed:**
- that the joint role-and-weight model uniquely identifies the mechanism, because role, weight and speed form one correlated athletic profile;
- any causal reading of the adjusted negative value (−0.27 ± 0.45). Role is partly a consequence of athleticism (mediator, possible collider bias). The value is sign-unstable across conditioning sets and scaled by the total SD of speed (−0.16 with the conditional SD).
- The outcome is game movement, not get-off and not pass-rush performance.

## 8. Measurement reliability

| quantity | reliability | source |
|---|---|---|
| combine tracked peak speed, single attempt (within position) | WR 0.89, TE 0.93, DB 0.93, DL 0.98, OL 0.93 (pooled 0.987, inflated by position differences) | `forty_test_retest.md` (D3) |
| registered predictor (best of 2 attempts) | WR 0.94, TE 0.96, DB 0.96, DL 0.99, OL 0.97 | D3 |
| official 40 | **not identifiable** from tracking (the tracked start is not the electronic start); WR R_F ≥ 0.70 (≈ 0.86 under a stronger assumption) | D3 |
| game play-maximum speed, player-context mean | WR 0.85 / 0.82; TE 0.77 / 0.91; DB 0.65 / 0.68; DL 0.94 / 0.86; OL 0.94 / 0.90 | secondary run |
| WR deep-route separation, player level | 0.44 (between-player SD 0.13 yd vs 1.73 yd play to play) | H2 |
| near-top-speed demand D (cell level) | stable across player halves (WR deep SD 0.010) and across thresholds 85/90/95 % (Spearman 0.93–0.98); player-level shares unreliable where D ≈ 0 | `demand_measure_validation.md` |

## 9. Limitations and threats to validity

1. **Sample size: players, not plays, limit power.** n = 52–57 per position. Effects of Δ < 0.27–0.33 (WR) were not reliably detectable, and most secondary contrasts could only be estimated.
2. **Conservative registered bootstrap** (D2, documented). It is wider than the sampling distribution near the null, especially for DB (1.9× Wald) and OL (1.7×).
3. **Selection.** Only players with ≥ 100 primary opportunities are analysed. Eligibility selects mainly on draft capital. Selection on deep-route level could inflate the WR target by ≈ 0.04.
4. **Associational design.** Route, coverage and role assignment are partly *caused* by athleticism. Defender identity and quality, play-call intent and injuries are unobserved. Only cohort players are tracked.
5. **Outcome scope.** H1/H5 outcomes are realized game *movement*, not performance. H2 is the only performance-type outcome, and it has low player-level reliability.
6. **Measurement.** The official-40 reliability is unknown, and the combine test–retest is within one session.
7. **Covariates.** Time-to-throw is partly post-snap (a sensitivity analysis removed it, with no change). Pooled reliabilities are inflated by position differences, so within-position values are reported.
8. **Multiplicity and exploration.** Only the registered families are interpreted. Subgroup and season-split estimates are descriptive. Some unadjusted subset intervals exclude 0 (e.g. the 2025-only WR fit); these are not findings.
9. **Not computed:**
   - eligibility (inverse-probability) weights: the frozen engine has no weights;
   - the registered demand-moderated-coefficient benchmark (spec §1.4: B1/B2 player-grouped CV).

## 10. What we can claim, and what we cannot

**We can claim:**
- In this cohort, **combine tracked peak speed is associated with in-game play-maximum speed** for WR (ρ ≈ 0.5–0.6) and, across DL as a whole, for DL (≈ 0.55). It is weaker for DB (≈ 0.15–0.3) and small for OL (≈ 0.03–0.1). These are separately estimated, descriptive levels.
- **No resolved task-conditioning.** Among WRs, the deep-vs-short difference is not distinguishable from zero (Δ 0.09, CI [−0.09, 0.40]). The same holds for every other position. For DL, a pass-rush advantage ≥ 0.15 is not supported.
- **No detected incremental value of tracked peak speed** over the official 40 for WR deep-route separation. No combine speed measure predicted held-out players' deep separation better than the mean.
- **The DL speed association is substantially sensitive to role and body-weight adjustment** (registered, Holm-supported). Role alone and weight alone each remove most of it (descriptive).
- The registered pipeline is validated, reproducible and conservative. Every decision follows the frozen protocol and its logged deviations.

**We cannot claim:**
- that combine speed **causes** better game movement or performance, or that it has no or negative effects (in particular the adjusted DL value);
- that task demand moderates speed translation, or that it does not: everything is inconclusive or uninformative, and absence of evidence is not evidence of absence;
- **equivalence** for any contrast beyond the registered DL(a) equivalence-type statement;
- anything about **football performance** for DB, DL or OL (not analysed), or about separation beyond deep and short routes of thrown passes;
- **novelty** relative to the literature: the full texts of the closest prior work have not been read (CLAUDE.md literature rule);
- generalization beyond REG 2023–2025, the 510-player cohort, players with ≥ 100 opportunities, or the positions studied.

## 11. Remaining research opportunities (each would need its own registration)

1. **More players.** Add future seasons and draft classes. Power is player-limited: doubling the players raises WR power far more than extra plays do.
2. **Performance outcomes.** DL pressure generation (`time_to_pressure`) and OL pressure allowed, with role and body type modelled explicitly. Registered as new analyses, never as re-analyses.
3. **The demand-moderated coefficient** (spec §1.4). Benchmark B1/B2 by player-grouped CV as a candidate algorithmic contribution; it was not run here.
4. **Bootstrap for crossed designs.** A validated alternative to the registered player bootstrap, such as copy-specific team-season labels or a parametric bootstrap. D2 was rejected for *this* protocol, but the problem is general.
5. **Weighted REML** (pseudo-likelihood) for eligibility weights.
6. **Role-aware DL models** that treat role as a mediator, e.g. joint models of role assignment and game speed, rather than adjusting for it.
7. **Better measurement:**
   - per-attempt official 40 times, to identify R_F;
   - longer separation windows or defender-quality-adjusted separation, to raise player-level reliability above 0.44.
8. **The original B + C programme** (exposure-aware acceleration–speed frontier; capacity-constrained change of direction), shelved after Phase 2 feasibility checks. It needs better game-acceleration measurement first.
