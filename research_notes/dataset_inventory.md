# Dataset Inventory — NFL Big Data Bowl 2027

*Phase 1 (exploration). All figures were computed in `notebooks/01_dataset_exploration.ipynb` from
`data/interim/*.parquet`, a lossless, typed Parquet cache of the raw CSVs. Row counts were checked
against the CSVs and match exactly. Raw files are untouched. Missing values are encoded as the literal `NA`.*

## 1. File overview

| File | Rows | Cols | Unique `nfl_id` | Games | Seasons / draft years | Full-row dups | Candidate PK (verified unique) |
|---|---:|---:|---:|---:|---|---:|---|
| `players.csv` | 510 | 10 | 510 | – | draft 2023–25 | 0 | `nfl_id` |
| `combine_results.csv` | 510 | 18 | 510 | – | draft 2023–25 | 0 | `nfl_id` |
| `player_career_successes.csv` | 510 | 9 | 510 | – | – | 0 | `nfl_id` |
| `combine_tracking.csv` | 463,189 | 14 | 510 | – | draft 2023–25 | 0 | `(nfl_id, time, entity_type)` or `(event_id, time, entity_type)` |
| `games.csv` | 1,002 | 7 | – | 1,002 | 2023–25 | 0 | `game_id` (also `game_key`) |
| `player_play.csv` | 314,197 | 64 | 497 | 1,001 | 2023–25 | 0 | `(game_id, play_id, nfl_id)` |
| `game_tracking_2023.csv` | 3,665,443 | 12 | 156 | 333 | 2023 | 0 | `(game_id, play_id, nfl_id, time)` |
| `game_tracking_2024.csv` | 7,827,944 | 12 | 318 | 334 | 2024 | 0 | `(game_id, play_id, nfl_id, time)` |
| `game_tracking_2025.csv` | 11,160,903 | 12 | 448 | 334 | 2025 | 0 | `(game_id, play_id, nfl_id, time)` |

`(nfl_id, time)` alone is **not** unique in `combine_tracking`. Its 32,095 duplicate tuples are exactly the
`BALL` rows, which carry the receiver's `nfl_id`.

## 2. Relationships

```
players (510) ─1:1─ combine_results ─1:1─ player_career_successes        (identical nfl_id sets)
   ├─1:N─ combine_tracking   (event_id = one player's single drill attempt)
   ├─1:N─ player_play        (game_id, play_id, nfl_id) ─N:1─ games
   └─1:N─ game_tracking_YYYY (game_id, play_id, nfl_id, time)  ≈1:1 per player-play with player_play
```

- All `nfl_id`s in every file exist in `players.csv` (0 orphans). All tracking `game_id`s exist in `games.csv`.
- **The game data covers only the 510-player cohort** (WR/TE/OL/DL/DB drafted or signed in 2023–25). It does not cover all 22 players on the field, and it has no ball. A tracked play holds 1–11 cohort players (2025 mode: 3).
- `games.csv`: each season has 49 PRE (weeks 0–3), 272 REG (weeks 1–18) and 13 POST (weeks 19–23) games. Game `2023100108` (PHI–WAS, REG week 4) has no tracking or `player_play` rows.
- **Play-type selection differs by position.** WR/TE rows, in both `player_play` and tracking, contain *only dropback plays on which the player ran a route*: 0% non-pass plays, so no run plays or blocking snaps. OL/DL/DB rows include run plays (37–41% non-pass). WR/TE exposure counts are therefore route counts, not snap counts.
- Tracking and `player_play` agree at the (game, play, player) level to within about 1%. Per season, tracked player-plays missing from `player_play` were 449 / 857 / 1,191, and `player_play` rows without tracking were 293 / 661 / 796 (2023 / 24 / 25). Unresolved; to investigate in Phase 2.

## 3. Column dictionaries and missingness

### players.csv
`nfl_id` Int64 · `display_name` Str (508 unique: 2 name collisions, which are different people) · `draft_year` Int64 ·
`nfl_position` Str (17 values) · `birth_date` Str (ISO, all parseable; age at combine 20.5–26.2, median 22.9) ·
`college_name` Str (112) · `college_conference` Str (21) · `draft_round`, `draft_pick_within_round`,
`draft_overall_pick` Int64 — **127 nulls (24.9%) = undrafted players** (44 / 36 / 47 per class).

