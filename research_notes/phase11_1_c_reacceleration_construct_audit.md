# Phase 11.1: construct audit of C re-acceleration (combine data only)

**Run:** `20261124T142408Z`, produced by `scripts/run_c_reacc_construct_audit.py`. Settings: seed 1111; B = 2000 bootstrap resamples for the reference configuration and 500 for the speed-source and smoothing variants.

**Code:**
- `src/nfl_bdb/features/turn_reacc_audit.py`: window audit, candidate B, turning diagnostics;
- `tests/test_turn_reacc_audit.py`: 8 tests;
- full suite 65/65 passing, including the code-freeze test.

**Outputs (git-ignored):**
- `data/interim/phase11_1_c_reacc/<run>/{c_turns,athlete_selection}.parquet` (player-level);
- `experiments/phase11_1_c_reacc/<run>/` (aggregate tables, `summary.json`).

**Scope:**
- **Inputs:** only `combine_tracking.parquet` (three-cone rows) and `combine_results.parquet`.
- **Game data:** no game table, outcome table or confirmatory-join file was opened. Unlike Stage 1, not even a REG play count was computed.
- **Stage 1 unchanged:** the detector, its thresholds and the candidate A definition are the Stage 1 code, untouched. The runner asserts that candidate A equals the Stage 1 `reacc` value for every turn in every configuration.
- **Preserved:** the Stage 1 report and results are unchanged, and no registered analysis or frozen file was modified.
- **Selection:** nothing was chosen by its relationship to NFL outcomes.

## Bottom line

**The current feature (candidate A) does not measure acceleration *after* the turn.**
- Its 0.5-s window lies **entirely inside the detected C turning segment in 117 of 193 attempts (61%)** and partly inside in the other 76. It lies wholly after the turn in **none**.
- During that window the athlete is still turning at a median of **184°/s**, through **≈110° of heading change**.
- A median **56% of the squared acceleration is centripetal** (direction change), not tangential (speed change).
- Candidate A is almost a mirror image of that split: ρ = −0.86 across attempts and **−0.94 within athletes** (attempt-2 − attempt-1 differences).

**What candidate A really measures:** speed gained while completing the second half of the loop. It is repeatable (ICC 0.64), but it is bound up with how tightly the athlete turns.

**Candidate B (slope after the detected exit) fails as a measure of the same thing:**
- It is unreliable: ICC 0.34 [−0.02, 0.64].
- It is missing for 21% of attempts.
- It measures a different phase of the drill depending on whether the B2 curve is detected separately.
- Even after the exit the athlete is still curving (median 48°/s, 29° over the window). The three-cone drill has **no straight post-turn acceleration phase** between C and the finish.

**Recommendation:**

| measure | verdict |
|---|---|
| Candidate A as "acceleration out of the turn" | **NO-GO** |
| Candidate A relabelled "late-loop speed gain" (a measurement, not an outcome predictor) | **CONDITIONAL GO**, for further measurement work only |
| Candidate B | **NO-GO** |
| Outcome validation of a re-acceleration construct from this drill | **Not supported** |

## 1. Operational definitions

All definitions use the Stage 1 reference parameters:
- SG window 7, order 2;
- speed from the SG derivative of x and y;
- turning frame: |ω| ≥ 60°/s or speed < 1 yd/s;
- merge gap 2;
- chord ≥ 45°;
- C = first ≥ 90° turn after R2 (with optional B1).

**Frame indices:**
- `start`, `end`: first and last frames of the detected C turning segment (inclusive);
- `i_min`: frame of minimum speed within [start − 1, end + 1];
- `next_start`: start frame of the next detected turn (B2), or the recording length *n* if none.

**Candidate A, post-minimum speed slope (Stage 1, unchanged):**
- the OLS slope of speed on time over frames `i_min … min(i_min + 5, next_start − 1, n − 1)`, requiring ≥ 3 frames;
- in all 193 attempts the window has the full 6 frames (0.5 s).

**Candidate B, post-turn-exit speed slope (diagnostic only; candidate A is not replaced):**
- the OLS slope over frames `end + 1 … end + 6`;
- usable only if all 6 frames exist (`end + 6 ≤ n − 1`) and the window ends before the next turn starts (`end + 6 < next_start`);
- same speed series and same number of frames as a full A window.

