# H1-DL(a) and H1-DL(b): defensive linemen (secondary, Holm family)

**Provenance:**
- Run `experiments/secondary/20261122T015315Z/`, commit `18fca76`.
- Seeds: 8002 for (a); 8101–8104 for (b).
- Data: the single join.
- Display: notebook 10.

**Sample:** 53 DL (25 EDGE and 28 interior by modal REG alignment); 34,154 plays (pass rush 18,882; run 15,272); 69 team-seasons.

## 1. Registered specification (unchanged)

**Contexts:**
- **pass rush** = pass play with `player_get_off` non-null;
- **run** = `pass_result == ""`.

**Outcome:** play maximum speed `vmax_play` over the tracked play.
- This is **not** get-off speed and not a pass-rush outcome.
- Pass-rush plays are only *identified* by a recorded get-off.

**Model:** registered bivariate REML.
- Covariates: context, play-level lined-up position, down, distance, formation, season; NFL year.
- Random effects: player × context and team-season.

**Inference:** full REML player-cluster bootstrap, B = 2,000, within the Holm family.

**H1-DL(a):** Δ_DL = ρ_pass-rush − ρ_run > 0.

**H1-DL(b):** "the pooled DL translation shrinks after alignment (EDGE / interior) and combine weight are adjusted for".
- **Operational definition, declared in the runner before the run.** The registration does not define "pooled" numerically.
  - Pooled ρ = mean of ρ_pass-rush and ρ_run.
  - The adjusted model is the registered model **plus** the player's modal alignment (EDGE = 1) × context **plus** standardised combine weight × context. Weight is standardised over all DL combine participants.
  - Quantity: pooled_registered − pooled_adjusted. Predicted > 0.
  - Inference: a paired registered-scheme bootstrap (both models refitted on the same resamples).

## 2. Results

**Per-context estimates:**

| quantity | estimate | uncertainty |
|---|---|---|
| ρ_pass-rush / ρ_run (registered model) | 0.568 / 0.530 | Wald SE 0.10 / 0.11 |
| raw slopes per 0.25 yd/s of combine peak | pass rush 0.088, run 0.066 yd/s | — |

**H1-DL(a):**

| quantity | estimate | uncertainty |
|---|---|---|
| **Δ_DL** | **0.038** | **95 % CI [−0.229, 0.154]**; 90 % [−0.191, 0.124]; SE 0.095 |
| Wald check | 0.038 | SE 0.069; 95 % [−0.10, 0.17] |
| p, unadjusted / Holm-adjusted | 0.931 / 1.00 | Holm step 4 (α = 0.05) |
| **Decision (§12)** | **FALSIFIED** under the registered rule | the 90 % CI upper bound (0.124) is below the SESOI 0.15 |

**H1-DL(b):**

| quantity | estimate | uncertainty |
|---|---|---|
| pooled ρ: registered model → adjusted model | 0.549 → −0.267 | adjusted per-context ρ: −0.18 (pass rush), −0.35 (run); Wald SE ≈ 0.24 |
| **pooled − adjusted** | **0.816** | **95 % CI [0.160, 1.538]**; 90 % [0.323, 1.476]; SE 0.359 |
| p, unadjusted / Holm-adjusted | **0.008 / 0.032** | Holm step 1 (α = 0.0125); Holm-level CI [0.031, 1.659] |
| **Decision (§12)** | **SUPPORTED** (secondary family, Holm-adjusted) | |

**Exploratory, not registered as tests:** role subgroups fitted with the registered model, Wald CIs.

| subgroup | ρ_pass-rush | ρ_run |
|---|---|---|
| EDGE only (25) | 0.10 (SE 0.24) | −0.01 (SE 0.25) |
| interior only (28) | 0.00 (SE 0.21) | 0.01 (SE 0.23) |

## 3. What the two results mean together

