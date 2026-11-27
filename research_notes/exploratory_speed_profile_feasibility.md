# Exploratory feasibility audit: "Combine-to-Game Speed Profile"

**Status: EXPLORATORY, not registered, not part of the submission.**
- Descriptive analyses only. No predictive model was fitted.
- No association between Combine speed and any game outcome is estimated or reported. Combine peak speed enters only as the denominator of the candidate ratio.
- Unchanged: the pre-registration, registered results, frozen files, final writeup, public notebook and Kaggle dataset.
- Code: `scripts/explore_speed_profile_feasibility.py`. Run `experiments/speed_profile_feasibility/20261127T224250Z/summary.json` (git-ignored; aggregates only). Seed 2027.

**Recommendation: NO-GO** for a ratio-based "percentage of Combine speed" tool. A narrower, game-only descriptive alternative is outlined in §8; it is **not** implemented.

## 1. Available data fields and definitions

| quantity | source and calculation | notes |
|---|---|---|
| **Combine peak speed** `x_peak` (yd/s) | `combine_tracking`, `FORTY_YARD_DASH`, provider speed channel `s`, 10 Hz. Per attempt: `vpeak = max(s)`. An attempt is valid if a mono-exponential sprint fit up to the peak has R² > 0.95 and the peak is ≤ 12.5 yd/s. `x_peak` = max over valid attempts (best of up to 2) | frozen (`run_real_capacity.forty_fits`, `confirmatory_data.predictor_table`). Straight line, maximal effort, from a stance, 40 yd |
| **Game speed per route** `v_ij` (yd/s) | `game_tracking_<season>`, provider `s`, 10 Hz. `vmax_prepass` = max(`s`) from the `ball_snap` frame to the `pass_forward` / `pass_shovel` frame (frozen Phase 3 feature). Frames with `s` > 12.5 and the faulty game are excluded | **undefined when there is no pass-forward event**: 97–99% of sacks and scrambles. Alternative `vmax_play` = max to the end of the tracked play (includes post-throw running) |
| route label | `player_play.route_ran` (12 values) | charted route; available for every WR route. Frozen groups: deep = GO/POST/CORNER/WHEEL; short = HITCH/SLANT/OUT/FLAT/SCREEN/ANGLE; IN/CROSS separate |
| other pre-outcome context | `receiver_alignment` (2x2, 3x1, …), `offense_formation`, `in_motion_at_ball_snap` (bool), `season`, `week` | describe the call and alignment, not the player's physical demand |
| time to throw | frames from snap to pass forward (`k_pf`/10, s) | a QB/play property, not a player trait |
| targets | `player_play.target` (bool) | an outcome; used only as a secondary descriptive comparison |

**Coverage (WR):**
- 107 Combine WR; 94 with a valid tracked 40.
- 83 have regular-season routes; 73 have both routes and a valid tracked 40.
- Routes for those 73: 30,472. With tracking: 30,391. With a pass-forward event, and hence a defined `v`: **26,640** (87%).
- Routes without a defined `v`: sacks (96.5% missing) and scrambles (98.6%); ≤ 0.3% of completions, incompletions and interceptions.

## 2. Measurement compatibility

| aspect | Combine 40 | game route (pre-throw) | compatible? |
|---|---|---|---|
| unit, channel, sampling | yd/s, provider `s`, 10 Hz | yd/s, provider `s`, 10 Hz | yes |
| `s` vs 10 × frame displacement at ≥ 8 yd/s (median ratio) | 1.003 (5,900 WR frames) | 0.995 (164,178 WR frames) | about 0.8% system offset; small next to the thresholds, but not zero |
| task | maximal straight-line sprint, from a stance, 40 yd | route with cuts, at whatever effort the route needs, ended by the throw | **no** |
| window | ≈ 16 frames per attempt within 5% of peak | pre-throw window: median 2.7 s on deep routes (p90 4.1 s), 2.4 s on short routes | **no**: the game window is often shorter than the time needed to reach top speed |
| maximum statistic | max over the best of 2 attempts (upward selection) | max over one route's pre-throw frames | **no**: different number of frames and selection |
| truncation | none (the sprint reaches its peak) | the maximum falls **on the throw frame** in **55%** of deep, 37% of IN/CROSS and 28% of short routes | **no**: the throw, not the player, often ends the measurement |

**Consequences on the eligible 57 WR (26,640-route base):**
- No route reaches 95% of Combine peak. **R > 1 never occurs.**
- The highest ratio for any player is 0.92; the median player's highest ratio is 0.87.
- Median ratio: deep 0.68, IN/CROSS 0.65, short 0.54.

**Verdict:** the two numbers share units and sampling but **not measurement conditions**. R is therefore **not** "percentage of physical capacity". It mixes:
- route depth;
- time to throw (a QB and play property);
- the window truncation;
- different maximum statistics.

