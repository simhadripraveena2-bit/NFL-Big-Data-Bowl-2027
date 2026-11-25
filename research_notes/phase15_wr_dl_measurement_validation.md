# Phase 15: deep measurement validation of WR route-drill movement and DL pass-rush arc bend

**Scope:**
- **Measurement only.** No NFL game or outcome table was opened, nothing was joined to any NFL performance measure, no predictive model was fitted, and no feature was chosen by any outcome.
- **Combine data only.** Inputs are Combine tracking, `combine_results`, and the registered combine-only tracked-40 peak speed (`predictors.parquet`, columns `nfl_id`, `x_peak`, `valid_tracked_40` only).
- **Nothing earlier changed.** Phases 11–14, the registered analyses and the frozen files are unchanged.
- **Output location:** player- and attempt-level outputs are under the git-ignored `data/interim/phase15/`; aggregates are under `experiments/phase15/`.

**Runs:**

| run | id |
|---|---|
| WR | `20261125T021311Z` (`scripts/run_phase15_wr_gstudy.py`, supplement `scripts/run_phase15_wr_supplement.py`) |
| DL | `dl_20261125T021641Z` (`scripts/run_phase15_dl_arc.py`) |
| synthetic arcs | `arc_dev_20261125T021428Z` and `arc_holdout_20261125T021509Z` (`scripts/run_phase15_arc_synthetic.py`) |

**Code and tests:**
- `src/nfl_bdb/features/phase15_measures.py`: SG gain, arc geometry, G-study.
- `src/nfl_bdb/simulation/arc_synth.py`: synthetic arc generator.
- **Correction decision:** made on dev data only and committed in `d0a4665` before the held-out run (`configs/phase15_arc_correction_decision.json`).
- **Tests:** `tests/test_phase15_measures.py` (8). The full suite passes 95/95, including the code-freeze test.

## 1. Research questions

1. **WR routes:** do route-drill movement measures (peak speed, mean speed, tangential and centripetal acceleration, braking) characterise athletes stably across the ~12 different routes, across draft years, and across processing choices? Is "route speed" anything more than straight-line sprint speed?
2. **DL pass rush:** is the arc in the pass-rush drill a measurable "bend" characteristic once speed is separated from curvature, smoothing bias is quantified, and the two attempts are recognised for what they are?

## 2. Exact feature definitions

**Common processing:**
- Positions are smoothed with Savitzky–Golay (order 2), window 7 by reference, with 5 and 9 as sensitivity windows. Velocity comes from the SG derivative.
- Speed is |v|, heading rate ω is the derivative of the unwrapped heading, tangential acceleration is a_t = d|v|/dt, and centripetal acceleration is a_n = |v|·|ω|.
- The vendor `a` and `dis` channels are never used.

### WR (per route attempt)

Valid attempts need ≥ 20 frames; all 1,286 attempts qualify.

| feature | definition | notes |
|---|---|---|
| peak speed | max \|v\| | **Truncation rule** (physical validity, stated before use): a peak in the last 3 frames means the recording ended mid-acceleration, so it is invalid. Routes where > 50% of peaks are invalid (SLANT 85–97%, SLOT_STRIKE 73–84%) are excluded from all peak analyses |
| mean moving speed | mean \|v\| over frames ≥ 1 yd/s | |
| tangential acceleration p95 | 95th percentile of a_t | **73% of the top-5% frames fall in the first second**: this is mainly the launch from the stance. SLOT_STRIKE is the exception (re-acceleration after its 160° stop) |
| centripetal acceleration p95 | 95th percentile of a_n over frames ≥ 2 yd/s | |
| braking p05 (diagnostic) | 5th percentile of a_t | |
| speed expression | route peak ÷ tracked-40 peak, and log(route peak) − log(tracked-40 peak) | a **speed-expression measurement**, not a capacity |

