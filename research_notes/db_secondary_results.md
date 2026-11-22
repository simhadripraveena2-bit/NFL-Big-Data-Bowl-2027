# H1-DB: defensive backs (secondary, Holm family)

**Status:** registered secondary hypothesis (demoted from primary in Phase 3.5 for power). Tested once, under the registered Holm procedure. **Not promoted.**

**Provenance:**
- Run `experiments/secondary/20261122T015315Z/`, commit `18fca76`, seed 8001.
- Data: the single join `20261121T135032Z`.
- Display: notebook 10.

## 1. Registered specification (unchanged)

**Hypothesis:** Δ_DB = ρ_man − ρ_underneath-zone > 0.

**Contexts** (`coverage_assignment` on pass plays):
- **man** = MAN;
- **underneath zone** = any other assignment except DEEP_*, QUARTERS_*, NO_ASSIGNMENT and PREVENT;
- deep zone (DEEP_* / QUARTERS_*) is a third context, used only in the three-context secondary fit.

**Outcome:** play maximum speed `vmax_play`.

**Model:** registered bivariate REML.
- Covariates: team coverage type, lined-up position, down, distance bin, time-to-throw bin, season; NFL year.
- Random effects: player × context and team-season.

**Inference:**
- `h1_registered_test`: full REML player-cluster percentile bootstrap, B = 2,000.
- Holm family {H1-DB, H1-DL(a), H1-DL(b), H5(b)} at α = 0.05.

**Sample:** 52 DBs; 16,643 plays (man 8,218; underneath zone 8,425); 69 team-seasons.

## 2. Result

| quantity | estimate | uncertainty |
|---|---|---|
| ρ_man / ρ_underneath | 0.290 / 0.150 | Wald SE 0.17 / 0.19 |
| **Δ_DB** | **0.139** | **95 % CI [−0.61, 1.05]** (bootstrap); 90 % [−0.47, 0.90]; bootstrap SE 0.415 |
| Wald check (delta method) | 0.139 | SE 0.223; 95 % [−0.30, 0.58] |
| p, unadjusted / Holm-adjusted | 0.691 / 1.00 | Holm step 2 (α = 0.0167); Holm-level CI [−0.82, 1.24] |
| raw slopes per 0.25 yd/s of combine peak | man 0.058, underneath 0.028 yd/s | — |
| three-context fit (secondary): ρ man / deep zone / underneath | 0.293 / 0.091 / 0.146 | SE 0.17–0.19 |

**Decision (§12): INCONCLUSIVE.**
- Not supported: the Holm-adjusted p is 1.0 and the CI includes 0.
- Not falsified: the 90 % upper bound (0.90) is far above 0.15.
- **Reported as estimation:** the data are compatible with Δ_DB anywhere from about −0.6 to +1.0.

**Precision:**
- The registered bootstrap SE (0.415) is 1.86× the Wald SE (0.223). This is the documented over-dispersion of the registered bootstrap for DB (D2; Phase 4 ratio ≈ 1.75; simulated power 0.025 at Δ = 0.2).
- Even with the Wald SE, the interval includes 0.
- As stated before the run, an H1-DB non-rejection is uninformative.

## 3. Interpretation by category

| category | what the data say for DBs |
|---|---|
| **1. Combine athletic capacity** | Tracked 40 peak speed. Within-DB best-of-2 reliability ≈ 0.96 (D3); 102 DBs with a valid tracked 40. |
| **2. Realized game movement** | Faster combine DBs reach somewhat higher play-maximum speeds in every coverage role: ρ ≈ 0.29 in man, 0.15 underneath, 0.09 deep zone. These are weaker than for WR (0.49–0.58) or DL (0.53–0.57). The man-vs-underneath difference is not resolved. |
| **3. Actual football performance** | **Not measured.** The data contain no DB coverage-performance outcome: no targets allowed or separation allowed per defender for the cohort. Nothing here says faster DBs *cover* better. |
| **4. Reliability and context** | Player-context reliability of game speed is only 0.65–0.68 (lower than WR 0.82–0.85 and DL 0.86–0.94); residual SD is ≈ 1.4–1.5 yd/s. Coverage roles mix CBs, slot CBs and safeties; lined-up position is a covariate, but role is partly a *consequence* of speed (a mediator). Near-top-speed demand is low in all DB contexts (D: man 0.058, deep zone 0.028, underneath 0.014). |

**Limitations:**
- With n = 52 and noisy coverage-context speeds, effects below about 0.4 cannot be resolved.
- The registered bootstrap is conservative for DB.
- Associational only: assignment of DBs to man coverage may itself depend on speed.
