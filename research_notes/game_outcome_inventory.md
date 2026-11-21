# Phase 3, Task 1: Game Outcome Inventory: What Can Actually Be Measured

*Pipeline: `scripts/run_phase3_screening.py` (stage `features`, then `analyse`; run
`experiments/phase3_screening/20261121T010253Z`). Definitions are from the official data dictionary (Kaggle
data page, retrieved 2026-11-21). **No combine × outcome association was computed in this phase**, and
`player_career_successes` was not read.*

## 1. Bottom line
- **The competition scores linkage to regular-season performance only.**
  - The data page says *"regular-season NFL game performance"*.
  - `player_play` also holds PRE (51,759 rows) and POST (13,169) rows; these are excluded from all outcomes.
  - REG rows: 249,269.
- **Usable performance outcomes exist for four of the five positions:**
  - WR/TE: separation at pass forward; targets per route.
  - DL: pressure generated per pass rush; NGS get-off.
  - OL: pressure allowed per pass block; peak pressure probability allowed.
  - DB: only tackles on run plays and speed expression in coverage. **There is no coverage-performance outcome for DBs.**
- **Two requested outcomes cannot be built as specified:**
  - **DB "closing separation"** cannot be built: no ball, no non-cohort players, and no receiver–defender assignment column.
  - **WR "separation creation" over time** is not available as a trajectory. Separation exists only as a single NGS value at the pass-forward moment, and only on thrown passes.
- **Important definitions discovered (not obvious from column names):**
  - Pressure *generated* by a defender has no flag. It is `time_to_pressure IS NOT NULL`: `quick_pressure` is non-null if and only if `time_to_pressure` is non-null (agreement 1.000).
  - `blitzing` is TRUE on most DL rushes (25k of 33k). For DL it behaves like a "rushing" flag, not a blitz.
  - A run play is `pass_result == ""` (empty string, not null).
  - `coverage_assignment == "NO_ASSIGNMENT"` marks rushers. It must be excluded from DB coverage snaps.

## 2. Linking player_play to tracking (REG)
| Position | REG rows | Rows with tracking and a snap event | Pass plays with `pass_forward` frame | Thrown passes (C/I/IN) with `pass_forward` | Median snap→throw (s) |
|---|---|---|---|---|---|
| WR | 35,427 | 99.7% | 87.6% | 99.7% | 2.7 |
| TE | 7,735 | 97.0% | 85.0% | 96.7% | 2.7 |
| OL | 86,582 | 99.6% | 88.2% | 99.5% | 2.6 |
| DL | 52,609 | 99.7% | 88.2% | 99.5% | 2.7 |
| DB | 66,916 | 99.7% | 87.9% | 99.4% | 2.7 |

- Play-level linkage is essentially complete.
- About 12% of pass plays have no pass-forward event. These are sacks and scrambles.
- Tracking exclusions (CLAUDE.md): 7 faulty-game sequences and 3 speed spikes (REG).

**Composition caveats:**
- WR and TE rows are pass plays only: 100% of their rows are dropbacks, and every row has a route.
- OL, DL and DB rows include runs: 40%, 41% and 37% of rows.

