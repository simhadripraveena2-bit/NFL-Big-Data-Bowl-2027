# Join-validation report: the single Combine-to-game-outcome join

**Status:**
- The join was performed once, as approved, on 2026-11-21 (run `20261121T135032Z`).
- **No confirmatory model has been fitted.**
- **No statistic relating any combine predictor to any game outcome has been computed or looked at.** This report contains counts, coverage, missingness and duplication checks only.

**Reproduce:**
- Command: `python scripts/run_confirmatory_join.py`. It refuses to run with uncommitted code in `src/`, `scripts/` or `tests/`.
- Machine-readable output: `experiments/confirmatory_join/20261121T135032Z/join_validation.json`.
- Joined frames (git-ignored, write-once): `data/interim/confirmatory_join/20261121T135032Z/`, containing `h1_{WR,TE,DB,DL,OL}.parquet`, `h2_WR.parquet`, `predictors.parquet` and the eligibility tables. Their sha256 hashes are in the JSON.

## 0. Pre-join checklist (requested items 1–8)

| # | Item | Status |
|---|---|---|
| 1 | D1, D2, D3 recorded in the deviations log (`preregistration.md` §15), with reasons and consequences | ✅ done. An implementation note was also added (the full valid-attempt rule; no player affected). |
| 2 | Validated code frozen; exact commit recorded | ✅ Phase 4 validated code: `a690b9a`. **Pre-join freeze, which is also the commit that ran the join: `955d94d4486175223d045af6a883e09ac519432d`.** `research_notes/code_freeze.json` holds sha256 hashes of 12 pipeline files, and `tests/test_code_freeze.py` fails if any changes. |
| 3 | Combine-only 40 test–retest (D3) | ✅ `forty_test_retest.md`. No game table read. Results logged under D3 (within-position R_x: WR 0.94 best-of-2; R_F not identifiable, WR R_F ≥ 0.70). |
| 4 | H1-WR primary test = full REML bootstrap, B = 2,000 | ✅ `confirmatory.h1_registered_test`: REML refit in every resample, shared team-season columns (D2 rejected), and it raises an error if B < 2,000. A smoke test at B = 2,000 on synthetic data completed (2,000/2,000 refits converged, 268 s). The fallback `h1_procedure` remains only for reproducing Phase 4. |
| 5 | H2 secondary and estimation-focused | ⚠️ **Discrepancy: decision needed (proposed D4, below).** The frozen protocol registers H2 as **primary confirmatory, test 2 of the fixed sequence** (§2, §9), not secondary. Phase 4 showed its interpretation can only be estimation-focused (full support ≤ 0.035). I have **not** changed its status. |
| 6 | DB secondary, TE descriptive | ✅ As registered: H1-DB is in the secondary Holm family (§9), and H1-TE is "descriptive only" (§2). |
| 7 | Registered matching rules, seasons, eligibility, missing-data rules | ✅ Implemented in `src/nfl_bdb/data/confirmatory_data.py`. **All registered sample sizes are reproduced exactly** (§5 below). |
| 8 | Raw data not modified or overwritten | ✅ sha256 of every file under `data/raw/` (10 files, 2.7 GB) is identical before and after. The interim inputs are also unchanged. Outputs went only to new directories. |

### Proposed D4 (needs your decision before any model is fitted)

**Option A: demote H2 to secondary/estimation.**
- The primary family becomes {H1-WR} alone, at α = 0.05.
- H2 is reported as estimation: β_P, the true-scale partial correlation and ΔR²_CV with CIs, plus the EIV grid.
- Its registered "supported" criteria are still evaluated and reported, as descriptive.
- This matches your instruction and the Phase 4 conclusion.
- It is still "before seeing outcome associations", because no model or association has been computed.

**Option B: keep the registration.**
- H2 stays test 2 of the fixed sequence.
- It would simply be interpreted as estimation-focused in the write-up.
- FWER control is identical under A and B, because H2 is reached only after H1-WR.

## 1. Matching (nfl_id exact key; no name matching)

| check | result |
|---|---|
| combine_results rows / unique nfl_id | 510 / 510 |
| players rows / unique nfl_id | 510 / 510 |
| predictor table rows / unique nfl_id | 510 / 510 |
| nfl_id with more than one combine position or draft year | 0 / 0 |
| combine nfl_id missing from `players` | 0 |
| **unmatched game players** (game nfl_id with no combine row; any season type / REG) | **0 / 0** |
| duplicate (game, play, nfl_id) keys in `player_play` / in the REG analysis table | 0 / 0 |
| plays before the player's draft season | 0 |
| non-REG rows in the analysis table | 0 |
| players appearing in more than one position frame | 0 |
| ambiguous matches | **none**. The two display-name collisions from Phase 1 are irrelevant: names are never used. |

