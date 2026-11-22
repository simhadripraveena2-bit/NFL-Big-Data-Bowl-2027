# H1-DL(b): interpretation audit (role, weight and speed in defensive linemen)

**Scope:**
- This audit is limited to *interpreting* the supported secondary result H1-DL(b) (Holm-adjusted p = 0.032).
- **Unchanged:** the registered model, hypothesis, outcome and decision, and the Holm family.
- **All additional numbers are descriptive diagnostics:** point estimates with delta-method (Wald) SEs. They are not tests.

**Provenance:**
- `scripts/dl_role_weight_diagnostics.py` → `experiments/secondary/20261122T015315Z/dl_role_weight_diagnostics.json`.
- Same frame and estimator as the registered run. It reproduces the registered base (0.549) and adjusted (−0.267) pooled values exactly.

## 1. Exact definition of the pooled DL translation

**Registered wording:**
- Protocol §2: "the pooled DL translation shrinks after alignment (EDGE / interior) and combine weight are adjusted for".
- Spec §1.4: "Compare ρ (pooled DL, both contexts) with ρ from a model adding alignment (EDGE vs interior) × context fixed effects and standardised combine weight".
- §12, supported iff "the pooled-minus-adjusted ρ difference > 0, with the 95 % CI excluding 0".

**Operational definition** (declared in `scripts/run_secondary.py` before the run). For model M ∈ {registered, adjusted}, the registered bivariate DL model is:

y_ijc = μ_c + γ_c′w_ij + κ_c a_ij + β_c^(M) x_i + [θ_c′ z_i]^(adjusted only) + b_ic + τ_t(ij) + ε_ijc,  c ∈ {pass rush, run}

where:
- x_i is tracked combine peak speed, standardised in-sample (var x = 1);
- w_ij are the registered play covariates (including play-level lined-up position);
- **adjusted only:** z_i = (EDGE_i, weight_i), each entered with context-specific coefficients. EDGE_i is 1 if the player's modal REG alignment is EDGE. weight_i is combine weight, standardised over all DL combine participants.

The quantities are:

ρ_c^(M) = β_c^(M) / √( (β_c^(M))² + Σ_b,cc^(M) )   (registered estimand, spec §1.1)

ρ̄^(M) = ½ ( ρ_pass-rush^(M) + ρ_run^(M) )   (pooled DL translation)

Δ_b = ρ̄^(registered) − ρ̄^(adjusted)   (H1-DL(b) quantity; predicted > 0)

**Relation to the wording:**
- "Pooled DL, both contexts" is read as one summary over the two registered task contexts, from the *registered bivariate* model.
- "Alignment × context fixed effects" is implemented literally.
- "Standardised combine weight" is entered × context. A main-effect version gives the same answer (§2).

## 2. Why the average of the two context estimates is appropriate

1. **It stays inside the registered model.** H1-DL(a) and H1-DL(b) are then computed from the same bivariate fit and estimand ρ_c. A separate single-context "pooled-plays" model would be a new, unregistered model: it would treat pass-rush and run plays as one context, mixing context mean differences into the player variance.
2. **Equal weights describe the two tasks, not the deployment mix.** Play counts per context (55 % pass rush) are partly a consequence of role and athleticism, which are exactly what the adjustment is about. Equal weighting avoids letting deployment define the estimand.
3. **The conclusion does not depend on the weighting** (descriptive point estimates):

| pooling of the two contexts | Δ_b (registered − adjusted) |
|---|---|
| equal mean (registered operationalisation) | 0.816 |
| play-weighted (55.3 % pass rush) | 0.809 |
| pass-rush context only | 0.749 |
| run context only | 0.882 |

Because the drop is large in *each* context, any convex weighting lies between 0.75 and 0.88.

4. **Weight specification.** Entering weight as a main effect instead of × context gives an adjusted pooled ρ of −0.286, so Δ_b ≈ 0.835. This is also insensitive.

## 3. Correlation structure (combine data and role)

The 53 eligible DL are 25 EDGE and 28 interior by modal alignment.

| | peak speed | combine weight | EDGE |
|---|---|---|---|
| peak speed | 1 | **−0.80** | **+0.72** |
| combine weight | | 1 | **−0.82** |
| EDGE | | | 1 |

**Context:**
- Speed–weight correlation over all 93 DL combine participants with a valid tracked 40: −0.83.
- Role means:

| role | n | peak speed | weight |
|---|---|---|---|
| EDGE | 25 | 10.57 yd/s (SD 0.33) | 258 lb (SD 11) |
| interior | 28 | 9.71 yd/s (SD 0.49) | 304 lb (SD 20) |

- **Within-role** speed–weight correlation: EDGE −0.06; interior −0.69.

## 4. How collinearity affects the adjusted estimate and its uncertainty

| peak speed regressed on | R² | VIF | SD of speed left after conditioning (share of total) |
|---|---|---|---|
| role | 0.52 | 2.1 | 0.69 |
| weight | 0.64 | 2.8 | 0.60 |
| role + weight | 0.66 | 2.9 | 0.59 |

**Collinearity is substantial but not extreme.** About two-thirds of the between-player variation in combine speed is shared with role and weight.

**Correction to `dl_secondary_results.md`.** That note cited the Phase 3 figure "|ρ| 0.80–0.97, one dimension", which concerned the 40, the 10-yd split, peak speed and weight together, and called the adjusted model "weakly identified". For the adjusted model, the relevant collinearity is VIF ≈ 2.9. The model is identified; it is imprecise rather than unidentified.

