# Phase 11, Stage 1: three-cone turn retention and recovery (measurement feasibility only)

**Run:** `20261124T140625Z`, produced by `scripts/run_turn_recovery_feasibility.py`. Settings: seed 1111; B = 2000 bootstrap resamples for the reference configuration and 500 for each sensitivity configuration.

**Code:**
- `src/nfl_bdb/features/turn_recovery.py`: detection and features;
- `src/nfl_bdb/evaluation/repeatability.py`: ICC, typical error, within-position centring, bootstrap. It reuses the frozen `forty_reliability.icc` read-only.
- `tests/test_turn_recovery.py`: 15 synthetic-trajectory tests, all passing. The full suite passes 57/57, including the code-freeze test.
- `notebooks/12_turn_recovery_feasibility.ipynb`: committed with outputs stripped. Rebuild it with `scripts/build_notebook_12.py --execute`, which writes the executed copy to the git-ignored `build/`.
- Aggregate figures: `reports/figures/phase11_turn_reliability.png` and `phase11_turn_sensitivity.png`.

**Outputs (git-ignored):**
- `data/interim/phase11_turn_recovery/<run>/{attempts,turns,player_features}.parquet`;
- `experiments/phase11_turn_recovery/<run>/`: config, summary and aggregate tables.

**Scope and discipline:**
- Combine data only. No NFL game outcome was read, joined or modelled.
- The only game-side input is a per-player *count* of REG `player_play` rows, used for the coverage audit.
- No registered analysis, preregistration, frozen file or registered result was changed.
- Every threshold was fixed by inspecting trajectory geometry before any reliability number was computed. None was chosen by correlation with any outcome.
- The features are descriptive measurements, not algorithms. No novelty is claimed.
- Correlations are associations between measurements, not causal effects.

## Summary

- **Turn-recovery features can be measured on 193 of 203 attempts (155 athletes), but only 34 athletes have two valid attempts. Single-attempt test-retest reliability is moderate at best:** ICC(3,1) runs from 0.28 to 0.64, and every 95% CI spans roughly 0.3–0.4.
- **The most reliable and least processing-sensitive feature is re-acceleration out of the far-cone loop (C).**
  - ICC 0.64 [0.42, 0.81]; within position 0.60.
  - Player rank agreement across all processing variants is ≥ 0.89.
- **Speed retention through the loop is not a stable athlete trait:**
  - ICC 0.49 [0.13, 0.72].
  - It is almost the same quantity as minimum speed (ρ 0.97).
  - It trades off against re-acceleration *within the same athlete* from attempt to attempt (ρ of the attempt-2 − attempt-1 differences = −0.72). This looks like a turn-shape choice rather than an ability.
- **Recovery time is processing-sensitive.** It depends on the speed source, the smoothing window and the stop threshold.
- **No feature is ready for outcome validation as a confirmatory test.**
  - Even the best feature would enter an outcome analysis with player-level reliability of about 0.64, because most athletes have one attempt.
  - Only 8–33 athletes per position have ≥ 100 REG plays.
  - At those sizes, the detectable observed correlation is about 0.5–0.7.

## A. Data audit (recomputed from raw tracking)

| item | count |
|---|---|
| three-cone attempts (PLAYER rows, distinct `event_id`) | **203** |
| athletes | **160** |
| attempts per athlete (raw) | 1: 122, 2: 33, 3: 5 |
| analysable (≥ 20 frames, moving) | 202. One failure, `too_short` (10 frames). A second short event (33 frames) is analysable but non-template |
| **template-valid** (R1, R2, C matched) | **193 attempts / 155 athletes** |
| non-template | 9 (aborted or single-turn recordings, extra stumbles, recording ending mid-turn) |
| valid attempts per athlete | 1: 121, **2: 30, 3: 4 → 34 athletes with ≥ 2 valid attempts** |
| duplicated (player, attempt) pairs / frame-gap anomalies | 0 / 0 (every Δt = 100 ms) |

Recordings start at rest or slowly: first-frame speed has a median of 0.62 yd/s and a maximum of 1.9. **74% of valid attempts** therefore begin with a "turning" run (speed < 1 yd/s), which is discarded and flagged `truncated_start`. This is the start stance, not a tracking failure: no turn is lost, because R1 is always preceded by an approach.

**By position:**

| position | attempts | athletes | valid athletes | ≥ 2 valid attempts | valid athletes with ≥ 100 REG play rows |
|---|---|---|---|---|---|
| DB | 31 | 24 | 24 | 7 | 17 |
| DL | 60 | 45 | 45 | 11 | 33 |
| OL | 55 | 48 | 44 | 7 | 24 |
| TE | 27 | 19 | 19 | 5 | 8 |
| WR | 30 | 24 | 23 | 4 | 17 |