**Route identity:**
- The original drill name is used. SPEED_OUT_LEFT (2024) was borderline in Phase 14's geometry audit (minor-extent ratio 1.15 against the 15% rule), so it is **kept as its own route**; merging it is a sensitivity analysis only.
- POST_CORNER_LEFT and POST_CORNER_RIGHT are different routes.
- CIRCUS (2025 only) and GAUNTLET are excluded.

**Route-specific differences:** each route × draft-year cell is a fixed effect, so athlete scores are relative to the cell mean. A cell-standardised (z-score) version is a sensitivity analysis.

### DL (per pass-rush attempt)

**Turning frames:** speed ≥ 2 yd/s and |ω| ≥ **25°/s**. The 25°/s threshold was fixed from geometry before any agreement statistic: the 99th percentile of |ω| on straight-sprint frames is 23°/s.

**The arc:**
- Turning-frame runs separated by ≤ 2 frames are merged, which bridges brief straight segments.
- The arc is the run with the largest absolute heading change.
- It is valid if it has ≥ 5 frames, ≥ 30° of heading change, and does not touch the start or end of the recording.
- Side = sign of the heading change (left or right).

**Medians over the arc frames:**
- speed (with the adopted SG correction, §5.2);
- heading rate;
- curvature κ = |ω|/v;
- radius 1/κ;
- a_n.

**Common-speed curvature:**
- Median κ over arc frames whose corrected speed lies inside **[3.95, 5.00] yd/s**, the interquartile range of the pooled arc-frame speeds (3,690 frames). The band was fixed before any agreement statistic.
- At least 3 frames in the band are required. No extrapolation is used.

**Sensitivity grid:** window 5 or 9; ω threshold 20 or 30°/s; merge gap 1 or 3 frames.

## 3. Data coverage

### 3.1 WR routes (A1)

**Athletes and routes:**
- **107 WR** (all Combine WR with route drills) contributed 1,286 valid attempts.
- 102 athlete × route cells contain a repeat attempt.
- Routes per athlete: 12 for 52 athletes, 11 for 37, 10 for 8, 9 for 4, ≤ 7 for 6.
- 24 distinct route sets appear.
- **Route availability differs by year:**
  - POST_CORNER_LEFT exists only in 2023–24;
  - the 2024 speed-out is the borderline SPEED_OUT_LEFT;
  - **2025 athletes have at most 11 routes**, with no POST_CORNER_LEFT.
- Per route × year: 28–39 athletes and 28–46 attempts. Median frames range from 28 (2025 SLANT, shorter recordings) to 77.

**Truncation:**
- Recordings start from rest (start-moving share 0–24%) and **end in motion in 95–100%**.
- Peak in the last 3 frames: SLANT 0.85–0.97, SLOT_STRIKE 0.73–0.84, CURL 0.26–0.44, DAGGER 0.19–0.44, SLOT_SAIL 0.21–0.40, all others ≤ 0.11.

**Tracked-40 peak available:** 94 of 107 WR.

### 3.2 DL pass-rush drill (B1)

**Attempts:** 217 attempts by 114 athletes (1 attempt: 12; 2: 101; 3: 1). All 217 have a valid geometric arc.

**Sides:** left 107, right 110.

**What the two attempts are:**
- **101 of 102 two-attempt athletes ran one left and one right arc.** Only 1 repeated the same side (right).
- **So the two attempts are mirrored sides, not repeats. No test-retest reliability can be estimated.**
- **Side is confounded with order:** the first attempt was a right-side arc for 109 of 114 athletes.
- The pattern is the same every year (2023: 28 left/right pairs, 2024: 30, 2025: 43 plus 1 same-side pair).

**Arc geometry** (medians, 5th–95th percentile):

| quantity | value |
|---|---|
| frames | 16 (13–21) |
| heading change | 83° (69–114) |
| corrected speed | 4.31 yd/s (3.81–4.95) |
| heading rate | 51.6°/s |
| curvature | 0.208 /yd (radius 4.82 yd) |
| a_n | 4.05 yd/s² (3.47–4.68) |

