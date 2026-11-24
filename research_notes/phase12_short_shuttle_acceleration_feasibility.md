# Phase 12: short-shuttle straight-exit acceleration (measurement feasibility only)

**Run:** `20261124T144434Z`, produced by `scripts/run_shuttle_accel_feasibility.py`. Settings: seed 1111; player bootstrap B = 2000 for the reference configuration and 500 for each sensitivity variant.

**Code:**
- `src/nfl_bdb/features/shuttle_accel.py`: a new shuttle-specific definition. It does not reuse the three-cone detector or feature.
- `tests/test_shuttle_accel.py`: 10 synthetic-trajectory tests.
- Full suite: 75/75 passing, including the code-freeze test.

**Outputs (git-ignored):**
- `data/interim/phase12_shuttle_accel/<run>/{attempts,reversals,player_features,athletes}.parquet`;
- `experiments/phase12_shuttle_accel/<run>/` (aggregate tables, `summary.json`).

**Scope:**
- **Inputs:** combine tracking (SHORT_SHUTTLE rows), combine results, and, for Section 7 only, the git-ignored combine-only Phase 11.1 three-cone table.
- **Game data:** no game, outcome or confirmatory-join file was opened.
- **Unchanged:** no registered analysis, frozen file or Phase 11 result was changed.
- **Threshold choice:** no threshold was chosen using reliability or outcome associations.

## Bottom line

**The shuttle does provide a genuinely straight post-turn window. The 10 Hz measurement of acceleration in it is not repeatable within position.**

**The window is straight.** After the first touch reversal (R1), the 0.5-s window starts a median 0.2 s after the speed minimum, and inside it:
- heading changes 11°;
- 2% of the squared acceleration is centripetal (three-cone late loop: 56%);
- the path straightness is 1.00 and the lateral spread 0.09 yd.

**The acceleration measured there is not repeatable:**
- pooled ICC(3,1) 0.46 [0.20, 0.73];
- **within-position ICC 0.21 [−0.16, 0.42]**;
- position alone explains 50% of the variance in player means.

**Why:**
- With a window this close to the stop, the slope depends on where the window happens to start on the acceleration curve.
- One 10 Hz frame later changes it by about 0.8 yd/s², the size of the between-athlete SD (0.79).
- The start speed itself is not repeatable (ICC −0.12).
- Moving the window 0.2–0.3 s later drops ICC to 0.27 and 0.16.

**The second reversal (R2)** gives a *negative* ICC (−0.24).

**Recommendation: NO-GO** for straight-exit acceleration as defined (R1 and R2), and **NO-GO** for outcome validation. The movement phase is the right one; the measurement is not yet good enough.

## 1. Raw data audit (recomputed)

| item | count |
|---|---|
| short-shuttle attempts (PLAYER rows, distinct `event_id`) | **223** |
| athletes | **170** |
| attempts per athlete | 1: 128, 2: 33, 3: 7, 4: 2 → **42 athletes with repeated recordings** |
| duplicate (player, attempt) / non-100-ms frame gaps | 0 / 0 (all 11,467 gaps = 100 ms) |
| frames per attempt | median 51 (5th–95th percentile 45–64) |
| path length | median 15.3 yd. Body sensor, against 20 yd nominal: the athlete reaches to touch the lines |
| range along / across the drill line | median 7.3 / 0.75 yd |
| provided speed > 12.5 yd/s | 0 |
| median \|position-derived speed − provided `s`\| per attempt | 0.10 yd/s |
| too short (< 15 frames) | 2 (11 and 12 frames) |
| 0 reversals | 1 more: a 19-frame recording with 0.9 yd of movement |
| only 1 reversal | 10 (partial recordings: 29–36 frames or ending early) |
| **both reversals visible** | **210** |
| R1 visible / R2 visible | 220 / 210 |
| recording already moving (≥ 1 yd/s) at the first frame | 37 |
| still moving at the last frame | 219 (recordings end during the final sprint) |

**Unusual recordings, from inspecting the trajectories:**
- one 202-frame recording has about 15 s of standing before the drill;
- one 86-frame recording has a slow walk after the drill;
- the short ones are fragments.

The legs-based detector (below) handles the idle periods. Fragments yield no valid reversal.

**Validity per reversal (reference configuration):**