**Other measures for the 155 valid athletes:**
- official three-cone 145;
- short shuttle 136;
- official forty 139;
- 10-yd split 139;
- valid tracked 40 (registered predictor table) 138;
- any REG `player_play` rows 122; ≥ 100 REG rows 99.

These numbers agree with the Phase 2 audit (`combine_execution_cost.md`: 203 attempts, 32 players with two attempts *before* the quality filter; 38 here, before the template filter).

**Is there enough repetition for repeatability?** Barely. Thirty-four pairs give a 95% CI about ±0.2 wide around an ICC near 0.6. Position-specific ICCs are reportable only for DL (11 pairs). The other positions have 4–7 pairs each, which is not reportable.

## B. Turn detection

**Kinematics:**
- Savitzky–Golay smoothing of x and y (window 7, order 2, 10 Hz).
- Speed is |v| from the SG derivative. The vendor `s` is a sensitivity option.
- Heading = unwrap(atan2(v_y, v_x)); heading rate is its time gradient.
- Combine `dis` and `a` are not used (`a` is unsigned; combine `dis` is not displacement).

**Turning frames:** |heading rate| ≥ 60°/s, *or* speed < 1 yd/s, because heading is undefined near a stop: the touch reversals pass through about 0.3 yd/s.

**Segments:**
- Contiguous turning frames form a segment; segments separated by ≤ 2 frames are merged.
- Segments that touch the first frame are discarded (start stance). Segments that touch the last frame are also discarded and flagged `truncated_end`.
- Frames are never treated as independent observations: the unit is the turn within an attempt, and statistics are computed per athlete.

**False turns:** a segment counts as a turn only if the chord heading change is ≥ 45°. The chord is the angle between the mean velocity directions over the 3 frames before and after the segment, using frames with speed ≥ 1 yd/s. Noise wiggles on straight runs are rejected; a unit test checks this with 0.01 yd noise.

**Template labelling** (three-cone geometry seen in the data):

| turn | definition |
|---|---|
| R1, R2 | first two turns; each chord ≥ 135° and near-stop (min speed < 1 yd/s). Touch-and-return reversals |
| B1 (optional) | 45–90° curve before C |
| C | next turn with chord ≥ 90°. The loop around the far cone |
| B2 (optional) | 45–90° curve after C |

Any extra turn makes the attempt non-template. Its turns are kept but unlabelled and excluded from the features.

**Multiple turns per attempt:** each turn is labelled and analysed separately. Its feature windows are bounded by its neighbours, as defined below.

**Feature definitions (per turn):**
- **Minimum speed:** speed at the minimum inside the segment ±1 frame.
- **Entry speed:** maximum speed in the 2.0 s before the minimum, but not before the previous turn's minimum. The entry search never reached the window edge.
- **Retention:** min / entry.
- **Recovery time:** time from the minimum to the first interpolated crossing of 0.9 × entry speed.
  - It is right-censored, and stored as missing, if the next turn starts first.
  - It is 0 if speed never fell below the target.
- **Re-acceleration:** slope of speed on time over 0.5 s after the minimum, truncated at the next turn and requiring ≥ 3 frames.
- **Duration:** length of the turning segment.
- **Heading change:** the chord plus the cumulative absolute heading change.

**Detection results (reference configuration, template attempts):**

| turn | n | entry (yd/s) | min | retention | recovery (s) | censored | re-acc (yd/s²) | chord |
|---|---|---|---|---|---|---|---|---|
| R1 | 193 | 2.68 | 0.32 | 0.12 | — | **90%** | 3.2 | 170° |
| R2 | 193 | 2.02 | 0.26 | 0.13 | 0.32 | 0% | 4.8 | 160° |
| B1 | 135 | 3.39 | 3.35 | 1.00 | 0 | 0% | 0.8 | 59° |
| C | 193 | 4.10 | 0.92 | 0.22 | 0.67 | 5% | 4.5 | 163° |
| B2 | 66 | 4.32 | 4.27 | 1.00 | 0 | 2% | 1.4 | 62° |

**Template patterns:**
- R1 R2 B1 C: 86;
- R1 R2 B1 C B2: 49;
- R1 R2 C: 41;
- R1 R2 C B2: 17.