**Common speed band:** 216 of 217 arcs have ≥ 3 frames in it; 165 span the whole band.

**Speed and curvature are strongly coupled across attempts:**
- speed vs curvature ρ = −0.71 (faster runners take wider arcs);
- speed vs a_n +0.53;
- curvature vs a_n −0.14.

## 4. WR generalizability study (A3–A5)

### 4.1 Model

**REML linear mixed model** (statsmodels MixedLM), fitted to all valid attempts:

  y = route × year cell (fixed) + athlete + athlete × route + residual

**What each term captures:**
- **Residual:** within-athlete, within-route variation, identified from the 102 repeat cells.
- **Route × year cells:** fixed. Route and year main effects and their interaction are absorbed, so scores are relative to the cell. The route-universe main effect therefore does not enter the error, which makes these relative (δ-type) coefficients.

**Assumptions:**
- random effects are normal and independent;
- the interaction and residual variances are the same for every route (homoscedasticity);
- repeat attempts are representative. They may be re-runs after poor attempts; with one attempt per route the G-coefficient depends only on the sum of interaction and residual, so this split does not change G.

**Generalizability of an athlete's mean over n routes:**

  G(n) = σ²_athlete / (σ²_athlete + (σ²_athlete×route + σ²_residual)/n)

- **Range:** n = 1 to 12, within the observed route universe only.
- **CIs:** athlete-cluster bootstrap, 200 resamples.
- **Cell-standardised version:** each attempt is z-scored within its route × year cell, so every route carries equal weight. This addresses the heteroscedasticity across routes.

### 4.2 Results (window 7)

| feature | σ² athlete : athlete×route : residual | G(4) | G(6) | G(8) | G(10) [95% CI] | G(12) |
|---|---|---|---|---|---|---|
| peak speed, all routes | 0.010 : 0.063 : 0.136 | 0.16 | 0.23 | 0.28 | 0.33 [0.08, 0.47] | 0.37 |
| **peak speed, truncation-valid** (10 routes) | 0.010 : 0.031 : 0.125 | 0.21 | 0.28 | 0.35 | **0.40 [0.06, 0.55]** | 0.44 |
| peak speed, truncation-valid, cell z | 0.109 : 0.276 : 0.613 | 0.33 | 0.42 | 0.49 | 0.55 [0.42, 0.65] | 0.59 |
| mean moving speed | 0.004 : 0.020 : 0.140 | 0.10 | 0.14 | 0.17 | 0.21 [0.00, 0.45] | 0.24 |
| mean moving speed, cell z | — | 0.13 | 0.18 | 0.23 | 0.27 [0.05, 0.43] | 0.31 |
| **tangential acceleration p95** | 0.017 : 0.064 : 0.076 | 0.33 | 0.42 | 0.50 | **0.55 [0.36, 0.68]** | 0.60 |
| **tangential acceleration p95, cell z** | 0.168 : 0.289 : 0.551 | 0.44 | 0.55 | 0.62 | **0.67 [0.56, 0.75]** | 0.71 |
| centripetal acceleration p95 | 0.028 : 0.024 : 0.515 | 0.17 | 0.24 | 0.29 | 0.34 [0.06, 0.49] | 0.38 |
| centripetal acceleration p95, cell z | 0.082 : 0.000 : 0.917 | 0.26 | 0.35 | 0.42 | 0.47 [0.31, 0.63] | 0.52 |
| braking p05 (diagnostic) | 0.003 : 0.009 : 0.832 | 0.02 | 0.02 | 0.03 | 0.04 [0.00, 0.23] | 0.05 |

**Between-athlete SDs are small:**
- raw peak speed: about 0.10 yd/s, against a within-athlete SD per route of about 0.4 yd/s;
- launch acceleration: 0.13 yd/s².

