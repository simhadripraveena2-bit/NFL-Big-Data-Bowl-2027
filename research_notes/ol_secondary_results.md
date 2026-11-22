# H5: offensive linemen as a comparison group (secondary)

**Status:**
- **H5(b)** is in the registered secondary Holm family.
- **H5(a)** and **H5(c)** are estimation only. H5(a) is also the registered OL negative control N2.

**Provenance:**
- Run `experiments/secondary/20261122T015315Z/`, commit `18fca76`, seed 8003.
- Δ_WR and its bootstrap draws come from the frozen primary run (seed 4004).
- Display: notebook 10.

**Sample:** 53 OL; 64,285 plays (pass block 38,266; run 26,019); 65 team-seasons.

## 1. Registered specification (unchanged)

**Contexts:**
- **pass block** = pass play with `pass_rushers_encountered` non-null;
- **run** = run play.

**Outcome:** play-maximum speed.

**Model:** the registered bivariate REML.
- Covariates: context, lined-up position, down, distance, formation, season; NFL year.
- Inference: full REML player-cluster bootstrap, B = 2,000.

**Quantities:**
- **H5(a):** Δ_OL = ρ_pass-block − ρ_run. No direction assumed. "Consistent with the demand model" iff the 90 % CI lies within ±0.15.
- **H5(b):** Δ_WR − Δ_OL > 0, with the CI from independent player bootstraps.
- **H5(c):** OL overall translation vs the value the cross-fitted demand meta-regression predicts for OL when fitted **without** the OL cells.
  - Operationalised before the run: OL pooled ρ = mean of the two contexts; registered cross-fit halves (seed 3503); 90 % prediction interval ± t(4)·√(se² + ω² + se_fit²); averaged over the two swaps.

## 2. Results

| | estimate | 95 % CI | 90 % CI | p (unadj. / Holm) | reading |
|---|---|---|---|---|---|
| ρ_pass-block / ρ_run | 0.108 / 0.025 | Wald SE 0.15 / 0.16 | — | — | — |
| raw slopes per 0.25 yd/s of combine peak | 0.014 / 0.003 yd/s | — | — | — | — |
| **H5(a) Δ_OL** | **0.084** | [−0.457, 0.636] (Wald [−0.22, 0.39]) | [−0.315, 0.522] | 0.675 / — | **uninformative**: the CI is far wider than ±0.15 |
| **H5(b) Δ_WR − Δ_OL** | **0.007** | [−0.573, 0.627] | [−0.422, 0.498] | 0.833 / 1.00 (Holm step 3) | **inconclusive** |
| **H5(c)** observed OL pooled ρ vs prediction | observed 0.068 vs predicted 0.331 | — | PI [−0.135, 0.798] | — | **inside the prediction interval**: uninformative (PI width 0.93) |

**H5(c) per cross-fit swap:**

| swap | predicted | 90 % PI | observed |
|---|---|---|---|
| D from half A, ρ from half B | 0.169 | [−0.29, 0.63] | 0.011 |
| D from half B, ρ from half A | 0.494 | [0.02, 0.97] | 0.125 |

The between-cell heterogeneity was estimated at ω² = 0 in both swaps.

## 3. The registered OL negative control (N2 = H5(a))

**What it is designed to detect.** Both OL contexts have essentially zero near-top-speed demand: D = 0.008 (pass block) and 0.009 (run). A sizeable OL context contrast would signal that the H1 machinery picks up context differences unrelated to speed demand, such as play-type differences in outcome variance, scheme or tracking.

**What would indicate a problem.** A clearly non-zero Δ_OL, with a CI excluding 0.

**Result.** Δ_OL = 0.084, CI [−0.46, 0.64].
- There is **no sign of a spurious context contrast**.
- But the interval is too wide to show the control "passes" in an equivalence sense: the 90 % CI is not within ±0.15.
- The registration anticipated this outcome at n = 53 (§12).
- **No equivalence and no absence of an effect is claimed.**

## 4. Interpretation

**H5(b).** The WR-minus-OL difference in task contrasts is estimated at ≈ 0. Both components are uncertain: Δ_WR is 0.09 (inconclusive) and Δ_OL is 0.08.

**H5(c).** OL translation is lower than the demand model predicts (0.07 vs 0.33), but well inside a prediction interval almost 1.0 wide. As stated in advance, the 11-cell meta-regression cannot discriminate.

**Notable but descriptive.** The OL association between combine peak speed and game play-maximum speed is small in both contexts (ρ 0.11 and 0.03; raw slopes ≈ 0.01 yd/s per 0.25 yd/s). This contrasts with WR (≈ 0.5) and DL (≈ 0.55). It is a between-position comparison of separately estimated quantities, not a test.

| category | what the data say for OL |
|---|---|
| **1. Combine athletic capacity** | Tracked 40 peak speed; within-OL best-of-2 reliability ≈ 0.97 (D3) |
| **2. Realized game movement** | Weak association with OL play-maximum speed (ρ ≈ 0.03–0.11); OL rarely approach top speed (D ≈ 0.01) |
| **3. Actual football performance** | **Not analysed.** Pressure allowed, sacks allowed and peak pressure probability exist but are not in the registered H5 analyses. Nothing here bears on blocking quality |
| **4. Reliability and context** | Player-context reliability of game speed is high (0.94 / 0.90): players are measured precisely, but they differ little and their game speed does not track combine speed. Lined-up position (G / T / C) is a covariate |