| | R1 (primary) | R2 (secondary) |
|---|---|---|
| visible | 220 | 210 |
| valid | **211 attempts / 163 athletes** | 203 / 158 |
| invalid: approach not observed (< 5 straight incoming frames) | 8 | 0 |
| invalid: no straight exit before the next leg ends | 1 | 0 |
| invalid: window not straight | 0 | 1 |
| invalid: window cut by the end of the recording | 0 | 6 |
| athletes with ≥ 2 valid | **37** (2: 28, 3: 7, 4: 2) | 37 |

**R1 by position:**

| position | attempts | athletes | R1 valid athletes | ≥ 2 valid |
|---|---|---|---|---|
| DB | 36 | 28 | 26 | 5 |
| DL | 44 | 38 | 38 | 4 |
| OL | 70 | 54 | 49 | 12 |
| TE | 37 | 21 | 21 | 10 |
| WR | 36 | 29 | 29 | 6 |

**Other measures for the 163 R1-valid athletes:**
- official short shuttle 153;
- three-cone 120;
- forty and 10-yd split 145.

**Consistency with Phase 2:** `combine_execution_cost.md` listed 225 shuttle attempts (158 valid for gate timing, 28 players with two valid). This phase counts 223 distinct `event_id`s. The 2-attempt difference was not reconciled; Phase 2 may have used a different attempt key. That earlier phase found tracking-derived shuttle *drill times* non-repeatable, which pointed to gating problems. The present measurement uses no gates.

## 2. Turn detection and straight-exit definition

All definitions below were fixed before any repeatability statistic was computed.

**Drill axis and legs:**
- **Kinematics:** Savitzky–Golay smoothing of x and y (window 7, order 2); speed from the SG derivative (vendor `s` as a sensitivity option); heading only where speed ≥ 1 yd/s.
- **Drill axis:** first principal direction of the attempt's positions. u = velocity projected on the axis.
- **Legs:** runs of ≥ 3 frames with |u| ≥ 1.5 yd/s and constant sign; same-sign legs are merged.
- **Reversal:** sits between consecutive legs of opposite sign. R1 = first, R2 = second.
- R1 and R2 are analysed separately and never pooled: R1 follows a 5-yd leg and opens the 10-yd leg; R2 follows the 10-yd leg and opens the finish.

**Turn and window:**
- **Minimum-speed region:** i_min = argmin speed between the two legs (±1 frame).
- **Straight frame for direction d:** speed ≥ 1 yd/s and velocity within **15°** of d × axis.
- **Turn region:** from the frame after the last straight incoming frame up to the first straight outgoing frame k0 (exclusive).
- **Measurement window:** frames k0 … k0 + 5 (6 frames, 0.5 s). Straight-exit acceleration = OLS slope of speed on time.

**A window is valid only if all of these hold:**
- every window frame is straight for the outgoing direction;
- the window lies inside the recording;
- the window ends before the next reversal's leg ends;
- at least 5 straight incoming frames precede the turn (an observed approach).

**Criteria are never relaxed:** invalid windows are reported, not repaired.

**Why 15°:** this was fixed from geometry only. Across 4,978 mid-leg frames (|u| ≥ 3 yd/s), the deviation of the velocity from the drill axis is:
- median 2.7°;
- 95th percentile 9.7°;
- 99th percentile 15.7°.

So 15° admits normal straight-running wobble and excludes turning. 10° and 20° are sensitivity values.

## 3. Window-overlap and straightness checks

Medians (5th–95th percentile) over valid windows:

| check | R1 window | R2 window | three-cone late-loop window (Phase 11.1) |
|---|---|---|---|
| windows overlapping the turn region | **0** of 211 | 0 of 203 | 117 of 193 entirely inside the turn |
| time from speed minimum to window start | 0.2 s (0.1–0.3) | 0.2 s (0.1–0.5) | 0 (starts at the minimum) |
| turn region duration | 0.3 s (0.2–0.7) | 0.3 s (0.2–0.6) | — |
| heading change across the reversal | 166° (154–178) | 163° (154–178) | — |
| max deviation from axis in window | 6.7° (2.3–13.9) | 9.4° (2.9–14.5) | — |
| heading change within window | **11°** (1–27) | 10° (1–23) | **110°** (93–132) |
| max \|heading rate\| in window | 55°/s (9–159) | 49°/s (7–164) | mean 184°/s |
| centripetal share of squared acceleration | **0.02** (0.00–0.08) | 0.02 (0.00–0.09) | **0.56** (0.34–0.74) |
| straightness (chord / path) | 1.00 | 1.00 | — |
| lateral spread in window | 0.09 yd (0.03–0.24) | 0.12 yd (0.03–0.38) | — |
| speed at window start | 1.39 yd/s (1.01–1.99) | 1.53 (1.06–3.13) | — |
| outgoing leg's speed peak reached inside window | 0% | 1% | — |
| entry speed (max in 1 s before minimum) | 3.15 yd/s (2.66–3.52) | 5.42 (4.83–5.83) | — |
| minimum speed | 0.29 yd/s (0.09–0.58) | 0.36 (0.10–0.68) | — |