### 4.3 Stability

| check | peak speed (valid) | tangential acc. p95 (raw / z) | centripetal acc. p95 | mean speed | braking |
|---|---|---|---|---|---|
| leave-one-route-out G(10) | **0.07–0.52**; dropping COMEBACK gives 0.08 | **0.51–0.63 / 0.64–0.70** | 0.29–0.41 | 0.11–0.23 | 0.00–0.15 |
| within year G(10), 2023 / 2024 / 2025 (raw, all routes) | 0.21 / 0.23 / 0.47 | 0.60 / 0.62 / **0.35** | 0.63 / 0.50 / 0.21 | 0.18 / 0.30 / 0.16 | ≤ 0.25 |
| SG window 5 / 9, G(10) | 0.32 / 0.32 (all routes) | 0.54 / 0.55 | 0.35 / 0.34 | 0.20 / 0.20 | 0.00 / 0.08 |
| vendor speed `s` instead of SG | G(10) 0.34 | — | — | — | — |
| SPEED_OUT merged | unchanged (0.33) | unchanged | unchanged | unchanged | — |

**Empirical check with disjoint random route subsets** (cell-centred, raw scale):
- **Peak speed:** 2-route vs 2-route r = 0.13; 6 vs 6 r = 0.22 [0.05, 0.41]. This is consistent with the model's G(6) = 0.23 on all routes.
- **Launch acceleration:** short-route vs long-route mean r = 0.51.

### 4.4 Speed expression vs sprint capacity (A4)

**Size of the gap:**
- Route peak speed is a median **73%** of the athlete's tracked-40 peak (5th–95th percentile 57–91%).
- At athlete level, route peak (cell-centred) correlates only **ρ 0.12–0.17** with the tracked-40 peak.

**The expression measures look generalizable:**
- log(route peak) − log(tracked-40 peak): G(10) = 0.71 [0.59, 0.80], stable across years (0.65 each) and leave-one-out (0.63–0.69).
- The ratio behaves the same way: G(10) = 0.69.

**But that is mostly the denominator:**
- **59% of the athlete-level variance of the log-difference is the log tracked-40 peak itself.** The log-difference correlates −0.68 with log tracked-40 peak and +0.65 with the route part.
- Dividing a weakly generalizable route score by a highly reliable athlete constant manufactures generalizability.
- **The route component itself has the generalizability of raw peak speed (G(10) ≈ 0.40).**

### 4.5 WR interpretation

- **Generalizable, robust and stable: tangential acceleration p95.** It is stable across routes, windows and leave-one-route-out. But it is mostly the **launch from the stance at the start of each route**, measured about 12 times; it is not route-break skill. It is weaker for the 2025 cohort (0.35).
- **Not stable athlete characteristics:**
  - route peak speed and mean speed (dominated by route-specific and attempt variation; highly dependent on which routes are included);
  - centripetal acceleration (residual-dominated; 2025 G = 0.21);
  - braking.
- **"Route speed" carries little sprint capacity** (ρ ≈ 0.15 with the tracked-40 peak). It reflects how fast athletes choose, or are able, to run these drill routes, which is noisy from route to route.

## 5. DL arc geometry and smoothing study

### 5.1 Synthetic design (B4)

**Trajectories:**
- straight lead-in;
- curvature ramped linearly over 0.1–0.4 s to 1/R, with R between 2 and 5 yd;
- constant curvature until the heading change reaches 60–150°;
- ramp down, straight lead-out;
- speed v₀ between 3 and 5 yd/s with tangential acceleration 0–2 yd/s²;
- left or right direction, random rotation and random 10 Hz sampling phase.

**Noise scenarios:** none; the 1/30-yd grid with 0.002 yd jitter (2023–24); Gaussian 0.002 or 0.005 yd.

**Windows:** 5, 7, 9.

**Seeds:** dev 101–103 and held-out 2001–2003, 900 arcs each.