**Detection caveat (seen in the notebook trajectories):** when B2 is not detected (127 of 193 attempts), the curve around cone B often merges into the C segment.
- 79 C turns (41%) have a chord < 135° (minimum 99°), and none of these attempts has a separate B2.
- This lengthens C **duration** (10th–90th percentile 0.6–2.0 s) and distorts the C **chord**.
- Minimum speed, entry speed, recovery and re-acceleration are unaffected: the speed minimum lies inside the loop, and with no B2 nothing censors the recovery.

## C. Player-level summaries

The player-level table (`player_features.parquet`, git-ignored) gives the **mean, median, first and best** valid attempt for every feature. "Best" is the maximum for retention and re-acceleration, and the minimum for recovery time.

**Agreement between summaries** (34 athletes with ≥ 2 attempts):
- mean vs median: ρ 0.96–1.00;
- mean vs best: 0.84–0.95;
- first vs best: 0.53–0.82.

Best-attempt selection uses the noisiest order statistic, and it is defined differently for athletes with 1 and 2+ attempts. **It is not used.** The recommended summary is the **mean of valid attempts**, with the number of attempts carried as a weight or reliability term. Spearman–Brown gives the reliability of a two-attempt mean as 2r/(1+r): 0.78 for C re-acceleration. But 121 of 155 athletes have only one valid attempt, so their scores carry single-attempt reliability.

## D. Reliability (the decisive task)

**Method:** first two valid attempts in chronological order, n = 34 athletes. Within-position values use attempts centred on the position mean. 95% player-bootstrap CIs (B = 2000).

| feature | ICC(3,1) [95% CI] | ICC(2,1) | Spearman | typical error (TE % of mean) | within-position ICC [95% CI] | ICC(1), all attempts |
|---|---|---|---|---|---|---|
| **C re-acceleration** | **0.64 [0.42, 0.81]** | 0.65 | 0.61 | 0.57 yd/s² (12%) | **0.60 [0.25, 0.78]** | 0.66 |
| R2 re-acceleration | 0.63 [0.40, 0.79] | 0.63 | 0.65 | 0.33 yd/s² (7%) | 0.59 [0.28, 0.73] | 0.61 |
| C entry speed | 0.62 [0.36, 0.78] | 0.62 | 0.55 | 0.19 yd/s (4.5%) | 0.44 [0.07, 0.65] | 0.63 |
| C recovery time (n = 31) | 0.58 [0.28, 0.80] | 0.56 | 0.53 | 0.06 s (8%) | 0.53 [0.09, 0.74] | 0.57 |
| C minimum speed | 0.56 [0.26, 0.75] | 0.54 | 0.46 | 0.16 yd/s (18%) | 0.54 [0.14, 0.72] | 0.43 |
| C duration | 0.54 [0.26, 0.77] | 0.52 | 0.53 | 0.39 s (30%) | 0.54 [0.18, 0.73] | 0.44 |
| **C retention** | **0.49 [0.13, 0.72]** | 0.47 | 0.40 | 0.044 (20%) | 0.47 [0.03, 0.69] | 0.37 |
| R1 retention | 0.48 [0.17, 0.69] | 0.49 | 0.40 | 0.050 (37%) | 0.43 [0.01, 0.63] | 0.48 |
| R2 retention | 0.44 [0.10, 0.69] | 0.44 | 0.29 | 0.055 (39%) | 0.38 [−0.06, 0.60] | 0.45 |
| R2 recovery time | 0.43 [0.15, 0.66] | 0.44 | 0.46 | 0.04 s (14%) | 0.34 [−0.05, 0.56] | 0.43 |
| R2 minimum speed | 0.28 [−0.04, 0.55] | 0.28 | 0.18 | 0.11 yd/s (42%) | 0.19 [−0.25, 0.43] | 0.28 |
| R1 recovery time | not estimable: 2 pairs, 90% censored | | | | | |

**Systematic change between attempts is negligible:**
- ICC(2,1) ≈ ICC(3,1);
- the mean difference for C re-acceleration is +0.03 yd/s² and for C retention +0.017.

Within-position centring changes ICCs only slightly. The exception is C entry speed (0.62 → 0.44), much of whose reliable variance is position.

**By position:** only DL has ≥ 8 pairs (n = 11):

| feature | DL ICC(3,1) |
|---|---|
| C retention | 0.69 |
| C re-acceleration | 0.54 |
| C recovery time (n = 9) | 0.26 |
| R2 re-acceleration | 0.63 |

With 11 pairs these are not interpretable beyond "not obviously different from pooled". Other positions have 4–7 pairs and are not reported.