**Matched players by position** (combine participants → valid tracked 40 → REG game rows):

| pos | combine participants | valid tracked 40 | official 40 | any game rows | REG game rows | **matched (REG rows + valid 40)** | **unmatched: no REG rows** | REG rows but no valid 40 |
|---|---|---|---|---|---|---|---|---|
| WR | 107 | 94 | 97 | 106 | 83 | **73** | 24 | 10 |
| TE | 42 | 34 | 34 | 38 | 33 | **28** | 9 | 5 |
| DB | 122 | 102 | 104 | 118 | 96 | **81** | 26 | 15 |
| DL | 118 | 93 | 94 | 115 | 98 | **77** | 20 | 21 |
| OL | 121 | 95 | 95 | 120 | 91 | **73** | 30 | 18 |
| **all** | **510** | **418** | 424 | 497 | 401 | **332** | **109** | 69 |

**Unmatched combine players:**
- **109** combine participants have no REG game rows. Of these, 13 have no game rows of any kind (Phase 1: zero snaps, consistent).
- A further 69 have REG rows but no valid tracked 40, so they are excluded by §5 (the predictor is the object of study).
- 510 − 418 = **92 players without a valid tracked 40**, exactly as registered in §5.

**Official 40 vs tracked 40:**
- Every player with a valid tracked 40 has an official 40 (0 exceptions), as §5 states.
- 6 players have an official 40 but no valid tracked 40 (WR 3, DB 2, DL 1). They are excluded by the tracked-40 rule.

**Predictor standardisation:** within position over all participants with a value (n_x = WR 94, TE 34, DB 102, DL 93, OL 95). The z-scores have mean 0 and SD 1 in every position. Eligible players are a subset, so their z-scores need not be centred.

## 2. Play exclusions (outcome side, applied before eligibility)

| step | player-play rows |
|---|---|
| REG player-plays of combine cohort | 249,269 |
| after removing plays nullified by penalty | 240,412 (−8,857) |
| after removing faulty game 2025101205 plays 1289/1314 | 240,405 (−7) |
| additional rows removed for s > 12.5 yd/s | 0. Spike sequences have no tracking feature, from the Phase 3 loader. |
| rows without a tracking feature (no ball_snap frame, faulty or spike sequence, untracked) | 910 (0.4 %). Never imputed. |

## 3. Final eligible sample sizes vs the registration (§4)

| frame | eligible (≥ 100 opp. + valid 40) | registered | eligible for the test | registered | 50 / 200 sensitivity | registered 50 / 200 | match |
|---|---|---|---|---|---|---|---|
| H1-WR | 57 | 57 | 57 | 57 | 63 / 45 | 63 / 45 | ✅ |
| H1-TE | 18 | 18 | 17 | 17 | 20 / 11 | — | ✅ |
| H1-DB | 56 | 56 | 52 | 52 | 62 / 50 | 62 / 50 | ✅ |
| H1-DL | 53 | 53 | 53 | 53 | 65 / 37 | 65 / 37 | ✅ |
| H1-OL (H5) | 53 | 53 | 53 | 53 | 56 / 48 | 56 / 48 | ✅ |
| H2-WR | — | — | 57 | 57 | — | — | ✅ |

**No discrepancy with the preregistered sample sizes or matching rules.**

**Why players were ineligible** (counts within position):

| | < 100 opportunities | no valid 40 | < 20 plays in a contrast context | other |
|---|---|---|---|---|
| WR (H1) | 20 | 10 | 0 | — |
| TE (H1) | 12 | 5 | 1 | — |
| DB (H1) | 29 | 15 | 4 | — |
| DL (H1) | 29 | 21 | 0 | — |
| OL (H1) | 25 | 18 | 0 | — |
| WR (H2) | 20 | 10 | — | < 30 deep: 17; < 20 short: 15 |

The categories overlap.

## 4. Rows, contexts, team-seasons and duplication

