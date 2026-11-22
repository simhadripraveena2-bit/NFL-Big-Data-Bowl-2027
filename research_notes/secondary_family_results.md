# Registered secondary analyses: family-level summary

**Scope.** The registered secondary layer, under the D4 hierarchy. Nothing here changes the primary result (H1-WR, inconclusive) or the H2 estimation report, and nothing is promoted to primary.

**Provenance:**
- **Run:** `experiments/secondary/20261122T015315Z/` (`secondary_result.json`, `bootstraps.npz`), run once from commit `18fca76`.
- **Runner:** `scripts/run_secondary.py`. Its operational choices and seeds were declared in its docstring before the run.
- **New code:** `src/nfl_bdb/models/secondary.py`, unit-tested. It re-uses the frozen estimator and bootstrap.
- **Data:** the single join `20261121T135032Z`.
- **Display:** `notebooks/10_secondary_analysis.ipynb`.
- **Per-position notes:** `db_secondary_results.md`, `dl_secondary_results.md`, `ol_secondary_results.md`.

## 1. Hierarchy

| tier | analyses | inference |
|---|---|---|
| primary (done, frozen) | H1-WR | inconclusive: Δ 0.090, 95 % CI [−0.089, 0.400] |
| secondary, estimation (done) | H2 | no incremental information detected; registered label inconclusive |
| **secondary Holm family (this run)** | **H1-DB, H1-DL(a), H1-DL(b), H5(b)** | Holm, α = 0.05, m = 4; bootstrap p-values; predicted direction > 0 for all |
| secondary estimation only (this run) | H5(a) (= OL negative control N2), H5(c), H1-global | estimates and intervals, no test |
| descriptive (this run) | H1-TE | point estimates with Wald CIs |
| exploratory (this run) | DL role subgroups | labelled; not tests |

## 2. Holm family

| hypothesis | estimate | 95 % CI | Holm step / level | Holm-level CI | p unadjusted | **p Holm-adjusted** | registered decision |
|---|---|---|---|---|---|---|---|
| H1-DL(b): pooled − adjusted DL ρ (role/weight sorting) | 0.816 | [0.160, 1.538] | 1 / 0.0125 | [0.031, 1.659] | 0.008 | **0.032** | **SUPPORTED** |
| H1-DB: ρ_man − ρ_underneath | 0.139 | [−0.609, 1.050] | 2 / 0.0167 | [−0.820, 1.240] | 0.691 | 1.00 | inconclusive |
| H5(b): Δ_WR − Δ_OL | 0.007 | [−0.573, 0.627] | 3 / 0.025 | [−0.744, 0.739] | 0.833 | 1.00 | inconclusive |
| H1-DL(a): ρ_pass-rush − ρ_run | 0.038 | [−0.229, 0.154] | 4 / 0.05 | [−0.229, 0.154] | 0.931 | 1.00 | **falsified** (registered equivalence-type rule: 90 % upper bound 0.124 < 0.15) |

**How to read the table:**
- Holm step-down: H1-DL(b) is rejected at 0.0125 (p = 0.008). The procedure then stops at H1-DB (0.691 > 0.0167).
- Adjusted p-values are the monotone Holm adjustments.
- "Falsified" follows the registered §12 rule, which uses the unadjusted 90 % interval. It means a SESOI-sized pass-rush-vs-run difference is not supported. It does not mean the difference is exactly zero.
- **The one supported secondary result (H1-DL(b)) is a role-sorting result about game movement.** It is not a performance result (see `dl_secondary_results.md` for the collinearity and mediation caveats).

**§9 sensitivity** (Holm over the original {H1-WR, H1-DB, H2}; reported only as a sensitivity analysis):
- p = 0.211 / 0.691 / 0.708; Holm-adjusted 0.633 / 1.00 / 1.00; nothing rejected.

## 3. Estimation-only analyses

| analysis | estimate | interval | reading |
|---|---|---|---|
| H5(a) Δ_OL (also the OL negative control N2) | 0.084 | 95 % [−0.457, 0.636]; 90 % [−0.315, 0.522] | no spurious contrast visible, but uninformative: the 90 % CI is not within ±0.15 |
| H5(c) OL pooled ρ: observed vs demand-model prediction (fitted without OL) | 0.068 vs 0.331 | 90 % PI [−0.135, 0.798] | inside the PI; uninformative (width 0.93), as expected in advance |
| H1-global λ (cross-fitted demand meta-regression; 11 cells) | 0.94 (D: half A, ρ: half B); 0.23 (swap); averaged 0.58 | model SE ≈ 1.1–1.2; cell-cluster bootstrap 95 % [−5.8, 4.0] and [−4.3, 8.2] | **descriptive, uninformative.** Half-sample ρ are noisy (TE halves of 8–9 players: ρ_deep −0.30 vs +0.86). Estimated ω² = 0 |