### combine_results.csv
`draft_year`, `nfl_id`, `combine_position` (**only 5 values: WR 107, TE 42, OL 121, DL 118, DB 122**),
anthropometrics with no nulls (`combine_height` in, `combine_weight` lb, `hand_size`, `arm_length`, `wing_span`),
and official drill results with substantial missingness (players skip drills):

| Column | Null % | Column | Null % |
|---|---:|---|---:|
| `ten_yd_split` | 16.7 | `three_cone` | 64.7 |
| `forty` | 16.9 | `short_shuttle` | 60.6 |
| `vertical` | 14.1 | `bench_reps` | 62.4 |
| `broad_jump` | 17.1 | `ngs_college_production_score`, `ngs_final_score` | 0.2 |
| `ngs_athleticism_score` | 0.0 | | |

The `ngs_*` scores are pre-computed NFL Next Gen Stats composites.

### player_career_successes.csv (no nulls)
`career_offensive_snaps`, `career_defensive_snaps`, `career_special_teams_snaps`, `career_games_active`,
`career_games_started`, `ap_all_pro_1st_team` (0/1), `ap_all_pro_2nd_team` (0/1), `pro_bowl_original_ballot` (0/1/2).
Elite outcomes are rare: 11 players have any Pro Bowl selection and 7 have any All-Pro selection.

### combine_tracking.csv (no nulls)
| Column | Meaning (verified empirically, §4) |
|---|---|
| `draft_year` | combine year (matches the timestamp year) |
| `event_id` | one attempt by one player (6,310 events; format differs in 2023 vs 2024–25) |
| `nfl_id` | athlete (for BALL rows: the receiver) |
| `entity_type` | `PLAYER` (431,094) / `BALL` (32,095; WR and TE catching drills only) |
| `time` | wall-clock timestamp, 100 ms grid |
| `drill_type` | 9 families: `FORTY_YARD_DASH`, `THREE_CONE_DRILL`, `SHORT_SHUTTLE`, `SKILL_DRILLS_{WR,TE,OL,DL,DB,LB}` |
| `drill_name` | 56 names (several are synonyms split by year; see §5) |
| `attempt` | attempt index within the drill (max 17) |
| `x, y` | position (yd) |
| `s` | speed (yd/s) |
| `a` | **unsigned** acceleration magnitude (yd/s²) |
| `dis` | **not** per-frame displacement (≈0.46× of it); do not use |
| `dir` | motion direction (deg; 0 = +y, clockwise) |

There is no orientation (`o`) and no event markers.

### game_tracking_YYYY.csv
`game_id, play_id, nfl_id, time, x, y, s, a, dis, o, dir, event`. Nulls appear only in `event` (≈93.4%,
because events are sparse frame annotations). The `event` vocabulary has 43–47 values (ball_snap, pass_forward,
handoff, first_contact, tackle, …). There are vocabulary drifts across seasons: `autoevent_playaction` has
0 rows in 2025, and `shift` has 0 rows in 2024.

### player_play.csv (64 columns)
- **Play context:** quarter, down, distance, field position, clock, score, win probability / EPA, formation, receiver alignment, coverage type, `play_direction`, penalties.
- **Player-level outcomes and NGS-derived metrics:** `route_ran`, `separation_at_pass_forward`, `cushion`, `expected_yards_after_catch`, pass-blocking metrics (`pressure_allowed`, `time_to_pressure_allowed`, `peak_pressure_probability_allowed`, …), pass-rush metrics (`player_get_off`, `time_to_pressure`, `sack`, …), tackling, and coverage assignment.
- Missingness is structural: a column is filled only when it applies to the player's role. For example, `route_ran` is filled for 100% of WR/TE rows and ~0% of others. `pass_result` uses the empty string (not null) for non-pass plays (103,636 rows).
- Known quirk: the column name `visitor_team_win_probility_added` is misspelled in the source.