## 3. Candidate metric (definition only; evaluated, not adopted)

For route j of player i (regular season, with a pass-forward event):

  R_ij = v_ij / x_peak_i, with v_ij = max_{snap ≤ t ≤ pass forward} s_ij(t)

Player summaries over a route set S (all routes, or a context):
- A_q,i = (1/|S_i|) Σ_j 1[R_ij ≥ q], for q ∈ {0.80, 0.85, 0.90};
- R_p90,i = 90th percentile of R_ij;
- R_top5,i = mean of the 5 largest R_ij.

**Controls (no Combine denominator):**
- V_p90 / V_top5: the same summaries of v_ij;
- A_q with a constant denominator (the median x_peak, 11.09 yd/s);
- O_q: the share of routes ≥ q × the player's own top-5 game speed.

## 4. Sample sizes (eligible: ≥ 100 routes with defined v, valid tracked 40)

| | value |
|---|---|
| players with any route / ≥ 50 / **≥ 100** / ≥ 200 | 73 / 63 / **57** / 41 |
| routes per eligible player | min 119, median 370, max 1,301 |
| deep / short routes per player | median 141 (min 47) / 144 (min 31) |
| games per player | median 25 (10–50) |
| seasons per player (1 / 2 / 3) | 17 / 22 / 18 |

The eligible set is essentially the registered H1-WR cohort (57). It is **not an independent sample**.

**Threshold exceedances per player, all routes:**

| threshold | median routes at or above it | players with ≤ 3 | players with 0 |
|---|---|---|---|
| 80% | 14 (p10 4, p90 39) | 7% | 0% |
| 85% | **3** (p10 0, p90 7) | **60%** | 25% |
| 90% | **0** | 100% | **89%** |

**Share of routes at or above each threshold, by context:**
- 80%: deep 8.4%, IN/CROSS 4.1%, short 0.09%;
- 85%: deep 1.7%, short 0.01%;
- 90%: deep 0.05%, short 0.

## 5. Reliability and sensitivity

Split-half reliability by alternating games (Spearman–Brown corrected; 95% CI from resampling players; 57 WR):

| metric | all routes | deep only | GO/POST | short only |
|---|---|---|---|---|
| A80 (ratio) | 0.75 [0.60, 0.87] | 0.78 [0.60, 0.89] | 0.76 | −0.04 |
| A85 (ratio) | 0.84 [0.57, 0.93] | 0.76 [0.26, 0.93] | 0.65 [−0.15, 0.91] | not defined |
| A90 (ratio) | 0.86 [**−0.14**, 0.98] | −0.06 | 0.84 [−0.12, 1.00] | not defined |
| R_p90 / R_top5 (ratio) | 0.86 / 0.84 | 0.79 / 0.83 | 0.78 / 0.80 | 0.68 / 0.77 |
| **V_p90 / V_top5 (game only)** | **0.90 / 0.89** | 0.83 / 0.88 | 0.83 / 0.86 | 0.71 / 0.78 |
| A80 / A85, constant denominator | 0.83 / 0.85 | 0.81 / 0.75 | 0.73 / 0.79 | 0.32 / — |
| O80 / O85 / O90 (own top, game only) | 0.78 / 0.84 / 0.79 | 0.56 / 0.63 / 0.74 | 0.66 / 0.72 / 0.68 | 0.70 / 0.68 / 0.74 |