**Truth:** true values at the frames the detector selected. A second truth (the true R and the constant-curvature-part speed) adds the segmentation effect.

### 5.2 Speed correction (decided on dev, committed before held-out)

**Analytic gain:** for uniform circular motion the SG derivative returns v·g(ω), with g(ω) = |Σ c_k e^{iωkΔt}|/ω, and returns ω without bias. g depends only on the filter, so it is not fitted to data. Unit tests confirm it to 10⁻⁶.

**Pre-stated adoption rule:** at window 7, in every noise scenario, corrected |median error| ≤ 2% and corrected SD ≤ 1.2 × uncorrected SD.

**Dev decision:**
- **Adopt the correction for speed only.**
- Heading rate, curvature, radius and a_n failed the rule, so they are reported **uncorrected, with held-out error bounds**.

### 5.3 Held-out errors

Relative error at window 7 on the 2023–24 grid (quant30); other noise scenarios agree within 0.01.

| quantity | median error | SD | \|error\| 90th percentile |
|---|---|---|---|
| speed, uncorrected | −3.1% | 2.0% | — |
| **speed, corrected** | **0.0%** | **0.4%** | — |
| heading rate | **−8.6%** | 7.2% | — |
| curvature | −7.7% | 7.5% | — |
| radius | +8.4% | 9.8% | — |
| a_n | **−9.6%** | 7.0% | 21.5% |
| radius vs true R (includes segmentation) | +11.0% | 20.8% | — |

**Why curvature-type quantities resist correction:** on real arcs curvature is not constant, and smoothing spreads and flattens the heading-rate peak. The bias therefore does **not** follow the circular-motion formula.

**The bias depends on arc geometry**, which is not constant across athletes:

| geometry | a_n error | curvature error |
|---|---|---|
| R ≤ 3 yd | −16.5% | — |
| R > 4 yd | −5.9% | — |
| heading change ≤ 90° | — | −12.1% |
| heading change > 120° | — | −2.1% |

**Window dependence:** a_n error is −5.5% at window 5 and −15% at window 9.

**Geometry-dependent bias** distorts between-athlete comparisons; a constant offset would not.

**Not error sources:** sampling phase does not matter (bias identical across phase bins), and side detection is 100% correct.

## 6. Bilateral consistency (B5)

**Design:** first valid left vs first valid right arc, n = 102 athletes.

**These are agreement-between-sides statistics, not test-retest.** Side is also confounded with attempt order.

| measure | left mean | right mean | L − R [95% CI] | median \|asym\| | ICC(3,1) [95% CI] | year-centred | ICC(2,1) |
|---|---|---|---|---|---|---|---|
| **arc speed (corrected)** | 4.44 | 4.26 | **+0.17 [0.09, 0.25] yd/s** | 7.3% | **0.41 [0.28, 0.54]** | 0.36 | 0.38 |
| heading rate | 51.0°/s | 52.6°/s | −1.7 [−2.8, −0.5] | 8.7% | 0.19 [−0.01, 0.37] | 0.17 | 0.18 |
| curvature | 0.206 | 0.217 | −0.011 [−0.018, −0.004] | 8.8% | 0.25 [0.09, 0.45] | 0.19 | 0.24 |
| radius | 4.93 | 4.70 | +0.23 [0.09, 0.37] yd | 8.9% | 0.31 [0.16, 0.46] | 0.26 | 0.30 |
| **a_n** | 4.05 | 4.09 | −0.04 [−0.13, 0.06] | 8.6% | **0.17 [−0.02, 0.34]** | 0.14 | 0.17 |
| curvature in common speed band | 0.238 | 0.245 | −0.007 [−0.015, 0.001] | 11.2% | 0.22 [0.03, 0.39] | 0.17 | 0.21 |
| heading change | 90° | 84° | +6.7° [3.3, 10.2] | 10.9% | 0.32 [0.14, 0.50] | 0.29 | 0.29 |