**H1-TE (descriptive only, n = 17):**
- ρ_deep 0.30 (SE 0.27); ρ_short 0.21 (SE 0.26).
- Δ_TE 0.08 (Wald SE 0.18; 95 % [−0.27, 0.44]).

**Exploratory (DL):** within-role fits give ρ ≈ 0 for EDGE (0.10 / −0.01) and interior (0.00 / 0.01), each with SE ≈ 0.21–0.25.

## 4. Cross-position picture (separately estimated; not a test)

| position (contexts h / l) | ρ_h | ρ_l | Δ (95 % CI) | player-context reliability h / l | demand D h / l |
|---|---|---|---|---|---|
| WR (deep / short), primary | 0.576 | 0.486 | 0.090 [−0.089, 0.400] | 0.85 / 0.82 | 0.183 / 0.004 |
| TE (deep / short), descriptive | 0.296 | 0.213 | 0.083 (Wald [−0.27, 0.44]) | 0.77 / 0.91 | 0.184 / 0.023 |
| DB (man / underneath) | 0.290 | 0.150 | 0.139 [−0.609, 1.050] | 0.65 / 0.68 | 0.058 / 0.014 |
| DL (pass rush / run) | 0.568 | 0.530 | 0.038 [−0.229, 0.154] | 0.94 / 0.86 | 0.026 / 0.013 |
| OL (pass block / run) | 0.108 | 0.025 | 0.084 [−0.457, 0.636] | 0.94 / 0.90 | 0.008 / 0.009 |

**What is consistent across positions:**
- **No position shows a resolved within-position task contrast.** Every Δ CI includes 0, and the DL contrast is bounded below the SESOI.
- What differs strongly is the **overall level** of translation: WR and DL ≈ 0.5–0.6; DB and TE ≈ 0.15–0.3; OL ≈ 0.03–0.1.
- In DL, that overall level is explained by role and body-type sorting (H1-DL(b)).
- This pattern does not follow the near-top-speed demand gradient in any testable way: the H1-global λ is uninformative.

## 5. Interpretation rules applied to every position

The analyses separate four categories, and no relationship in one is taken to establish another:

1. **Combine athletic capacity.** Tracked 40 peak speed.
   - Within-position reliability is high: best-of-2 R_x 0.94 (WR) to 0.99 (DL) (D3).
   - It is collinear with the 40, the 10-yd split and, in DL, weight.
2. **Realized game movement.** Play-maximum speed: pre-pass for WR/TE, whole play for DB/DL/OL. This is what H1 and H5 measure. A combine–movement association says a player *moves* faster in games, not that he *plays* better.
3. **Actual football performance.** Only H2 used a performance-type outcome (WR deep separation), and it found no incremental information from tracked peak speed.
   - No DB coverage outcome exists.
   - DL pressure and OL pressure-allowed outcomes exist but are not part of these registered analyses.
   - No performance claim is made for DB, DL or OL.
4. **Measurement reliability and context.**
   - Game-speed reliability varies by position: DB is lowest (0.65–0.68); DL and OL are highest (0.86–0.94).
   - Demand differs by context.
   - Role (DL EDGE / interior, DB CB / S / slot) and deployment are partly consequences of athleticism.
   - The registered bootstrap is conservative, especially for DB and OL (bootstrap SE 1.9× and 1.7× the Wald SE).

## 6. Limitations

- n = 52–57 players per position. Most secondary contrasts can only be estimated, as registered (§11–§12).
- The H1-DL(b) adjusted model is weakly identified (speed–weight collinearity), and role is a mediator.
- The meta-regression has 11 cells, of which 2 TE cells are noisy (8–9 players per half), so λ is uninformative.
- Everything is associational. REG season only, 2023–2025, players with ≥ 100 primary opportunities.
- **Not run:** TE beyond the registered descriptive estimates; the H2-related negative control (done in H2); any exploratory performance outcome.