**Reference point:** within-WR test-retest of the official 40 is R ≈ 0.94 (`forty_test_retest.md`). No turn feature comes close.

### Sensitivity to processing

Each setting was changed one at a time; n_pairs stays between 25 and 36. Full tables: `experiments/.../reliability.parquet` and `sensitivity.parquet`; figure: `reports/figures/phase11_turn_sensitivity.png`.

| feature | ICC range across 17 configurations | lowest rank agreement of player means vs reference | main driver |
|---|---|---|---|
| C re-acceleration | 0.55–0.68 | 0.89 (`provided_sg` speed) | speed source; reacc window shifts the level (4.2–4.6 yd/s²) |
| C retention | 0.44–0.52 | 0.98 | essentially insensitive (and essentially unreliable) |
| C recovery time | 0.44–0.67 | **0.80** (provided speed) | smoothing window (0.45 at w = 5, 0.67 at w = 9) and speed source (0.44–0.45 with vendor speed) |
| R2 re-acceleration | **0.17**–0.68 | 0.79 | **stop threshold** (v_stop 0.75: ICC 0.17); reacc window 0.3/0.8 s: 0.49/0.50 |
| R2 recovery time | **−0.06**–0.52 | **0.47** (provided_sg speed) | stop threshold (v_stop 0.75: −0.06) and speed source |

**Effect on the template-match rate:**
- 0.93–0.96 for most settings;
- 0.85 at ω_min 45°/s or v_stop 1.5 yd/s, where extra small turns appear.

**Entry window (1.0–3.0 s):** no effect on any feature.

**Recovery fraction (0.85 / 0.95):** shifts C recovery time (median 0.60 / 0.74 s) without changing its ranking (ρ ≥ 0.98).

### What retention measures

Across attempts:
- C retention ↔ C minimum speed: ρ 0.97;
- C retention ↔ duration: 0.82;
- C retention ↔ re-acceleration: −0.77.

**The trade-off also holds within athletes:** between an athlete's two attempts, the change in retention and the change in re-acceleration correlate at ρ = −0.72 (n = 34). A wider, rounder loop keeps more speed but leaves less to regain. A tight plant-and-go loop drops to a lower minimum and re-accelerates harder.

**Implications:**
- Retention, and to some degree re-acceleration, therefore reflect partly an *attempt-level choice of turn shape*, not only an athlete trait.
- "Higher retention" is not unambiguously "better".
- Re-acceleration measured from a lower minimum speed is mechanically favoured, since available acceleration falls with speed.
- Neither feature should be read as a pure capacity.

## E. Comparison with conventional combine measures (descriptive)

**Method:** player means; Spearman correlations with player-bootstrap 95% CIs; within-position values use position-centred ranks.

| feature | three-cone | short shuttle | forty | 10-yd | tracked peak | within-position ρ with three-cone |
|---|---|---|---|---|---|---|
| C re-acceleration | −0.39 [−0.52, −0.24] | −0.34 | −0.33 | −0.36 | +0.33 | **−0.08** |
| C retention | +0.12 [−0.04, 0.28] | +0.06 | +0.04 | +0.09 | −0.04 | −0.02 |
| C recovery time | +0.18 [0.02, 0.34] | +0.21 | +0.23 | +0.20 | −0.20 | −0.04 |
| C entry speed | −0.56 [−0.67, −0.42] | −0.51 | −0.49 | −0.48 | +0.50 | −0.36 |
| R2 re-acceleration | +0.01 | +0.04 | −0.04 | −0.00 | +0.00 | +0.04 |
| R2 recovery time | +0.50 [0.37, 0.62] | +0.50 | +0.45 | +0.47 | −0.45 | **+0.39** |

**Adjusted R² from position, forty, three-cone and tracked peak speed:**
- C re-acceleration 0.17, almost all from position alone;
- C retention 0.01;
- C recovery time 0.12;
- R2 re-acceleration −0.01;
- R2 recovery time 0.24;
- C entry speed 0.32.

**Readings (associations only):**
- **C re-acceleration and C recovery time:** their pooled association with drill times and speed is between positions. Within position they are essentially unrelated to the three-cone, shuttle, forty, 10-yd split and peak speed (|ρ| ≤ 0.12). Their reliable variance (ICC about 0.6) is therefore *not* a re-expression of straight-line speed or drill time. Whether that variance reflects a useful athlete quality or turn-shape strategy cannot be decided from combine data.
- **C retention and R2 re-acceleration:** unrelated to every conventional measure, pooled or within position. For retention, this goes with low reliability and the strategy trade-off above.
- **R2 recovery time:** the only feature associated with drill time within position (ρ 0.39 with three-cone). It is also the least reliable and most processing-sensitive of the recovery features.
- **C entry speed:** largely approach speed. It tracks the forty and the three-cone and adds little.