**Window diagnostics (both windows):**

| diagnostic | definition |
|---|---|
| overlap with [start, end] | inside / partial / after |
| mean \|ω\| | mean absolute heading rate over the window |
| share of turning frames | share of frames with \|ω\| ≥ 60°/s (the Stage 1 turning rule) |
| heading change | \|Σω\|·Δt over the window |
| centripetal share | Σ(v·ω)² / Σ[(v·ω)² + (dv/dt)²] |

**B2 status (per attempt):**

| status | rule | attempts |
|---|---|---|
| B2 detected | a separate 45–90° turn after C | 66 |
| B2 absorbed | no B2 and C chord < 135° (the B curve is merged into the C segment) | 79 |
| no B2, C ≥ 135° | the curve is not separated and C ends near 160–180° | 48 |

## 2. Window-overlap audit (Task A)

| | all | B2 absorbed | B2 detected | no B2, C ≥ 135° |
|---|---|---|---|---|
| attempts / athletes | 193 / 155 | 79 / 69 | 66 / 64 | 48 / 41 |
| A window **entirely inside** C | **117** | **79** | 12 | 26 |
| A window partly inside | 76 | 0 | 54 | 22 |
| A window entirely after C | **0** | 0 | 0 | 0 |
| share of A frames inside C (median) | 1.00 | 1.00 | 0.83 | 1.00 |
| frames from minimum to C exit (median, range) | 6 (1–18) | 15 (13–18) | 4 (1–6) | — |
| A window: mean \|ω\| (median, °/s) | 184 | 182 | 187 | 181 |
| A window: share of frames with \|ω\| ≥ 60°/s (median) | 1.00 | 1.00 | 0.83 | 1.00 |
| A window: heading change (median) | 110° | 109° | 112° | 108° |
| A window: centripetal share of squared acceleration (median) | 0.56 | 0.64 | 0.46 | 0.53 |

**Robustness:** the same picture holds under every speed-source and smoothing variant. Windows entirely inside C number 106–122 per configuration; none is ever wholly after C.

**Reading:** the speed minimum sits at the apex of the loop, roughly halfway through the 160–180° reversal. The 0.5 s that follows is the second half of the loop, so candidate A's window is turning time by construction, not post-turn time.
- When B2 is detected, C's turning frames end about 0.4 s after the minimum. The last 1–3 frames of the A window then fall on the short run between C and the B curve.
- When B2 is absorbed, the athlete keeps turning above 60°/s for 1.3–1.8 s after the minimum, all the way round cone B.

**Conclusion for Task A: candidate A does not measure acceleration after exiting the turning movement.** It measures speed gain during the late loop. Part of the athlete's acceleration in that window is spent changing direction, and that part does not appear in the speed slope.

## 3. Candidate A vs candidate B (Task B)

**Method:** first two usable attempts per athlete in chronological order. ICC(3,1) is consistency; ICC(2,1) is absolute agreement; typical error (TE) = SD(diff)/√2. Within-position values use attempts centred on the position mean. Player-bootstrap 95% CIs.

| | candidate A | candidate A on B's attempts | candidate B |
|---|---|---|---|
| usable attempts / athletes | 193 / 155 | 153 / 123 | 153 / 123 |
| athletes with 2 usable attempts | 34 | 26 | 26 |
| mean (SD), yd/s² | 4.57 (0.88) | 4.47 (0.92) | 2.39 (0.91) |
| 5th / 50th / 95th percentile | 3.25 / 4.55 / 6.05 | 3.21 / 4.35 / 6.31 | 1.07 / 2.21 / 4.17 |
| ICC(3,1) [95% CI] | **0.64 [0.42, 0.81]** | 0.65 [0.36, 0.84] | **0.34 [−0.02, 0.64]** |
| ICC(2,1) [95% CI] | 0.65 [0.42, 0.81] | 0.65 [0.35, 0.84] | 0.35 [−0.02, 0.64] |
| Spearman [95% CI] | 0.61 [0.31, 0.81] | 0.62 [0.24, 0.84] | 0.41 [0.03, 0.71] |
| typical error (% of mean) | 0.57 (12%) | 0.59 (13%) | 0.83 (35%) |
| within-position ICC(3,1) | 0.60 | 0.61 | 0.29 |