## 3. Outcome-by-outcome availability (REG, cohort players, by combine position)
| Desired outcome | Column(s) | Exists? | Where defined (non-null) | Notes |
|---|---|---|---|---|
| WR/TE route separation | `separation_at_pass_forward` | ✅ | **All routes on thrown passes** (C/I/IN = 100%), not sacks or scrambles (0%); 87.6% of routes | Nearest-defender distance at the throw, *not* only for the target. Measured on untargeted routes too, which is the key to opportunity adjustment |
| WR/TE separation *creation* (over time) | — | ❌ | — | No defender trajectories except cohort defenders (§4) |
| WR/TE targets | `target` | ✅ | every route | Targets per route is a standard usage/"getting open" rate |
| WR/TE yards, YAC, xYAC | `rec_yards`, `yards_after_catch`, `expected_yards_after_catch` | ✅ | targets / receptions only (≈12–16%) | Sparse; heavily QB and scheme dependent |
| Pre-snap cushion | `cushion` | ✅ | WR 95%, DB 59% of rows | A *deployment* choice by the defence, not performance |
| TE speed expression | tracking (`s`) | ✅ (derived) | 97% of TE rows | Route max speed before the throw |
| DL burst / get-off | `player_get_off` | ✅ | 82% of DL pass plays, 37% of DL run plays | Snap → crossing the LOS. Validated against our tracking (§5) |
| DL pressure | `time_to_pressure` non-null | ✅ (derived) | per rush snap: 7.8% (DL), 11.7% (DB rushers) | 96 DL pressures with no get-off value (excluded from the rate) |
| DL sacks, QB hurries | `sack`, `time_to_qb_hurry` | ✅ | event-only | Too rare for player-level n ≈ 60 |
| DL/DB tackles | `tackle`, `assist`, `tackle_for_loss` | ✅ | DL 12% / DB 9% of run plays | Role dependent |
| OL pass-protection | `pressure_allowed`, `peak_pressure_probability_allowed`, `sack_allowed` | ✅ | 93% of OL pass plays; ≈ 0.5% of OL run plays | Pressure-allowed rate 8.5%; peak pressure probability is continuous (NGS model) |
| OL time to pressure | `time_to_pressure_allowed` | ✅ | only when pressure allowed | Event-conditional |
| OL lateral / run-block movement | tracking (derived) | ⚠️ | 99.6% | No run-block *outcome* exists: movement only |
| DB coverage performance (separation allowed, targets allowed) | — | ❌ | — | No column links a DB to the receiver covered. `separation_at_pass_forward` is on receiver rows only |
| DB coverage role | `coverage_assignment` | ✅ | 94% of DB pass plays (MAN 10.0k, deep zone 18.1k, underneath zone 10.5k) | Context, not outcome |
| Play value | `expected_points_added` | ✅ | all rows | Team-level outcome. Not attributable to one cohort player |

## 4. Can the missing relationships be reconstructed from tracking?
At the `pass_forward` frame, we paired every tracked cohort receiver with every tracked cohort defender on the opposite side of the same play.

| Check | Result |
|---|---|
| WR/TE route plays (with separation) that have ≥ 1 tracked cohort defender | 27,888 |
| … cohort defender within 3 yd at the throw | 3,133 |
| … cohort defender *is* the NGS nearest defender (\|d − separation\| < 0.25 yd) | 5,224 (4,821 of them DBs); 111 distinct receivers |
| Median \|d − separation\| when it is that defender | ≈ 0 yd (exact match) |
| Share of plays where the nearest cohort defender is no closer than the NGS separation (− 0.25 yd) | 99.8% |

**Two conclusions:**
1. **`separation_at_pass_forward` is reproduced exactly from the same tracking coordinates.** It is a tracking-consistent, validated quantity, not a charting label.
2. **DB coverage outcomes could be built only for the ≈ 4.8k plays where a cohort DB is the nearest defender.**
   - These plays are a selected subset: both players must be rookies or young players in the cohort.
   - Such a DB outcome is **exploratory at best** and is not used as a primary outcome.

## 5. Tracking-derived speed-expression metrics (new, per player-play)
- **Definitions:**
  - Coordinates are normalised so the offence moves toward +x.
  - `vmax_play` / `vmax_prepass`: max `s` after the snap, or between the snap and the throw.
  - `disp_10` / `fwd_10`: displacement, or forward (toward the opponent) displacement, 1.0 s after the snap.
  - `lat_15`: |Δy| at 1.5 s.
  - `t_to_4`: first time `s` ≥ 4 yd/s.
- **Validity against an independent NGS measure (DL rushes):**
  - Play level: get-off vs `fwd_10` ρ = −0.90; vs `disp_10` −0.77; vs `t_to_4` +0.52.
  - Player level: get-off vs `disp_10` ρ = −0.88 (n = 69).
  - So get-off is essentially a speed-expression (burst) measure, not a performance outcome in itself.
- **Separation is context-driven:**
  - Median separation: man coverage 1.55 yd, zone 3.15 yd.
  - Deep routes 2.28 yd, short routes 2.92 yd.
  - It is almost unrelated to time to throw (play-level ρ = −0.06).

## 6. Classification used in the rest of Phase 3
| Layer | Meaning | Examples |
|---|---|---|
| **Capacity** (combine) | What the athlete can do when asked maximally | tracked 40 peak speed (r = 0.987), official 40 / 10-yd split |
| **Speed expression** (game, not performance) | How much of the capacity the game shows | `vmax_prepass`, `vmax_play`, get-off, `disp_10`, `lat_15` |
| **Performance** (game outcome) | A football result an evaluator cares about | separation, targets per route, pressure rate, pressure allowed, tackles |
| **Deployment** (coach/scheme decision) | How the player is used | cushion, coverage role, alignment, route mix |

Phase 2 measures that failed validation (game A0, D99/C99 as capacities, CCMT execution cost) are **not** used as capacities here.