## GO / NO-GO per feature

**What GO means here:** worth carrying forward on *measurement* grounds. It is not a recommendation to test against outcomes now (see below).

| feature | verdict | reason |
|---|---|---|
| **C re-acceleration** (slope 0–0.5 s after the loop minimum) | **CONDITIONAL GO** | Most reliable (0.64; within-position 0.60). Robust to every processing choice tested (ρ ≥ 0.89 vs reference). Not explained by speed or drill time within position. Conditions: report it with retention or minimum speed (turn-shape trade-off); use the mean of attempts with reliability carried forward; do not read it as a capacity |
| C retention (min / entry) | **NO-GO** | Low reliability (0.49, CI down to 0.13). Near-duplicate of minimum speed. Trades off against re-acceleration within athletes, so it is not interpretable as "better" |
| C recovery time to 90% | **NO-GO (processing-sensitive)** | ICC 0.44–0.67 depending on window and speed source; rank agreement 0.80 with vendor speed; 5% censored; depends on the entry-speed definition |
| C entry speed | NO-GO as a feature; keep as a covariate | Mostly approach speed (ρ −0.56 with three-cone; within-position ICC 0.44) |
| C minimum speed | NO-GO | Same construct as retention; ICC 0.56 |
| C duration / heading change | **NO-GO (detection artefact)** | C absorbs the B2 curve in 41% of attempts |
| R2 re-acceleration (from a near-stop) | **NO-GO (processing-sensitive)** | ICC 0.63 at reference but 0.17 at v_stop 0.75 and 0.49–0.50 at other re-acceleration windows; rank agreement 0.79 with vendor speed |
| R2 recovery time | **NO-GO** | ICC 0.43 (within-position 0.34); −0.06 at v_stop 0.75; rank agreement 0.47 with smoothed vendor speed |
| R1 recovery time | **NO-GO (not measurable)** | 90% censored: R2 starts before the athlete regains speed |
| R1 / R2 retention | **NO-GO (definitional)** | Touch reversals go to about 0.3 yd/s by design; retention ≈ 0.12 reflects the drill, not the athlete |
| B1 / B2 retention, recovery | **NO-GO (uninformative)** | No speed loss (retention ≈ 1); detected in only 70% / 34% of attempts |

## Does the sample support further research? Should anything go to outcome validation?

1. **Measurement research: marginally yes, for C re-acceleration only.**
   - The decisive limitation is repetitions, not detection: 34 test-retest athletes, 4–11 per position.
   - A position-specific reliability estimate, which CLAUDE.md requires before any within-position use, is not available for DB, OL, TE or WR.
2. **Outcome validation: not recommended now as a confirmatory test.**
   - Valid athletes with ≥ 100 REG play rows number 17 DB, 33 DL, 24 OL, 8 TE and 17 WR.
   - At n = 17–33, 80% power at α = 0.05 requires an observed correlation of about 0.50–0.67.
   - With single-attempt reliability of about 0.64, the observed correlation is attenuated by a factor of about 0.8.
   - Only an implausibly large true association would be detectable. The project's registered analyses already showed that players, not plays, limit power.
   - If the lead wants to proceed anyway, the defensible route is a **new pre-registration**: C re-acceleration only, one pre-specified outcome per position, estimation-only (no significance claim), reliability-corrected intervals, with C minimum speed reported alongside. Its Stage 1 definition and all thresholds must stay frozen as in this report.
3. **Not attempted, by instruction:** no feature has been linked to separation, pressure, get-off or any other NFL outcome.

## Limitations

- **Thresholds:** they were chosen from trajectory geometry on the same 203 attempts that are evaluated. There is no hold-out for the detection design. They were never tuned on reliability or outcomes, and the sensitivity grid shows how much each one matters.
- **Repeat attempts:** these may not be random. Athletes who repeat the drill may have had a poor or invalid first attempt. Mean differences between attempts are near zero, but selection cannot be excluded.
- **Sensor placement:** the sensor path stops short of the cones because athletes touch with the hand. Path geometry around the cones is not the foot path.
- **Sampling rate:** at 10 Hz the speed minimum is resolved to ±0.1 s. Re-acceleration over 0.5 s uses only 6 frames.
- **Mean summaries:** the per-player mean mixes athletes with 1, 2 and 3 attempts, so measurement precision is unequal across athletes.