**Why B is missing:** 38 of 66 attempts with B2 detected, because B2 starts within 0.6 s of C's exit; and 2 attempts, because the recording ends.

**Agreement between A and B:** ρ = 0.61 across 153 attempts. This is driven by the attempts where B2 is detected (0.78) or C ≥ 135° (0.69). Where B2 is absorbed, ρ is only **0.19**: there B is measured after cone B, at a median exit speed of 5.5 yd/s, compared with 2.7–3.3 in the other groups.

**Sensitivity to speed source and smoothing:**

| configuration | ICC A | ICC B | rank agreement of player means with reference, A | same, B |
|---|---|---|---|---|
| reference (pos, w = 7) | 0.64 | 0.34 | 1 | 1 |
| SG window 5 | 0.57 | 0.31 | 0.97 | 0.96 |
| SG window 9 | 0.66 | 0.46 | 0.97 | 0.97 |
| SG window 11 | 0.68 | 0.48 | 0.96 | 0.93 |
| provided speed | 0.61 | 0.31 | 0.92 | 0.95 |
| SG-smoothed provided speed | 0.60 | 0.32 | 0.89 | 0.95 |

**Reading the comparison:**
- **Candidate A** is processing-robust.
- **Candidate B** is low in every configuration. Its best value (0.48 at window 11) still has a lower CI bound near 0.15.
- **Same sample:** A's advantage is not a sample artefact; on B's own 26 pairs, A still has ICC 0.65.
- **Validity:** as instructed, a higher ICC is not read as evidence of validity. It shows that A repeats, not what A measures.

## 4. Results by B2 detection status

| | candidate A | candidate B |
|---|---|---|
| mean when B2 absorbed / detected / no B2, C ≥ 135° | 4.11 / 5.15 / 4.55 | 1.96 / 3.33 / 2.52 |
| ICC, B2-absorbed attempts only (10 / 9 pairs) | 0.53 [−0.19, 0.93] | 0.11 [−0.25, 0.39] |
| ICC, pairs with no B2 in either attempt (23 / 22 pairs) | 0.53 [0.21, 0.79] | 0.14 [−0.13, 0.48] |
| ICC, pairs with B2 in both attempts | 2 pairs, not estimable | 1 pair |

**Is B2 status consistent within athletes?** Across the 34 athletes' first two attempts:
- both with B2: 2;
- neither: 23;
- **mixed: 9**.

So the segmentation state, and with it the phase that candidate B measures, changes between an athlete's attempts.

**Pooled reliability and segmentation:** both candidates lose reliability within a status stratum (A 0.64 → 0.53). Part of A's pooled ICC therefore comes from athletes who repeatedly produce the same turn shape and segmentation state, which is itself a turn-shape trait.

**Precision:** the stratified estimates are imprecise and should not be over-read.

## 5. Speed and turn-shape dependence (Task C)

**Method:** Spearman correlations at attempt level, pooled and within position (position-centred ranks), and between within-athlete differences of the first two usable attempts (n = 34 for A, 26 for B). Associations only; none is causal.

| covariate | A, attempts | A, within position | **A, within athlete Δ** | B, attempts | B, within athlete Δ |
|---|---|---|---|---|---|
| C minimum speed | −0.70 | −0.74 | **−0.72** | −0.67 | −0.52 |
| C entry speed | +0.37 | +0.24 | +0.27 | +0.12 | +0.29 |
| C retention | −0.77 | −0.79 | **−0.72** | −0.69 | −0.44 |
| C duration † | −0.67 | −0.66 | −0.43 | −0.66 | −0.57 |
| C chord † | +0.46 | +0.45 | −0.12 | +0.50 | +0.17 |
| C cumulative heading † | −0.50 | −0.53 | −0.27 | −0.54 | −0.39 |
| speed at C exit | −0.42 | −0.51 | −0.18 | −0.48 | −0.12 |
| frames from minimum to exit | −0.64 | −0.64 | −0.38 | −0.65 | −0.59 |
| share of A window inside C | −0.67 | −0.68 | −0.67 | −0.75 | −0.62 |
| A window mean \|ω\| | +0.23 | +0.18 | +0.13 | +0.22 | +0.42 |
| **A window centripetal share** | **−0.86** | **−0.88** | **−0.94** | −0.70 | −0.51 |