**Conclusion:** the shuttle windows are straight, linear-acceleration windows. That is a real difference in movement phase from the three-cone late loop.

## 4. Reliability (primary: R1)

**Method:**
- Pairs are each athlete's first two valid attempts, in chronological order.
- The unit is the athlete; frames are never treated as samples.
- Within-position values centre both attempts on the position mean.
- CIs come from a player bootstrap (B = 2000).

| | **R1 straight-exit acceleration** | R2 straight-exit acceleration |
|---|---|---|
| valid attempts / athletes | 211 / 163 | 203 / 158 |
| athletes with 2 valid | 37 | 37 |
| mean (SD), yd/s² | 6.14 (0.79) | 5.65 (1.33) |
| 5th / 50th / 95th percentile | 4.91 / 6.20 / 7.31 | 3.15 / 5.84 / 7.29 |
| ICC(3,1) [95% CI] | **0.46 [0.20, 0.73]** | **−0.24 [−0.40, −0.05]** |
| ICC(2,1) [95% CI] | 0.44 [0.18, 0.71] | −0.22 [−0.37, −0.05] |
| Spearman [95% CI] | 0.53 [0.22, 0.77] | −0.18 [−0.48, 0.18] |
| typical error (% of mean) | 0.63 yd/s² (10.6%) | 1.75 yd/s² (34%) |
| mean change, attempt 2 − 1 | +0.32 | +0.71 |
| **within-position ICC(3,1)** | **0.21 [−0.16, 0.42]** | −0.30 [−0.52, −0.17] |
| per position (pairs) | OL 0.64 (12), TE 0.12 (10); DB 5, DL 4, WR 6: not reportable | OL −0.18 (11), TE −0.37 (10) |

**Aggregation across attempts** (R1, athletes with ≥ 2 valid): mean vs median ρ 0.99, mean vs first 0.91, mean vs best 0.87, first vs best 0.70. Use the mean if anything is ever carried forward.

**Interpretation:**
- **Typical error is acceptable; between-athlete spread is not.** The 10.6% error looks acceptable on its own, but the true between-athlete spread within position is small relative to it, so ranking athletes within a position is unreliable.
- **Pooled ICC reflects position, not athletes.** The pooled 0.46 comes mostly from position differences: position explains R² 0.50 of player means.
- **R2 is worse than noise.** It shows a negative test-retest association and a systematic increase between attempts. The R2 window falls in the final sprint, where finishing behaviour varies.

## 5. Sensitivity analyses (one change at a time)

| configuration | R1 valid / pairs | R1 ICC(3,1) [95% CI] | R1 within-position | R1 rank agreement with reference | R2 ICC |
|---|---|---|---|---|---|
| **reference** (pos, SG 7, 15°) | 211 / 37 | 0.46 [0.20, 0.73] | 0.21 | 1 | −0.24 |
| SG window 5 | 211 / 37 | 0.47 [0.20, 0.74] | 0.20 | 0.99 | −0.23 |
| SG window 9 | 212 / 37 | 0.43 [0.19, 0.65] | 0.19 | 0.98 | −0.22 |
| SG window 11 | 213 / 38 | 0.50 [0.27, 0.71] | 0.27 | 0.97 | −0.13 |
| vendor speed | 211 / 37 | 0.53 [0.32, 0.72] | 0.31 | 0.96 | −0.25 |
| SG-smoothed vendor speed | 211 / 37 | 0.54 [0.33, 0.73] | 0.33 | 0.97 | −0.25 |
| straightness 10° | 198 / 34 | 0.38 [0.19, 0.67] | 0.24 | 0.91 | −0.22 |
| straightness 20° | 216 / 39 | 0.41 [0.16, 0.66] | 0.10 | 0.98 | −0.14 |
| window start +1 frame | 211 / 37 | 0.38 [0.11, 0.62] | 0.19 | 0.97 | −0.30 |
| window start +2 frames | 211 / 37 | 0.27 [−0.05, 0.48] | 0.19 | **0.79** | −0.32 |
| window start +3 frames | 211 / 37 | 0.16 [−0.19, 0.45] | 0.13 | **0.34** | −0.23 |