**Chronological split** (first vs second half of the player's games): every metric is lower, e.g. A85 0.61, R_p90 0.75, V_p90 0.81, O90 0.43. Part of the alternating-game value is shared team-season context.

**Matched route counts** (alternating games; both halves subsampled to n routes; 30 repeats):

| routes per half | players | A80 | A85 | A90 | R_p90 | V_p90 | V_top5 |
|---|---|---|---|---|---|---|---|
| 25 | 57 | 0.42 | 0.45 | 0.48 | 0.50 | 0.58 | 0.66 |
| 50 | 55 | 0.56 | **0.37** | −0.04 | 0.68 | 0.77 | 0.77 |
| 100 | 40 | 0.72 | **0.43** | −0.07 | 0.81 | 0.85 | 0.81 |
| deep only, 50 | 32 | 0.66 | 0.45 | — | 0.69 | 0.83 | 0.83 |

**Whole-play definition** (`vmax_play`; includes sacks, scrambles and post-throw running): A80 0.86, A85 0.89, A90 0.65, R_p90 0.86. It looks more stable, but it measures a different thing: post-catch and ball-tracking running.

**Dominance by a few plays:**
- Dropping each player's 3 fastest routes leaves R_p90 and R_top5 rankings intact (rank correlation 0.97 / 0.95).
- It reorders A85 substantially (0.60): A85 rests on a handful of routes.

**Individual comparisons** (95% CI by resampling each player's games):

| metric | median value | median CI width | player pairs with non-overlapping CIs |
|---|---|---|---|
| A80 | 0.043 | 0.038 | 30% |
| A85 | 0.007 | 0.014 | 22% |
| A90 | 0 | 0 | 0% |

- A85 rank: median 95% rank interval spans **25 of 57 places**; 35% of players span more than half the list.

**Route mix, time to throw and count dependence** (Spearman, player level):
- A80 and A85 rise with deep-route share (0.29 / 0.22) and with mean time to throw (0.18 / 0.21).
- Top-5 summaries rise with route count (V_top5 +0.40, R_top5 +0.34): an extreme-value effect, where more routes give more chances for a high maximum.
- The own-top share falls steeply with route count (O90 −0.70).
- p90 is the least count-dependent summary (V_p90 −0.13; deep only −0.08).

**Deployment descriptors** (alternating-game reliability; game-only labels):

| descriptor | reliability |
|---|---|
| deep-route share | 0.86 |
| short-route share | 0.87 |
| GO share | 0.80 |
| in motion at snap | 0.93 |
| trips-or-more alignment | 0.86 |
| mean time to throw | 0.73 (a team/QB property) |

Deep target rate (secondary, descriptive; targets are an outcome and partly a QB decision): 0.67 [0.40, 0.86].

## 6. Limitations

1. **Not capacity utilisation.** The ratio's numerator is truncated by the throw (55% of deep routes peak on the throw frame) and measured under different task conditions. It is never above 0.92 of the denominator. Calling R "percentage of physical capacity" is not supported.
2. **Physical speed opportunity is not measurable.** There is no ball flight, defender or assignment data. Route labels and deep share describe the call, not whether a sprint to top speed was possible. Time to throw is a QB/play property. Defining opportunity from the observed speed itself would be circular, and this audit does not do so.
3. **The thresholds are empty or near-empty at 85–90%.** A90 is zero for 89% of players. A85 rests on a median of 3 routes. Neither supports individual comparisons.
4. **The Combine denominator adds no stability.** Game-only summaries (V_p90 0.90) are at least as reliable as their ratio versions (R_p90 0.86). A constant denominator is as stable as each player's own (A80 0.83 vs 0.75). The ratio's player-to-player differences are driven by game speed and route mix, with the Combine value only rescaling them.
5. **Confounding by deployment and play timing.** Attainment rises with deep share and time to throw. Top-k summaries depend on route count.
6. **Sample.** 57 players, the same cohort as the registered H1-WR analysis, 1–3 seasons each. The chronological split is weaker than the alternating-game split (shared team-season context).
7. **Overlap with the registered finding.** A per-player ratio of game speed to Combine speed restates, player by player, the relation the registered H1 analysis already estimated (with its uncertainty), plus measurement noise. It is not new information beyond the deep-versus-short findings.

## 7. Decision

Pre-stated GO conditions:

| condition | met? |
|---|---|
| measurements comparable for the intended interpretation | **no** (task, window and truncation differ; R ≤ 0.92) |
| deployment operationalised independently of speed attainment | **partly**: route-label shares are independent and stable, but they are not physical opportunity, which cannot be measured |
| individual estimates sufficiently stable | **no** for A85/A90 (matched 0.37–0.45; 22% of pairs separable; rank intervals ≈ 25 places); A80 only moderately stable (0.56 at 50 routes per half) |
| not mainly driven by play counts or route mix | **no** (deep share, time to throw and route count all move the metrics) |
| information beyond the existing deep-versus-short findings | **no** (the ratio rescales game speed by a constant per player) |

**NO-GO** for the Combine-to-Game Speed Profile as specified. Specifically, no R_ij-based "percentage of Combine speed" or attainment-threshold player card.

## 8. Narrower alternative (proposal only; not implemented, not approved)

**A game-only "Route Speed and Deployment" descriptor**, kept separate from the Combine value:
- **Speed:** a player's deep-route 90th-percentile pre-throw speed (V_p90, yd/s).
  - It is the most stable and least count-dependent summary: alternating-game 0.83 on deep routes; matched at 50 deep routes per half 0.83; ρ with route count −0.08.
  - It would be reported with a game-resampling interval, and only for players with ≥ 50 deep routes.
- **Deployment, shown next to speed and never combined with it:** deep / short / GO shares, alignment and motion rates (0.80–0.93), and the median time to throw on those routes as context.
- **Combine reference:** tracked 40 peak shown as a separate number. No ratio, and no "% of capacity" wording.

**What it could support:** a description of how fast a receiver ran on deep routes and how they were deployed. **What it cannot support:** capacity utilisation, effort, opportunity, or prediction.

**Prerequisites before any implementation:**
- the lead's approval;
- a written definition fixed before computing player values;
- an interval and minimum-sample rule;
- a statement that it is descriptive and separate from the registered study.

It would add little to the existing deep-versus-short findings for the competition entry, so **it is not recommended for the current submission.**