| frame | rows before join | rows after join | duplicate play keys | players | team-seasons | plays per context |
|---|---|---|---|---|---|---|
| H1-WR | 19,960 | 19,960 | 0 | 57 | 71 | deep 9,961 / short 9,999 |
| H1-TE | 4,170 | 4,170 | 0 | 17 | 36 | deep 1,311 / short 2,859 |
| H1-DB | 16,643 | 16,643 | 0 | 52 | 69 | man 8,218 / under-zone 8,425 |
| H1-DL | 34,154 | 34,154 | 0 | 53 | 69 | pass rush 18,882 / run 15,272 |
| H1-OL | 64,285 | 64,285 | 0 | 53 | 65 | pass block 38,266 / run 26,019 |
| H2-WR | 19,967 | 19,967 | 0 | 57 | 71 | deep 9,935 / short 10,032 |

**No player or outcome is duplicated.**
- The join is many-to-one on nfl_id, enforced by polars `validate="m:1"`.
- The script aborts if any row count changes.
- Every frame has unique (game, play, nfl_id) keys.

**The frames are identical in size to the outcome-only Phase 4 skeletons:**
- WR 19,960 plays, 57 players;
- DB 16,643 plays, 52 players;
- H2 deep 9,935 plays;
- 71 WR team-seasons (as in protocol §7).

## 5. Season coverage (REG only; plays / players)

| frame | 2023 | 2024 | 2025 | draft classes 2023 / 2024 / 2025 |
|---|---|---|---|---|
| H1-WR | 3,851 / 24 | 7,245 / 39 | 8,864 / 51 | 24 / 19 / 14 |
| H1-TE | 647 / 8 | 1,641 / 14 | 1,882 / 17 | 8 / 6 / 3 |
| H1-DB | 2,213 / 20 | 6,284 / 39 | 8,146 / 50 | 20 / 21 / 11 |
| H1-DL | 4,676 / 20 | 12,295 / 41 | 17,183 / 51 | 21 / 21 / 11 |
| H1-OL | 11,662 / 18 | 20,463 / 34 | 32,160 / 51 | 19 / 18 / 16 |
| H2-WR | 3,843 / 24 | 7,241 / 39 | 8,883 / 51 | as H1-WR |

**Season-forward split (§13):** the 2023 and 2024 training seasons contain 24 and 39 WRs; the 2025 hold-out contains 51. 2025 is the largest season, because all three draft classes are active.

## 6. Missingness in every primary analysis variable (joined frames)

| frame | variable | missing | handling (registered) |
|---|---|---|---|
| all H1 / H2 | x_peak, x_peak_mean, official 40, y (play max speed), ctx, season, nfl_year, team, down, distance bin, route, time-to-throw bin, lined-up position | **0** | — |
| H1-WR | team_coverage_type | 8 (0.04 %) | "NA" level |
| H1-TE | team_coverage_type | 2 (0.05 %) | "NA" level |
| H1-DL | offense_formation | 543 (1.6 %) | "NA" level |
| H1-OL | offense_formation | 798 (1.2 %) | "NA" level |
| H2-WR | team_coverage_type / in_motion_at_ball_snap | 9 / 7 (0.05 %) | "NA" level |
| H2-WR | separation_at_pass_forward | 0 (frame defined on non-missing separation) | — |

**Outcome missingness before the frame is formed** (eligible players' contrast-context plays without a defined y; never imputed, §5):
- **WR 2,678 / 22,638 (11.8 %), TE 672 / 4,842 (13.9 %).**
  - Almost entirely sacks (WR 1,430) and scrambles (WR 1,177). These have no pass-forward frame, so the registered pre-pass outcome is undefined, and the play is "not an opportunity" (§5).
  - The rest are 71 untracked WR plays.
  - The share is similar on deep (12.5 %) and short (11.1 %) WR routes.
- DB 8, DL 102, OL 222 plays: untracked only.

## 7. Discrepancies and open items

1. **Sample sizes and matching: none.** All registered counts are reproduced exactly.
2. **H2 status (item 5):** registered as primary. Proposed D4 needs your decision (§0).
3. **D3 finding (already logged):** the registered R_x = 0.987 is a pooled value; within WR it is 0.94. This affects only the reported disattenuated ρ and the H2 EIV sensitivity, not any decision rule.
4. **Sack/scramble exclusion from the WR/TE outcome** (≈ 12 %) follows §3.2/§5. It is listed because it is the largest single exclusion.

**Next step, only after your review:** fit the confirmatory models, in the order of protocol §14:
1. H1-WR with `h1_registered_test` (B = 2,000);
2. then H2 according to your D4 decision;
3. then the secondary analyses;
4. then the exploratory analyses.