**H1-DL(a): the pass-rush vs run contrast.**
- The registered equivalence-type rule classifies it as falsified: a pass-rush translation that exceeds the run-play translation by ≥ 0.15 is not supported by these data.
- This is evidence **against a meaningful difference** of that size. It is not evidence that the difference is exactly zero.
- The falsification rule uses the unadjusted 90 % interval, as registered.

**H1-DL(b): sensitivity to role and body weight.**
- **Registered statistical result:** supported after Holm adjustment (p = 0.008; Holm-adjusted p = 0.032).
- **Wording (final, after the interpretation audit):** the pooled DL association between combine peak speed and game play-maximum speed (ρ ≈ 0.55) is **substantially sensitive to adjustment for role (EDGE vs interior) and body weight**.
- **Descriptive audit** (`dl_role_weight_interpretation.md`, not a test):
  - role alone and weight alone **each remove most of the pooled association** (pooled ρ −0.05 and −0.08);
  - within EDGEs and within interior linemen the association is near zero (exploratory subgroups).
- **Not claimed:** that the joint role-and-weight model uniquely identifies the mechanism. Role, weight and speed form one correlated athletic profile, and these data cannot separate them.

**Necessary caveats:**
- **Collinearity.** In DL, combine speed, the 40, the 10-yd split and weight are close to one dimension (|ρ| 0.80–0.97; Phase 3). The adjusted model asks for the speed effect at fixed weight and role, which is weakly identified (*corrected in §5: identified but imprecise, VIF ≈ 2.9*). Hence the wide adjusted-ρ CIs and the implausibly negative point estimates. The registered quantity is the *drop*, and the drop is well outside 0. The adjusted ρ itself should not be read as "speed slows DL down".
- **Mediation.** Role is partly a consequence of athletic profile: lighter, faster players are deployed on the edge. The adjusted estimate is therefore not "the effect of speed". It is the association that remains within role and body type. The registration anticipated this (protocol §7: role as mediator).
- **Not get-off speed.** The outcome is play-maximum speed, not get-off time or pass-rush success. **Nothing here is performance evidence**, and get-off is not interpreted as independent evidence.

## 4. Interpretation by category

| category | what the data say for DL |
|---|---|
| **1. Combine athletic capacity** | Tracked 40 peak speed (within-DL best-of-2 reliability ≈ 0.99, D3), but nearly collinear with weight, the 40 and the 10-yd split |
| **2. Realized game movement** | Pooled association with play-maximum speed ρ ≈ 0.55 in both contexts. It is substantially sensitive to role and body-weight adjustment (H1-DL(b) supported); near zero within role |
| **3. Actual football performance** | **Not analysed.** Pressure (`time_to_pressure`) exists but is not part of the registered H1 analyses. A movement association would not establish a pressure association |
| **4. Reliability and context** | Player-context reliability is high (0.94 pass rush, 0.86 run). Demand is low in both contexts (D 0.026 / 0.013). The alignment covariate is in every model; the role mix is 25 EDGE and 28 interior |

## 5. Interpretation audit (added 2026-11-22; results and decisions unchanged)

See `dl_role_weight_interpretation.md`. Two clarifications to the text above:

1. **Collinearity is substantial, not extreme.** Within the 53 eligible DL, peak speed vs weight is r = −0.80, and peak speed regressed on role and weight gives R² 0.66 (VIF ≈ 2.9). The adjusted model is therefore identified but imprecise. The phrase "weakly identified" (and the Phase 3 "|ρ| 0.80–0.97" figure, which concerned the 40, split, peak and weight jointly) overstated this.
2. **The adjusted ρ (−0.27) is not interpretable.**
   - Conditioning on role alone gives −0.05, and on weight alone −0.08. Within EDGE and within interior, it is ≈ 0.
   - The registered formula scales the partial slope by the total SD of speed. Using the conditional SD gives −0.16.
   - The registered *drop* (H1-DL(b), supported) is unaffected.