**What changes the result:**
- **Smoothing, speed source and straightness threshold:** change the ranking little (ρ ≥ 0.91). Reliability stays at 0.38–0.54 pooled and 0.10–0.33 within position.
- **Window placement:** dominates. The start-offset runs, a diagnostic for SG-kernel overlap with the turn, show that delaying the window by 0.2–0.3 s re-orders athletes (ρ 0.79 and 0.34) and removes most of the reliability.
- **Where the signal sits:** whatever repeatable signal exists is concentrated in the first 0.1–0.2 s of re-acceleration. There the SG kernel (±0.3 s) still spans part of the reversal, and the measurement is most sensitive to frame timing.

## 6. Construct checks (associations, not causal)

| R1 straight-exit acceleration vs | attempts ρ [95% CI] | within position | within athlete Δ (n = 37) |
|---|---|---|---|
| entry speed before the reversal | +0.25 [0.11, 0.38] | +0.19 | +0.10 |
| minimum speed | −0.06 [−0.20, 0.09] | −0.21 | −0.33 |
| speed at window start | −0.19 [−0.33, −0.04] | −0.30 | **−0.55** |
| time from minimum to window start | **−0.51 [−0.60, −0.39]** | −0.52 | **−0.59** |
| turn region duration | −0.38 [−0.51, −0.25] | −0.44 | **−0.64** |
| heading change across the reversal | +0.12 [−0.03, 0.25] | +0.24 | +0.13 |
| window centripetal share | −0.12 | −0.25 | −0.31 |

| player mean vs official measure | pooled ρ [95% CI] | within position |
|---|---|---|
| official short shuttle (n = 153) | −0.69 [−0.78, −0.57] | −0.29 |
| official three-cone (n = 120) | −0.68 [−0.77, −0.55] | −0.25 |
| official forty (n = 145) | −0.76 [−0.82, −0.68] | −0.30 |
| official 10-yd split (n = 145) | −0.79 [−0.85, −0.70] | −0.38 |
| R2 straight-exit acceleration (n = 154) | +0.45 [0.31, 0.59] | +0.28 |

**Window-start quantisation** (R1, valid windows):

| window starts after the minimum | attempts | mean acceleration (yd/s²) | mean start speed (yd/s) |
|---|---|---|---|
| 0.1 s | 19 | 7.02 | 1.06 |
| 0.2 s | 163 | 6.19 | 1.39 |
| 0.3 s | 24 | 5.43 | 1.89 |
| 0.4 s | 4 | 4.43 | 2.23 |
| 0.5 s | 1 | 4.01 | 2.66 |

**Explained variance (player means):**
- position alone R² 0.50 (adjusted 0.49);
- + 10-yd split, adjusted R² 0.61;
- + shuttle, forty and 10-yd split together, adjusted R² 0.62.

**Residual test-retest (attempt level, position-adjusted)** after removing:
- start speed: 0.22 [−0.01, 0.59];
- entry speed: 0.20;
- minimum speed: 0.17;
- time to window: −0.08.

**Test-retest of the covariates themselves:**
- entry speed 0.55;
- minimum speed 0.47;
- turn duration 0.49;
- time to window 0.30;
- **speed at window start −0.12**.

**Interpretation:**

1. **Turn execution and timing dominate, not entry speed.**
   - The measurement mostly reflects *where on the re-acceleration curve the window starts*. That in turn depends on how long the athlete stays in the turn region and on which 10 Hz frame first crosses 1 yd/s with a straight heading.
   - Within athletes, a 0.1-s later start comes with a lower slope: ρ −0.59 with time to window, −0.64 with turn duration.
   - Because early acceleration is steepest, one frame of timing (about 0.8 yd/s²) is as large as the between-athlete SD.
   - Entry speed contributes little (within athlete +0.10).
2. **Pooled, it is a general speed-and-position factor.** It tracks the 10-yd split, forty and official shuttle times strongly (ρ −0.69 to −0.79). Within position, the association weakens to −0.25 to −0.38. With a within-position reliability of about 0.2, there is too little repeatable athlete-specific variance to show information beyond straight-line speed.
3. **Once timing is removed, nothing repeatable remains.** After adjusting for start speed or time to window, the residual is not repeatable (0.22 and −0.08). So no distinct, repeatable straight-line speed-gain component is detected.