### games.csv
`game_id, game_key, season, season_type (PRE/REG/POST), week, home_team_abbr, visitor_team_abbr` — no nulls.

## 4. Variable semantics (empirical verification)
Provided channels were tested against quantities derived from `x, y` (notebook §2.1).

| Check | Combine | Game (2025, 2M-row sample) |
|---|---|---|
| `s` vs 10 × frame step, r / median ratio | 0.998 / 1.004 | 0.996 / 0.984 |
| `dis` vs frame step, r / median ratio | 0.952 / **0.462** | 0.9996 / 0.999 |
| `a` vs ‖dv/dt‖, r / median ratio | 0.993 / 0.964 | 0.879 / 0.776 |
| `a` vs \|ds/dt\| (tangential), r | 0.625 | 0.616 |
| `dir` vs NGS bearing atan2(dx, dy), median \|error\| | 1.2° | 1.1° |

**What this means:**
- Coordinates are in yards and speed is in yd/s.
- `dir` uses the NGS convention in both sources.
- `a` is an unsigned magnitude that mixes speeding up, braking and turning. **Deceleration and signed acceleration must be derived.**
- Combine `dis` uses a different, undocumented basis. **Derive distance from `x, y`.**

A naive tracking-derived 40-yard time correlates r = 0.906 with the official `forty` (n = 381). It has a +0.35 s
offset from the crude onset rule. This confirms the tracking faithfully captures the sprint.

## 5. Data-quality issues

| Issue | Extent | Handling suggestion |
|---|---|---|
| Faulty tracking (negative `a`, `s` up to 16.9 yd/s) | game 2025101205 plays 1289 and 1314 (161 frames, 4 players), plus 1 frame in 2025113003 | exclude or repair |
| Speeds > 12.5 yd/s in 2023 / 2024 | 4 / 3 frames | flag as spikes |
| Frame gaps (Δt ≠ 100 ms) in game tracking | 8 player-plays in total, out of 314,944 | negligible |
| Combine frame gaps | 0 of 6,310 attempts | none |
| Drill synonyms split by year | `LINE`/`LINE_DRILL`, `PASS_PRO_MIRROR_DRILL`/`PASS_PRO-MIRROR_DRILL`, `OVER_THE_SHOULDER_ADJUST`/`OVER_SHOULDER_ADJUST` (TE), `SPEED_OUT_LEFT`/`SPEED_OUT_ROUTE_LEFT` | harmonise |
| Same (player, drill, attempt) recorded as 2 events | 9 cases, all 2023 | inspect or merge |
| Very short agility recordings | 5 shuttle attempts < 30 frames; 2 three-cone attempts < 40 frames | likely truncated or aborted reps |
| Combine `dis` definition | all rows | do not use |
| Tracking ↔ `player_play` mismatch | ≈1% of player-plays | investigate |

## 6. Temporal structure
- **Combine:** 10 Hz, every timestamp on the 100 ms grid, and every attempt contiguous. Four combine days per year (2023-03-02…05, 2024-02-29…03-03, 2025-02-27…03-02). Median attempt length is 5–9 s depending on the drill (range 1–21 s).
- **Game:** 10 Hz, PRE + REG + POST. Sequences start about 1.0 s before the snap (median 10 pre-snap frames, for 99.97% of 2025 player-plays) and end at the play outcome (tackle, incomplete pass, out of bounds, …). Median sequence length is 69 frames (6.9 s).

| Season | Plays | Player-plays | Players | REG / PRE / POST player-plays |
|---|---:|---:|---:|---|
| 2023 | 31,690 | 50,911 | 156 | 39,146 / 10,207 / 1,558 |
| 2024 | 40,331 | 108,720 | 318 | 86,219 / 18,210 / 4,291 |
| 2025 | 42,544 | 155,313 | 448 | 125,742 / 22,375 / 7,196 |

## 7. Storage
- Raw data: 2.31 GB of CSV plus a 0.51 GB zip.
- Parquet cache: 0.46 GB (zstd).
- Peak notebook memory: well under the 15 GB available.
- Everything under `data/` is git-ignored.
