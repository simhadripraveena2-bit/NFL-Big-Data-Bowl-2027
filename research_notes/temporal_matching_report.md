# Phase 3, Task 2: Temporal Player Matching (Combine → Later NFL Games)

*Run `experiments/phase3_screening/20261121T010253Z` (`temporal_matching.parquet`, `player_season_snaps.parquet`).
Identity is by `nfl_id` (verified in Phase 1). Outcomes are REG only.*

## 1. Rules
- **Ordering:** each combine (Feb–Mar of `draft_year`) precedes every game used. The first eligible season is `draft_year`, starting in September.
- **Leakage check:** rows in `player_play` with season < draft year = **0** (all season types). No pre-combine game data exists.
- **Predictors** are combine-day measures only: official forty and 10-yd split, and the tracked 40 peak speed (best attempt with fit R² > 0.95). Draft position is not a predictor; it is treated as a selection variable.
- **Outcomes** are post-combine REG games. NFL experience (season − draft_year + 1) is a covariate, because the 2023 class is observed in years 1–3 and the 2025 class only in year 1.

## 2. Coverage by draft class and position
| Class | Pos | Post-combine seasons | Combine players | Official 40 | Tracked 40 (and official) | Any REG snap | REG snaps | Players 2023 / 2024 / 2025 |
|---|---|---|---|---|---|---|---|---|
| 2023 | WR | 3 | 39 | 35 | 33 (33) | 32 | 21,036 | 30 / 28 / 24 |
| 2024 | WR | 2 | 31 | 29 | 28 (28) | 28 | 10,164 | – / 27 / 20 |
| 2025 | WR | 1 | 37 | 33 | 33 (33) | 23 | 4,227 | – / – / 23 |
| 2023 | TE | 3 | 12 | 9 | 9 (9) | 10 | 3,273 | 10 / 9 / 10 |
| 2024 | TE | 2 | 13 | 11 | 11 (11) | 12 | 2,642 | – / 12 / 9 |
| 2025 | TE | 1 | 17 | 14 | 14 (14) | 11 | 1,820 | – / – / 11 |
| 2023 | OL | 3 | 37 | 30 | 30 (30) | 28 | 41,437 | 25 / 24 / 24 |
| 2024 | OL | 2 | 46 | 37 | 37 (37) | 34 | 30,032 | – / 30 / 29 |
| 2025 | OL | 1 | 38 | 28 | 28 (28) | 29 | 15,113 | – / – / 29 |
| 2023 | DL | 3 | 37 | 33 | 33 (33) | 32 | 27,307 | 30 / 30 / 27 |
| 2024 | DL | 2 | 37 | 32 | 31 (31) | 29 | 16,255 | – / 27 / 26 |
| 2025 | DL | 1 | 44 | 29 | 29 (29) | 37 | 9,047 | – / – / 37 |
| 2023 | DB | 3 | 35 | 34 | 33 (33) | 30 | 25,863 | 27 / 25 / 21 |
| 2024 | DB | 2 | 50 | 41 | 40 (40) | 41 | 31,426 | – / 35 / 38 |
| 2025 | DB | 1 | 37 | 29 | 29 (29) | 25 | 9,627 | – / – / 25 |

**Totals:**
- 510 combine participants; 424 have an official forty.
- 418 have a tracked 40; every one of these also has an official forty.
- 401 have at least one REG snap.

## 3. Analysis-eligible players
Players with a tracked 40 and ≥ 100 position-relevant REG opportunities (Task 3). These are the `n` values used for power.

| Pos | Opportunity | n (≥ 50) | n (≥ 100) | n (≥ 200) |
|---|---|---|---|---|
| WR | routes | 63 | 57 | 45 |
| TE | routes | 20 | 18 | 11 |
| DL | pass rushes | 65 | 53 | 37 |
| OL | pass blocks | 56 | 53 | 48 |
| DB | coverage snaps (excluding NO_ASSIGNMENT) | 62 | 56 | 50 |

## 4. Threats and how they are handled
| Threat | Consequence | Handling |
|---|---|---|
| **Selection into playing time.** Only players who earn snaps produce outcomes; draft capital and athleticism both drive snaps. | Range restriction / collider bias on the speed–performance slope | Report the eligibility rate by combine-speed tertile. Use a selection-sensitivity analysis: thresholds of 50/100/200, and inverse-probability-of-eligibility weights from pre-combine variables (position, weight, draft class), never from outcomes |
| **Unequal post-combine windows** (1–3 seasons) | Experience is confounded with class | NFL-year fixed effect; season fixed effect; class-specific sensitivity |
| **Changing role over seasons** | Context drift | Context-adjusted play-level models (Task 3) |
| **Same-season information** | None: combine precedes all games | — |
| **Validation leakage** | Splitting by plays leaks player identity | Split by **player**, and **forward in time** (2023–24 → 2025). The 2025 class gives a fully new-player test, but it is small (WR 23, DL 37, DB 25 with any snap) |

## 5. Validation splits available
- **Player-grouped cross-validation:** within position, all seasons, for model comparison.
- **Season-forward:** fit on 2023–24 seasons, evaluate on 2025-season player means. Players with ≥ 100 position-relevant opportunities in the 2025 season (before requiring a tracked 40): WR 47, TE 13, DL 55, OL 56, DB 56.
- **Season-to-season stability** of outcomes uses consecutive-season pairs with ≥ 40 opportunities each: 49–58 pairs per position (TE 19).