**Systematic side (or order) effects:**
- The left (mostly second) arc is faster, wider and longer.
- So agreement on absolute values (ICC(2,1)) sits below consistency (ICC(3,1)).

**By draft year:**
- a_n ICC(3,1): 0.33 / 0.11 / 0.10 (2023 / 2024 / 2025);
- curvature: 0.07 / 0.38 / 0.12;
- speed: 0.62 / 0.29 / 0.31.

**By body-weight half** (a proxy only; role is not in the Combine data):
- a_n: 0.04 (lighter) / 0.24 (heavier);
- speed: 0.46 / 0.35.

**Sensitivity grid** (windows 5/9; ω threshold 20/30; merge gap 1/3):
- a_n 0.13–0.23;
- curvature 0.20–0.29;
- radius 0.25–0.35;
- speed 0.40–0.43.

**How much of the observed variation is measurement error?** Compare the synthetic error SD with the observed between-attempt CV:

| quantity | synthetic error SD | observed CV | implied ceiling on single-side reliability |
|---|---|---|---|
| a_n | 7.0% | 9.6% | ≤ 0.47 overall (≤ 0.82 for wide arcs, R > 4 yd) |
| curvature | 7.5% | 14.2% | ≤ 0.72 (≤ 0.83 for wide arcs) |
| radius | 9.8% | 13.1% | ≤ 0.44 |
| heading rate | 7.2% | 9.3% | ≤ 0.40 |
| speed (corrected) | 0.4% | 9.0% | ≈ 1 |

**Is pooling the two sides justified?**
- **Speed:** the sides agree moderately, and the bilateral average would have Spearman–Brown 0.58 *if* the sides were parallel measures, which the order and side shift contradicts.
- **Bend quantities:** side agreement of 0.14–0.31 with about 9% median asymmetry does **not** justify treating the bilateral average as a stable athlete trait.
- **Phase 14's "test-retest" ICC of 0.49 for a_n** was left/right agreement under a different definition (|ω| ≥ 60°/s frames only). The geometric arc fixed here, before any agreement statistic, gives 0.17.

## 7. Synthetic validation summary

| claim | evidence |
|---|---|
| The SG speed attenuation on curves is analytic and correctable | unit tests (10⁻⁶); held-out corrected speed error 0.0% ± 0.4% |
| Heading-rate, curvature, radius and a_n errors are not correctable by the circular-motion formula | held-out a_n −9.6% ± 7.0%, curvature −7.7% ± 7.5%; geometry-dependent (R, heading change) and window-dependent |
| Combine coordinate precision is not the limiting factor | none / quant30 / Gaussian scenarios within 1% of each other |
| Sampling phase is not a limiting factor | no trend across phase bins |

## 8. Sensitivity analyses (summary)

**WR:**
- SG window changes G(10) by ≤ 0.02 for every feature.
- Vendor speed instead of SG changes peak-speed G(10) from 0.33 to 0.34.
- Merging SPEED_OUT has no effect.
- Composition matters: peak speed is fragile to route composition (leave-one-route-out 0.07–0.52), while launch acceleration is not (0.51–0.70).
- Year: 2025 is consistently lower for launch acceleration and centripetal acceleration, the cohort with 11 routes and short SLANT recordings.

**DL:**
- Agreement values move by ≤ 0.10 across window, ω threshold and merge gap.
- Year and weight subgroups have wide CIs (n = 28–52).

## 9. Limitations

