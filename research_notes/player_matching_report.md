# Player Identity Matching Report

*Source: `notebooks/01_dataset_exploration.ipynb`, §4. Every check below was run, not assumed.*

## Summary
- **Combine participants:** 510. All of them have combine tracking and a `combine_results` row.
- **Identifiable NFL players:** 510 in `players.csv`. 497 have at least one tracked NFL play (PRE, REG or POST); 401 have regular-season tracking; 303 have at least 100 tracked regular-season plays.
- **Players appearing in both combine and game data:** 497 of 510 (97.5%).
- **Linking key:** `nfl_id` is shared by all files. It is a curated, competition-provided identifier, so no fuzzy name matching is needed. We verified it with seven independent consistency checks; none failed.
- **Ambiguous matches:** none at the ID level. Two display-name collisions exist. Each pair is clearly two different people (different `nfl_id`, position, draft year or conference), so any name-based join would be wrong.

## Verification checks

| # | Check | Result |
|---|---|---|
| 1 | `nfl_id` sets identical across players / combine_results / combine_tracking / career_successes | ✅ identical (510) |
| 2 | Every game-tracking and `player_play` `nfl_id` exists in `players` | ✅ 0 orphans |
| 3 | `draft_year` agrees: players = combine_results = combine_tracking = year of combine timestamps | ✅ all agree |
| 4 | Skill-drill family matches `combine_position` (WR→WR drills, OL→OL drills, …) | ✅. The 4 players with LB drills are all DL (2023 only); plausible edge rushers working out with LBs |
| 5 | Nobody appears in game tracking before their draft year | ✅ 0 violations |
| 6 | Offensive positions have no defensive snaps and vice versa | ✅ OL/TE/WR 0 defensive snaps; DB 27 and DL 1 offensive snaps (trick plays and goal-line packages are plausible) |
| 7 | `career_games_active` ≥ number of tracked REG games | ✅ never violated. r = 0.884 |

On check 7: `career_games_active` minus tracked REG+POST games has median +3 and range −6 to +47. The positive gap is
consistent with special-teams-only appearances. The small negatives suggest career fields may exclude the postseason
or use a different "active" definition. **Career-field definitions must be confirmed on the Kaggle data page before
they are used as outcomes.**

## Position consistency (`combine_position` → `players.nfl_position`)

| Combine | NFL position(s) |
|---|---|
| WR (107) | WR 106, TE 1 |
| TE (42) | TE 41, FB 1 |
| OL (121) | G 51, T 50, C 20 |
| DL (118) | DT 47, DE 36, **OLB 30**, NT 5 |
| DB (122) | CB 60, SS 28, FS 25, DB 5, ILB 2, MLB 1, RB 1 |

The modal in-game `lined_up_position` (from `player_play`) agrees with these labels, with expected nuances:
DE/OLB → EDGE, DT → INTERIOR_LINE, CB → CB or SLOT_CB, TE → TE or SLOT_WR.
**"DL" mixes interior linemen and edge rushers, and "DB" mixes corners and safeties.** These are heterogeneous groups,
which matters for any within-position analysis.

## Coverage by position

| Position | Combine | Any game tracking | REG tracking | ≥100 REG plays | Career games > 0 |
|---|---:|---:|---:|---:|---:|
| WR | 107 | 106 | 83 | 63 (58.9%) | 86 |
| TE | 42 | 38 | 33 | 21 (50.0%) | 34 |
| OL | 121 | 120 | 91 | 69 (57.0%) | 101 |
| DL | 118 | 115 | 98 | 77 (65.3%) | 100 |
| DB | 122 | 118 | 96 | 73 (59.8%) | 101 |
| **All** | **510** | **497** | **401** | **303 (59.4%)** | **422** |

### By draft class

| Draft class | Players | Any game tracking | ≥100 REG plays | Seasons observable | Median career starts |
|---|---:|---:|---:|---|---:|
| 2023 | 160 | 158 | 112 | 2023–25 (3) | 5 |
| 2024 | 177 | 175 | 105 | 2024–25 (2) | 2 |
| 2025 | 173 | 164 | 86 | 2025 (1) | 0 |

## Missing matches: the 13 players with no game tracking
All 13 have `career_games_active = 0` and zero snaps of any kind, so their absence is consistent, not a linkage
failure. By position: TE 4, DB 4, DL 3, WR 1, OL 1. By class: 2023 2, 2024 2, 2025 9. Seven were undrafted.

These are genuine "did not play" outcomes. They should be kept (not dropped) in any success analysis, or survivorship
bias follows.

## Selection and comparability caveats
1. **Cohort only.** The data contains just these 510 players. Opponents and teammates outside the cohort are invisible in tracking.
2. **Exposure is endogenous.** Who gets snaps depends on draft capital, which depends on combine performance. Selection into the outcome sample is therefore not random.
3. **Right-censoring.** The 2025 class has at most one season; career totals are not comparable across classes without exposure adjustment.
4. **Drill self-selection.** Official `three_cone` / `short_shuttle` are missing for about 60% of players. Tracking for those drills exists only for 160–170 players, and participation may correlate with athletic confidence.
5. **Position-dependent play sampling.** WR/TE tracked plays are route-running dropbacks only; OL/DL/DB include run plays. "≥100 REG plays" therefore means ≥100 routes for WR/TE but ≥100 snaps of any type for the others.
6. **No QB, RB or off-ball LB in the combine positions.** Conclusions cannot be generalised to those positions.