**Consequences:**
1. **Precision.** The SE of the pooled ρ rises from 0.099 (registered model) to 0.227 (adjusted).
   - About √2.9 ≈ 1.7× of that comes from the predictor variance shared with role and weight.
   - The rest comes from the smaller remaining between-player variance (Σ_b falls by about half).
   - The adjusted pooled ρ is −0.27 ± 0.45 (descriptive 95 % Wald band [−0.71, 0.18]): **its sign is not determined.**
2. **Scale of the estimand.** The registered ρ_c uses the *total* SD of x (var x = 1) with the *partial* slope β_c. With 41 % of x's SD absorbed by role and weight, this overstates the magnitude of the adjusted association.
   - Using the conditional SD (0.59) instead, the adjusted pooled value is −0.16 instead of −0.27 (descriptive).
   - The registered *drop* is unaffected. The adjusted *level* is not a partial correlation and should not be read as one.
3. **Extrapolation.** Fast heavy players and slow light players are rare, so the adjusted slope leans on few players at the edges of the joint distribution.

## 5. Four conditioning sets (descriptive)

Same registered model and outcome. Pooled = mean of the context ρ. Wald SEs.

| conditioning | ρ pass rush | ρ run | **pooled** (SE) | pooled with conditional SD of x |
|---|---|---|---|---|
| none: unadjusted pooled association (registered model) | 0.568 | 0.530 | **0.549** (0.099) | 0.549 |
| role (EDGE × context) | −0.030 | −0.074 | **−0.052** (0.219) | −0.037 |
| weight (× context) | 0.018 | −0.176 | **−0.079** (0.241) | −0.048 |
| role and weight (registered adjusted) | −0.181 | −0.352 | **−0.267** (0.227) | −0.165 |

**Reading:**
- **Unadjusted:** across all DL, faster combine athletes reach higher play-maximum speeds (ρ ≈ 0.55).
- **Conditional on role only, or on weight only:** the association is about zero (−0.05 and −0.08), with SEs of about 0.22–0.24.
- Either proxy alone accounts for essentially all of the unadjusted association.
- **Conditional on both:** the point estimate becomes more negative (−0.27). Conditioning on two strongly correlated proxies of the same body-type and role dimension removes more shared variance and leaves an imprecise, unstable residual slope.
- The negative value is not a substantive finding: its descriptive band includes 0, and both single-proxy versions are ≈ 0.

## 6. Why the adjusted negative estimate must not be interpreted causally

1. **Role is a mediator, not a confounder.** Lighter, faster athletes are *deployed* on the edge partly *because* of their athletic profile (protocol §7). Conditioning on role removes part of any pathway speed → role → game speed. The adjusted quantity is "association within role", not "effect of speed".
2. **Conditioning can induce bias (collider-type).** Role assignment depends on speed and on unmeasured attributes (pass-rush skill, length, technique) that may also affect game speed. Within a role, these can be negatively associated with combine speed, which can produce a spurious negative slope.
3. **No experiment, no instrument.** Combine speed is not assigned. Weight, role and speed come together as one athletic profile. The model has no source of variation that changes speed while holding the profile fixed.
4. **Statistical instability.** The adjusted ρ has SE ≈ 0.23. Its sign changes across reasonable conditioning sets (§5), and its magnitude depends on the SD convention (§4).
5. **Outcome.** Play-maximum speed is *realized game movement*, not get-off time and not pass-rush performance. Even a causal speed → movement effect would not establish a speed → performance effect.

**What H1-DL(b) establishes (registered, Holm-adjusted p = 0.032):** the pooled DL association between combine peak speed and game speed is **substantially sensitive to adjustment for role and body weight**.
- Descriptively, role alone and weight alone each remove most of it (§5).
- This is a statement about where the association sits in the athletic profile. It does **not** uniquely identify a mechanism (role, weight and speed are one correlated profile).
- **It is not a statement that speed has no effect, or a negative effect.**

## 7. Consistency across EDGE and interior groups

**These are the same two subgroup fits as in the secondary run (exploratory); no other subgroups were examined.**

| group | n | ρ pass rush (SE) | ρ run (SE) | pooled (SE) | within-group speed–weight r |
|---|---|---|---|---|---|
| EDGE | 25 | 0.100 (0.242) | −0.009 (0.254) | 0.046 (0.234) | −0.06 |
| interior | 28 | 0.002 (0.213) | 0.011 (0.226) | 0.007 (0.206) | −0.69 |

**Reading:**
- Within each role, the association between combine peak speed and game speed is about zero, in both contexts.
- This agrees with the role-conditioned full-sample estimate (−0.05) and with the sensitivity reading of H1-DL(b).
- It does **not** reproduce the negative "role and weight" estimate, which supports treating that value as unstable rather than substantive.
- The subgroups are small (25 and 28). Their SEs (≈ 0.21–0.25) do not exclude moderate within-role associations of either sign. **"About zero" means "no detectable association", not "no association".**

## 8. Summary for the scientific conclusions

| statement | status |
|---|---|
| Across DL, combine peak speed is associated with game play-maximum speed (ρ ≈ 0.55) | descriptive, registered model |
| This association is substantially sensitive to adjustment for EDGE/interior role and body weight (Δ_b = 0.82, 95 % CI [0.16, 1.54]) | **registered secondary hypothesis H1-DL(b), supported after Holm (p = 0.032)** |
| Role alone and weight alone each remove most of the pooled association | descriptive (this audit) |
| The joint role-and-weight model identifies the mechanism | **not claimed** |
| Conditional on role, or on weight, alone: ≈ 0; within EDGE and within interior: ≈ 0 | descriptive; consistent with the above |
| The adjusted value −0.27 | **not interpretable**: imprecise (±0.45), sign unstable across conditioning sets, inflated by the total-SD scaling, not causal |
| Speed causes (or does not cause) DL game speed or pass-rush success | **not addressed by these data** |