1. **Generalizability is not test-retest.** WR G-coefficients describe consistency across different routes. Repeat attempts within a route (102 cells) identify the residual but may be re-runs after failures.
2. **The G-study model assumes** normal effects and homoscedasticity across routes. The raw and cell-z versions differ (e.g. launch acceleration 0.55 vs 0.67), so heteroscedasticity matters; both are reported.
3. **Launch acceleration is mostly a start-from-stance measure.** It inherits the 10 Hz start-timing issues seen in Phases 12–13, although the 95th percentile is robust to window. Its overlap with the 10-yd split and tracked-40 early acceleration has not been checked in this phase; that check is combine-only and could be done next.
4. **DL has no same-side repeats** (1 athlete), so true test-retest of bend is not estimable. Side and attempt order are confounded.
5. **Arc truth in simulation** is a parametric family (linear curvature ramps, constant or linear speed). Real arcs (a bag, a hand fight) may differ, so the error bounds are indicative, not exact.
6. **No orientation and no bag position.** "Bend" is a body-path quantity only.
7. **Small subgroups:** year (28–44) and weight (50–52), with wide intervals.

## 10. Decisions

| part | feature | decision | reason |
|---|---|---|---|
| WR | **tangential acceleration p95 ("route-launch acceleration")** | **CONDITIONAL GO** (measurement only) | G(10) 0.55 [0.36, 0.68] raw, 0.67 [0.56, 0.75] cell-z; stable across routes and windows. Conditions: rename and interpret as launch-from-stance acceleration (73% of top frames in the first second), not route-break skill; resolve the 2025 drop (0.35); check its overlap with the 10-yd split and tracked-40 early acceleration (combine-only) before any further use |
| WR | route peak speed | **NO-GO** | G(10) 0.40 [0.06, 0.55] after removing truncated peaks; leave-one-route-out 0.07–0.52; between-athlete SD about 0.1 yd/s |
| WR | route peak speed, cell-z | **NO-GO** for now | G(10) 0.55 [0.42, 0.65], but composition-sensitive on the raw scale and little athlete-level variance |
| WR | mean moving speed | **NO-GO** | G(10) 0.21–0.27 |
| WR | centripetal acceleration p95 | **NO-GO** | G(10) 0.34 raw / 0.47 z; residual-dominated; 2025 G 0.21 |
| WR | braking p05 | **NO-GO** | G(10) ≈ 0.04 |
| WR | speed expression (ratio / log-difference) | **NO-GO as a distinct measurement** | G(10) 0.71, but 59% of its athlete variance is the tracked-40 peak; the route part has G ≈ 0.40 |
| WR | composite score | **NO-GO** | No defensible weighting; it would hide unreliable components |
| DL | arc speed (SG-corrected) | **CONDITIONAL GO** (measurement only, not "bend") | Error ≈ 0.4%; left/right agreement 0.41 (year-centred 0.36). Conditions: side and order confound must be resolved; overlaps with sprint speed (Phase 14 ρ −0.70 with the forty for peak speed) |
| DL | heading rate, curvature, radius, a_n, common-speed curvature ("bend") | **NO-GO** | Left/right agreement 0.14–0.31; smoothing error equals 18–60% of the observed variance; bias depends on arc geometry (−6% to −17%); no same-side repeats |
| DL | bilateral average of bend | **NO-GO** | Asymmetry and low agreement do not justify pooling |

## 11. Recommended next experiment

1. **Validate route-launch acceleration as a measurement.** All of it is combine-only and pre-specified.
   - Define the launch window explicitly: from the first frame above 1 yd/s to 1.0 s later.
   - Compare it with the tracked-40 early acceleration and the official 10-yd split. If it duplicates them, stop.
   - Quantify the start-timing sensitivity using the Phase 13 synthetic framework, with the generator re-used for straight starts.
   - Explain the 2025 drop (route set, recording length, layout).
2. **DL: no further bend work at 10 Hz is recommended.** The synthetic error bounds and the side/order design make bend measurement unidentifiable. If revisited at all, it needs same-side repeats or higher-rate tracking, neither of which is in this dataset.
3. **Outcome validation remains NO-GO.** Any future outcome study would need a new pre-registration naming route-launch acceleration only, after step 1. It would face the ~60-athlete power limit (|r| ≳ 0.36 detectable) documented in Phase 14.
