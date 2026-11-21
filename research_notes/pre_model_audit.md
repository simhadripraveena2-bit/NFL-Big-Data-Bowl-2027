# Pre-model audit (final check before any confirmatory model)

**Date:** 2026-11-21.
**Audit run:** `experiments/pre_model_audit/20261121T154237Z/audit.json`, produced by `python scripts/run_pre_model_audit.py`.
**Result: all checks passed.** No confirmatory or exploratory Combine-to-outcome model has been fitted.

## 1. Final analysis hierarchy (after D1–D4, `preregistration.md` §15)

| tier | analysis | inference |
|---|---|---|
| **Primary (sole confirmatory)** | **H1-WR:** Δ = ρ_deep − ρ_short > 0 | FWER α = 0.05. `confirmatory.h1_registered_test`: REML + full REML player-cluster bootstrap, B = 2,000 (D1; D2 rejected). Supported iff Δ̂ > 0, the 95 % CI excludes 0, and the 2025 season-forward sign agrees (§12). |
| Secondary, estimation-focused | **H2:** WR deep-route separation, peak speed given the official 40 (D4) | Estimates and CIs: β_P, true-scale partial correlation, ΔR²_CV, ΔRMSE; EIV grid R_F {0.85, 0.90, 0.95, 0.99} × R_x {0.94, 0.987}. The §12 criteria are reported descriptively. Never a confirmatory claim. |
| Secondary, Holm family (unchanged, §9) | H1-DB, H1-DL(a), H1-DL(b), H5(b) | Holm at α = 0.05. H1-DB is expected to be inconclusive (Phase 4 power ≈ 0.03). |
| Secondary estimates with uncertainty | H5(a), H5(c), H1-global (demand meta-regression) | Estimation only. |
| Descriptive | H1-TE (n = 17) | Descriptive only. |
| Sensitivity | Holm over {H1-WR, H1-DB, H2}; robustness grid (§13) | Reported alongside; never decisive. |
| Exploratory | as registered (§2) | Unadjusted and labelled. |

**Note on H5.** Your hierarchy lists "H5: secondary estimates and uncertainty". The registration puts **H5(b)** (Δ_WR − Δ_OL > 0) in the secondary Holm family, and H5(a)/(c) as estimation. I have kept that unchanged, because no deviation was approved for H5. In practice H5(b) is expected to be inconclusive (MDE ≈ 0.53). If you want H5(b) removed from the Holm family as well, that would be a further logged deviation (D5).

## 2. Frozen code

| check | result |
|---|---|
| freeze commit | `955d94d4486175223d045af6a883e09ac519432d` (Phase 4 validated code: `a690b9a`) |
| sha256 of the 12 frozen pipeline files vs `research_notes/code_freeze.json` | **0 mismatches** |
| `git diff 955d94d HEAD` on the frozen files | **empty** |
| uncommitted changes to the frozen files | none |
| `tests/` (29 tests, including `test_code_freeze.py`) | all pass |

The commits after the freeze changed only documentation (`preregistration.md` §15, research notes, `CLAUDE.md`) and added this audit script. None of these is a pipeline file.

## 3. The join is unchanged

| check | result |
|---|---|
| join run / code commit | `20261121T135032Z` / `955d94d` (the freeze commit) |
| sha256 of the 13 join outputs vs the manifest written at join time | 0 mismatched, 0 extra, 0 missing |
| other join runs in `data/interim/confirmatory_join/` | none: **a single join exists** |
| raw data (`data/raw/`, 11 files) vs sha256 recorded at join time | identical |
| files created anywhere in `experiments/`, `data/interim/`, `reports/` after the join | only the 13 join outputs, `join_validation.json`, `LATEST`, and this audit's own `audit.json`. **No model output exists.** |

## 4. Registered matching and exclusion rules: verified independently, without re-joining

Each item is recomputed from the source tables with the frozen code and compared with the stored outputs. The join itself was **not** repeated: the predictor side and the outcome side are rebuilt separately.