† These are affected by C absorbing B2 (Stage 1 limitation): duration and chord partly encode segmentation status, not turn geometry alone.

**What remains after removing the start speed or turn shape?** Each row is a pooled attempt-level OLS with position dummies; the residual is then put through the same test-retest analysis.

| residual of | removed | R² | residual ICC(3,1) [95% CI] |
|---|---|---|---|
| A | C minimum speed | 0.61 | 0.59 [0.44, 0.73] |
| A | C retention | 0.66 | 0.57 [0.40, 0.69] |
| A | A-window centripetal share | 0.82 | 0.68 [0.44, 0.81] |
| B | speed at C exit | 0.39 | 0.17 [−0.13, 0.46] |
| B | C minimum speed | 0.45 | 0.23 [−0.05, 0.50] |

**Test-retest of the covariates themselves:**
- minimum speed 0.56;
- exit speed 0.51 (systematic +0.63 yd/s shift between attempts);
- centripetal share 0.57;
- A-window mean |ω| **0.00**, so the turning *rate* is not an athlete trait.

**Interpretation:**

1. **Candidate A mostly reflects turn strategy.** It falls when the minimum is higher (a wider, rounder loop: ρ −0.72 within athletes) and is almost the mirror image of the centripetal share in its own window (−0.94 within athletes).
   - When an athlete takes a tighter apex, more of the late-loop acceleration shows up as speed gain.
   - When the athlete carries more speed round a wider arc, more goes into direction change.
   - This is the Stage 1 retention ↔ re-acceleration trade-off, now located: it is happening inside the turn.
2. **A is not a re-expression of entry speed** (ρ +0.27 within athletes).
3. **A repeatable component remains after removing the start speed or the centripetal share** (residual ICC 0.57–0.68). It is attempt-level, measured on 34 athletes, and its content is unknown. It could be a distinct speed-change ability, or a stable individual turn geometry (for example a consistent apex radius) that the 10-Hz path and the 60°/s rule cannot resolve. These data cannot distinguish the two.
4. **Candidate B mostly reflects where its window lands.** That depends on B2 segmentation and exit speed (5.5 yd/s if B2 was absorbed). After removing exit or minimum speed, almost nothing repeatable remains (ICC 0.17–0.23).

**Turning after the exit is real, not a smoothing artefact.** On a synthetic turn that ends abruptly, the SG window-7 tail leaves about 8° of heading change and a mean |ω| of about 13°/s in the B window (unit test). The real data show 29° and 48°/s.

## 6. Repeat-attempt selection audit (Task D)

**Groups:** 34 athletes with ≥ 2 valid attempts ("repeaters") vs 121 with one valid attempt ("single").
- Of the single group, 4 have extra raw attempts that failed the template.
- In 3 athletes the first valid attempt was not the first recorded.

| variable | repeaters: median (missing) | single: median (missing) | Mann–Whitney p | within-position z, repeaters vs single (p) |
|---|---|---|---|---|
| position | DB 7, DL 11, OL 7, TE 5, WR 4 | DB 17, DL 34, OL 37, TE 14, WR 19 | χ² p 0.68 | — |
| draft year | 2023: 11, 2024: 11, 2025: 12 | 34 / 47 / 40 | — | — |
| official three-cone (s) | 7.12 (6%) | 7.30 (7%) | 0.07 | −0.25 vs +0.07 (0.08) |
| short shuttle (s) | 4.35 (6%) | 4.46 (14%) | 0.06 | **−0.30 vs +0.09 (0.03)** |
| forty (s) | 4.69 (12%) | 4.78 (10%) | 0.23 | −0.24 vs +0.07 (0.12) |
| 10-yd split (s) | 1.65 (12%) | 1.68 (10%) | 0.23 | −0.29 vs +0.08 (0.08) |
| first-attempt candidate A | 4.48 | 4.55 | 0.63 | −0.10 vs +0.03 (0.66) |
| first-attempt candidate B | 2.21 (9% missing) | 2.18 (26% missing) | 0.91 | −0.04 vs +0.01 (0.92) |
| first-attempt C entry / minimum speed / retention | 4.18 / 0.90 / 0.22 | 4.08 / 0.91 / 0.22 | 0.66 / 0.33 / 0.29 | n.s. |
| **first attempt has B2 detected** | **21% (7/34)** | **44% (53/121)** | **Fisher p 0.017** | — |