## 7. Comparison with the three-cone late-loop speed gain (Phase 11 / 11.1)

| question | answer |
|---|---|
| Does the shuttle give a genuinely straight post-turn window? | **Yes.** No overlap with the turn; 11° of heading change and 2% centripetal share, against 110° and 56% in the three-cone late loop |
| Better or worse repeatability? | **Worse within position.** Shuttle R1: 0.46 pooled / 0.21 within position. Three-cone late-loop: 0.64 / 0.60 (Phase 11.1). The three-cone's higher ICC is not evidence of validity: Phase 11.1 showed it is bound up with turn shape (ρ −0.94 with centripetal share within athletes) |
| Is the measurement error acceptable? | TE 0.63 yd/s² (10.6%) is similar to the three-cone's (12%). But within-position between-athlete variance is small, and one-frame timing shifts are as large as the between-athlete SD. **Not acceptable for ranking athletes within position** |
| Different movement phase? | **Yes.** Shuttle: straight re-acceleration from about 1.4 to about 3 yd/s. Three-cone: speed gain while still turning. Across 114 athletes with both, player means correlate ρ 0.31 [0.13, 0.49] pooled and **0.08 within position**, so the two are not the same measurement |
| Is the repeat sample large and representative? | **No.** See below |

**Shuttle repeat-sample problems:**
- **Small:** 37 athletes; position-specific reliability is reportable only for OL (12 pairs) and TE (10).
- **Position mix:** repeaters are over-represented among TE (10 of 21) and OL (12 of 49) and under-represented among DL (4 of 38); χ² p = 0.027.
- **Lower first attempts:** repeaters' *first-attempt* acceleration was lower within position (mean z −0.51 vs +0.15; Mann–Whitney p = 0.01, uncorrected). Their official shuttle, three-cone, forty and 10-yd times do not differ (p 0.17–0.52). This is consistent with athletes re-running after a weaker first attempt, which would add regression to the mean to the test-retest pairs.
- **No common reliability sample:** only 5 athletes repeated both the shuttle and the three-cone.

## 8. Limitations

- **10 Hz sampling.** The re-acceleration out of a touch reversal is fast (about 6 yd/s²). At 10 Hz the window start can only move in 0.1-s steps, and each step changes the slope by about 0.8 yd/s². This is the main source of error and cannot be removed by smoothing choices.
- **SG kernel overlap.** With window 7 the kernel is ±0.3 s. At the window start, the smoothed velocity still contains frames from the reversal. Shifting the window later removes the overlap but also removes the repeatable signal.
- **Fixed definition, no alternatives tried.** Every threshold was fixed by geometry before repeatability was looked at, and no alternative definition (for example a window anchored at a fixed time after the minimum, sub-frame interpolation of the 1 yd/s crossing, or a model-based acceleration fit) was tried. Any of these would be a new definition and needs separate approval and pre-specification.
- **Repeat sample.** It is small, position-imbalanced, and may be selected on a weaker first attempt.
- **Body sensor.** Touches are made with the hand, and the sensor path is about 15 yd instead of 20.
- **R2 window placement.** It falls in the finish sprint, where pacing at the line varies. Its negative test-retest is not interpretable as an athlete property.
- **No validity check.** Nothing here establishes validity against an external criterion. By instruction, none was examined.

## 9. Recommendation

| measurement | decision | basis |
|---|---|---|
| **R1 straight-exit acceleration** (as defined) | **NO-GO** | The window is truly straight and post-turn (the construct issue of Phase 11.1 is solved). But within-position ICC is 0.21 [−0.16, 0.42], the pooled 0.46 is mostly position, and the value is driven by 10 Hz window-start timing (within-athlete ρ −0.59 with time to window). Nothing repeatable remains after removing start speed or timing. The repeat sample is small and selected |
| R2 straight-exit acceleration (secondary) | **NO-GO** | ICC −0.24 [−0.40, −0.05]; TE 34% |
| Short shuttle as a *setting* for post-turn acceleration | **CONDITIONAL GO for method work only** | The geometry is right, unlike the three-cone. Any further attempt needs a new, pre-specified definition that handles 10 Hz start-time quantisation (for example time-anchored or sub-frame methods), justified on synthetic data before any repeatability statistic is computed. It also needs a plan for the 37-athlete, selected repeat sample |
| Proceeding to NFL outcome validation with any shuttle or three-cone acceleration feature | **NO-GO** | No candidate has both a valid construct and adequate within-position repeatability |

No outcome validation has been started.