| rule (protocol section) | verification | result |
|---|---|---|
| Predictors: valid attempt = R² > 0.95 and peak ≤ 12.5 yd/s; x = max over valid attempts; within-position standardisation over all participants (§3.1) | `predictors.parquet` equals the table recomputed from combine data alone. No selected peak exceeds 12.5 yd/s. | ✅ |
| nfl_id exact-key matching; one row per player (player_matching_report) | combine 510 = predictors 510 = unique nfl_id. Each frame's predictor columns equal that player's row in `predictors.parquet`. | ✅ |
| REG only; from the draft season onward (§4) | 0 non-REG rows; 0 plays before the draft season | ✅ |
| Nullified plays, faulty game 2025101205 (1289/1314), speed spikes > 12.5 yd/s, plays without tracking (§4) | 0 / 0 / 0 remaining. The play-exclusion log equals the one at join time (249,269 → 240,412 → 240,405; 910 untracked rows not imputed). | ✅ |
| Contexts and route depth (§3.3; IN/CROSS excluded) | The outcome part of every stored frame (keys, ctx, y, covariates) equals the outcome frame recomputed without predictors. | ✅ |
| Eligibility: ≥ 100 primary opportunities + valid 40; ≥ 20 plays per contrast context; H2 rules (§4) | The stored eligibility tables equal the recomputed ones, for all five positions and H2 | ✅ |
| No duplicated player or outcome | 0 duplicate (game, play, nfl_id) keys in every frame. Every frame contains one position, and no player appears in two position frames. | ✅ |

## 5. Final sample sizes (all equal to the registration)

| analysis | tier | players (registered) | plays |
|---|---|---|---|
| **H1-WR** | primary | **57 (57)** | 19,960 (deep 9,961 / short 9,999) |
| H2-WR | secondary, estimation | 57 (57) | 19,967 (deep 9,935 / short 10,032) |
| H1-DB | secondary (Holm) | 52 (52); 56 (56) at ≥ 100 | 16,643 |
| H1-DL | secondary (Holm) | 53 (53) | 34,154 |
| H5 / H1-OL | secondary | 53 (53) | 64,285 |
| H1-TE | descriptive | 17 (17); 18 (18) at ≥ 100 | 4,170 |

**Threshold sensitivity, eligible at ≥ 50 / ≥ 200** (identical to §4): WR 63/45, DB 62/50, DL 65/37, OL 56/48, TE 20/11.

**Player-count reconciliation:** 510 combine participants fall into 6 mutually exclusive categories (`join_validation_report.md` §1):
- 332 matched;
- 69 with REG rows but no valid 40;
- 75 with PRE/POST rows only and a valid 40;
- 11 with no game rows and a valid 40;
- 21 with PRE/POST rows only and no valid 40;
- 2 with no game rows and no valid 40.

That gives 109 without REG rows, 92 without a valid 40 (overlap 23), and 13 with no game rows at all.

## 6. No association results have been inspected

**What has been done with joined data since the join:**
1. The join script computed counts, coverage, missingness and duplicate checks.
2. Official-40 availability was cross-tabulated against tracked-40 validity. This uses combine data only.
3. Outcome-side missingness (sacks and scrambles) was counted from the outcome table, restricted to the eligible IDs.
4. The player-count reconciliation used the validity flags and game-row presence.
5. This audit ran frame-equality and lookup-consistency checks.

**What has not been done:**
- None of these steps computed any statistic that uses a combine predictor value together with a game outcome value: no correlation, regression, mixed model, plot or summary of outcomes by predictor.
- `h1_registered_test` and the H2 functions have been run **only on synthetic data**.
- No model, figure or table derived from the joined frames exists in `experiments/` or `reports/` (§3).

**Protocol status:** the deviations log (§15) holds D1 (approved), D2 (rejected), D3 (approved, done), the implementation note, and D4 (approved, Option A). Each is marked "before seeing outcome associations".

**Stopping here.** The next step, only on your approval, is the confirmatory H1-WR fit with `h1_registered_test` (B = 2,000; about 13 min). The secondary and estimation analyses follow in the protocol §14 order.