**Observable differences:**
- **Faster athletes:** within position, repeaters were about 0.3 SD faster on the official agility and sprint measures. All four point the same way; shuttle p = 0.03, the others 0.07–0.12, with no multiplicity correction.
- **Turn shape:** repeaters' first attempts less often produced a separate B2 (21% vs 44%), so their turn shapes differ from non-repeaters'.
- **Similar first-attempt features:** candidate A, B, entry speed, minimum speed and retention on the first attempt do not differ detectably.
- **Missingness:** candidate B is missing more often for single-attempt athletes (26% vs 9%), which follows from the B2 difference.

**Implication:** the 34-athlete reliability estimates come from a non-random, somewhat faster subgroup with different turn segmentation. **They should not be assumed to hold for all athletes.** Why some athletes ran the drill twice is not recorded in the data.

## 7. Limitations and unresolved questions

- **Small sample:** test-retest rests on 34 athletes (26 for B). Position-specific and segmentation-stratified reliabilities are not estimable or are very imprecise.
- **Dependence on Stage 1 segmentation:** "inside C" depends on the Stage 1 turning rule (|ω| ≥ 60°/s or speed < 1). The direct turning diagnostics (|ω|, heading change, centripetal share) do not depend on it and lead to the same conclusion.
- **Body path, not foot path:** the sensor path is a body trajectory, and athletes touch cones with the hand. Turn radius and apex cannot be measured precisely at 10 Hz.
- **Centripetal share** uses the SG heading rate and the speed derivative of the same smoothed series. Measurement error common to both could inflate its correlation with candidate A, so the −0.94 should be read as strong coupling, not as an exact identity.
- **No straight post-turn phase:** the three-cone drill offers no clean straight acceleration after C. Any "post-turn" window is still curving toward or around cone B, or falls in the final sprint.
- **The residual repeatable component of A** (ICC about 0.6 after removing minimum speed or centripetal share) has no identified meaning. Whether it is an ability or a stable turn geometry cannot be decided from combine data.
- **Repeat attempts** are a selected subgroup (Section 6).
- **Unresolved:**
  - Would a curvature-aware quantity, for example the magnitude of the total acceleration vector along the late loop, be more interpretable than the speed slope? That would be a new definition and needs separate approval.
  - Would a drill with a straight exit, such as the 5-10-5, isolate post-turn acceleration better? This was not examined.

## 8. Recommendation

| measurement | decision | basis |
|---|---|---|
| **Candidate A as "re-acceleration out of the turn"** | **NO-GO** | The window is never after the turn: 61% wholly inside C, the rest partly; about 110° of heading change at about 184°/s within it. The construct label is not supported |
| **Candidate A relabelled "late-loop speed gain"** (Stage 1 definition unchanged) | **CONDITIONAL GO for further measurement work only** | Repeatable (0.64 [0.42, 0.81]) and processing-robust (rank ≥ 0.89). Conditions: always report it with C minimum speed and the A-window centripetal share; describe it as a turn-shape-dependent quantity, not an acceleration capacity; acknowledge the non-representative repeat sample; never use it as a capacity limit |
| **Candidate B (post-exit slope)** | **NO-GO** | ICC 0.34 [−0.02, 0.64], TE 35%. Missing in 21% of attempts. Measures different drill phases depending on B2 segmentation (A–B ρ 0.19 when B2 is absorbed). No repeatable component beyond exit or minimum speed |
| **Proceeding to NFL outcome validation of a C re-acceleration construct** | **NO-GO at this time** | The measured quantity is not the intended construct. Its repeatable variance is entangled with turn shape. Reliability is estimated on 34 non-random athletes. Any outcome study would first need a new, approved construct definition and pre-registration |

No outcome validation has been started.
