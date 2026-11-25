# Phase 16: WR route-launch acceleration, construct and redundancy audit

**Scope:**
- **Measurement only, Combine data only.** No NFL game or outcome data were opened or joined, and no predictive model was fitted.
- **Combine-only reference used:** the registered tracked-40 peak (`predictors.parquet`: `nfl_id`, `x_peak`, `valid_tracked_40`).
- **Nothing earlier changed:** Phases 11–15, the registered analyses and the frozen files are unchanged.
- **Output location:** athlete-level outputs are under the git-ignored `data/interim/phase16/`; aggregates are under `experiments/phase16/`.
- **No capacity claim.** Nothing here establishes a new athletic capacity.

**Protocol, committed before any real-athlete statistic and before the held-out synthetic run:**
- `configs/phase16_protocol.json`, commit `2a3fc47`.
- It contains one disclosed amendment written after the synthetic dev run (§2.3).

**Runs:**

| run | id |
|---|---|
| synthetic | `synthetic_dev_20261125T040656Z`, `synthetic_holdout_20261125T040858Z` (`scripts/run_phase16_launch_synthetic.py`) |
| real | `real_20261125T041228Z` (`scripts/run_phase16_launch_real.py`) |

**Code:** `src/nfl_bdb/features/launch.py` and `src/nfl_bdb/simulation/start_synth.py`.

**Tests:** `tests/test_phase16_launch.py` (4). Full suite 99/99, including the code-freeze test.

## 1. Exact measurement definition (frozen)

**Kinematics:** Phase 15 settings. Savitzky–Golay order 2, window 7 (5 and 9 as sensitivity) on x and y at 10 Hz; speed from the SG derivative; a_t = numerical gradient of speed.

**Onset and window:**
- Onset = first frame with speed > 1.0 yd/s.
- Window = onset … onset + 10 frames (1.0 s, 11 frames).

**Rejections** (no extrapolation):
- already moving at frame 0;
- never exceeds 1 yd/s;
- window not fully observed.

**Primary measure:** **95th percentile of a_t over the window.**

**Diagnostics only:** mean a_t and net speed gain over the same window.

**Identity:**
- 13 route labels (12 route families) as in Phase 15. SPEED_OUT_LEFT (2024) is kept separate; GAUNTLET and CIRCUS are excluded.
- Draft year, and the route × year cell.

**Tracked-40 reference:**
- The *identical* definition is applied to every Combine 40 attempt of the WR.
- Athlete value = mean over valid attempts.
- Test-retest uses the first two valid attempts.

## 2. Synthetic onset validation (Part B)

### 2.1 Generator

Straight starts from a stationary stance on a 1 ms grid. From movement start t0:

  a(t) = κ·A0·(1 − v/V)·min(1, (t − t0)/ramp)

| component | values |
|---|---|
| athlete A0 | N(8.0, 8% CV) |
| per trial | effort κ 0.75–0.95; force-development ramp 0.10–0.35 s |
| step oscillation | 0–0.4 yd/s (0 and 0–0.8 as sensitivity) at 3.5–4.5 Hz |
| lateral sway | yes |
| recording start relative to t0 | −0.1 to +0.5 s (real onsets fall 1–8 frames after recording start) |
| sampling | 10 Hz, phase uniform |
| noise | 1/30-yd grid (2023–24), Gaussian 0–0.01 yd |

**Design:** 60 athletes × 10 trials ("routes"). Dev seeds 101–103; held-out seeds 2001–2003.

### 2.2 Truth

- **Onset:** first continuous time the true speed exceeds 1 yd/s.
- **Primary launch truth:** 95th percentile of the step-free propulsive acceleration on the 11-instant grid from the true onset.
- **Instantaneous truth** (secondary): includes the 4 Hz step oscillation, which 10 Hz smoothing cannot resolve. Against it the estimate is −40% biased and correlates only 0.15.

This choice of primary truth was fixed after one dev-seed smoke test, before any held-out or real data.

### 2.3 Held-out results (window 7)

| criterion (protocol) | 1/30-yd grid | Gaussian 0.005 | threshold | pass |
|---|---|---|---|---|
| onset error, median (SD; 90th percentile of \|error\|) | **+0.038 s** (0.030; 0.078) | +0.038 s (0.030; 0.079) | \|median\| ≤ 0.05 s | ✅ |
| launch relative bias vs trend truth | **−11.8%** (SD 2.7%) | −11.5% (SD 2.4%) | \|bias\| ≤ 10% | ❌ |
| trial measurement reliability | 0.89 | 0.90 | ≥ 0.80 | ✅ |
| athlete-level Spearman (10-trial mean vs true A0) | 0.95 | 0.95 | ≥ 0.80 | ✅ |
| failure rate, recordings starting before onset | 0.0% (late-starting recordings correctly rejected) | 0.0% | ≤ 10% | ✅ |

**Sensitivity:**
- **Sampling phase:** no effect (bias −11.4% to −11.8% across phase bins).
- **Noise:** reliability 0.87–0.94.
- **Step oscillation (0 to 0.8):** no effect on bias or rank.
- **Window:** bias −8% (window 5) to −15% (window 9).

**Disclosed amendment (written after dev, before held-out; criterion values unchanged):**
- The bias criterion governs only *absolute-magnitude* statements.
- Onset, reliability, rank and failure govern relative and variance-component comparisons.
- **The bias criterion failed. Launch values are therefore reported as relative scores only, never as yd/s².**
- The bias is nearly constant across conditions (SD about 2.5%), so it does not affect rankings.

**Synthetic vs real noise:** a single synthetic trial is 89% reliable. The real single-route generalizability is only G(1) ≈ 0.18 (§7). So real route-to-route variation is far larger than the measurement error the generator models: technique, stance and effort differ between routes.

## 3. Route-launch distributions (Part A)

**Coverage:**
- 1,286 route attempts from 107 WR; **1,252 valid** (34 already moving at the first frame).
- Onset frame: median 2 (5th–95th percentile 1–8).

**By draft year:**

| year | valid rate | median onset frame | median frames | launch p95 mean (SD) |
|---|---|---|---|---|
| 2023 | 97.7% | 2 | 58 | 4.73 (0.72) |
| 2024 | 97.0% | 3 | 59 | 4.99 (0.73) |
| 2025 | 97.3% | 2 | 63 | 4.98 (**0.56**) |

These are relative units (−12% bias, §2).

**Tracked 40:** 176 attempts from 94 WR; 165 valid; 75 athletes with two valid attempts. Route × year distributions are in `route_launch_distributions.csv`.

## 4. Comparison with straight-line sprint measures (Part C)

**Athlete score:** mean over routes of the route × year-standardised launch p95 (107 athletes; median 11.7 routes).

| reference | n (missing) | Pearson [95% CI] | Spearman [95% CI] | Pearson, reference year-centred |
|---|---|---|---|---|
| tracked-40 launch p95 (same definition) | 90 (17) | 0.30 [0.01, 0.52] | 0.29 [0.10, 0.47] | 0.36 |
| official 10-yd split | 97 (10) | −0.15 [−0.31, 0.04] | −0.17 [−0.37, 0.04] | −0.14 |
| official 40 time | 97 (10) | −0.13 [−0.32, 0.07] | −0.08 [−0.27, 0.12] | −0.13 |
| tracked-40 peak speed | 94 (13) | 0.08 [−0.13, 0.28] | 0.07 [−0.13, 0.26] | 0.08 |

The raw cell-centred score gives the same picture (0.34 / −0.17 / −0.14 / 0.10).

**Variance explained** (OLS, 90 athletes with all references): R² = 0.090 for the 40 launch alone; 0.02, 0.02 and 0.01 for the other references alone; **0.10 for all four** (adjusted 0.06).

**Critical qualification: the tracked-40 launch reference is not reliable.**

| 40 launch measure | test-retest ICC(3,1), 2 attempts, window 7 [95% CI] | across windows 5–9 |
|---|---|---|
| p95 | **0.02 [−0.16, 0.44]** | — |
| mean a_t | 0.15 | 0.05–0.18 |
| net speed gain | 0.16 | 0.05–0.18 |

- Typical error is about 0.47–0.65 against a between-attempt SD of 0.50–0.67.
- With two attempts, the reliability of the 40 launch mean is at most about 0.04–0.3.
- **So a small correlation with the 40 launch cannot show non-redundancy:**
  - correcting 0.30 for this unreliability gives a value at or above 1;
  - complete redundancy with true early-sprint acceleration is consistent with the data;
  - so is its absence.
- **The informative references are the official times, which are reliable.** Route launch is only weakly associated with the official 10-yd split (−0.15) and 40 time (−0.13), and not with the tracked peak (0.08).

## 5. Remaining athlete-specific information (Part D)

**Model:** REML on route × year-standardised attempts:

  z ~ cell (fixed) + standardised athlete-level references (fixed) + athlete + athlete × route + residual

90 athletes and 1,048 attempts with all references; 200 athlete-cluster bootstrap resamples.

| references | share of athlete variance explained [95% CI] | G(10) without references | **residual G(10) [95% CI]** | protocol rule |
|---|---|---|---|---|
| tracked-40 launch | 0.15 [−0.01, 0.46] | 0.72 | **0.69 [0.54, 0.76]** | share < 0.70; residual G ≥ 0.50 with lower bound ≥ 0.30: passes |
| all four references | 0.11 [−0.03, 0.48] | 0.72 | **0.70 [0.52, 0.77]** | passes |

**Coefficients** (per SD of reference): 40 launch +0.20; 10-yd −0.02; 40 time −0.02; peak −0.00.

**Interpretation, with care:**
- A repeatable route-launch component remains that is **not** explained by official sprint times or tracked peak speed.
- How much of it the *true* early-sprint acceleration would explain is **unknown**, because the tracked-40 reference is unreliable and covariate measurement error weakens any adjustment.
- The residual component is **not** evidence of a new capacity. Its weak link to sprint measures, together with large route-to-route variation, is equally consistent with drill-specific launch behaviour (stance, effort and pacing in non-maximal drills).

## 6. The 2025 generalizability drop (Part E)

| G(10), frozen launch definition | 2023 | 2024 | 2025 |
|---|---|---|---|
| raw, all routes | 0.62 | 0.73 | 0.62 |
| raw, 10 harmonised routes (present in all years) | 0.57 | 0.71 | 0.56 |
| standardised, all routes | 0.67 | 0.73 | 0.65 |
| standardised, harmonised routes | 0.68 | 0.71 | 0.61 |

The harmonised routes drop POST_CORNER_LEFT (absent in 2025) and both SPEED_OUT labels.

**Findings:**
- **The Phase 15 drop (2025 G = 0.35) does not persist** under the frozen launch window. It also does not appear when route composition is harmonised or the number of routes is equalised (G is projected to the same n).
- **Phase 15's whole-route 95th percentile** included acceleration outside the launch. What made 2025 differ there is not identified.
- **Coverage is the same across years:** valid rate 97–98%, median onset frame 2–3. 2025 recordings are slightly longer (63 vs 58–59 frames).
- **One observable difference:** 2025 has smaller raw between-athlete and total variance (launch SD 0.56 vs 0.72; σ² athlete 0.013 vs 0.024–0.041). This fits the smoother 2025 position processing noted in Phase 13, but **a cause cannot be established** from these data. Cohort differences cannot be separated from processing differences, because year and cohort are confounded.

## 7. Generalizability results (Part F)

**Cross-route generalizability is consistency across different routes. It is not test-retest reliability.**

| version | G(1) | G(4) | G(6) | G(8) | **G(10) [95% CI]** | G(12) |
|---|---|---|---|---|---|---|
| raw | 0.14 | 0.43 [0.28, 0.53] | 0.53 | 0.60 | **0.65 [0.49, 0.74]** | 0.69 |
| route × year-standardised | 0.18 | 0.47 [0.34, 0.57] | 0.57 | 0.64 | **0.69 [0.56, 0.76]** | 0.73 |

**Variance components** (raw): athlete 0.024, athlete × route 0.054, residual 0.073.

**Stability:**
- **Leave one route out:** raw 0.62–0.72; standardised 0.66–0.73.
- **Smoothing window 5 / 9:** raw 0.63 / 0.68; standardised 0.65 / 0.72.
- **Within year:** see §6.

**Change from Phase 15:** the frozen launch window raises generalizability from Phase 15's whole-route definition (0.55 raw / 0.67 standardised) and removes its year instability.

## 8. Limitations

1. **The tracked-40 launch reference is unreliable** (ICC ≤ 0.18), so redundancy with true early-sprint acceleration is unresolved. The reliability of the official 10-yd split is not estimable here (one official value per athlete).
2. **Magnitudes are biased** (−12%) by smoothing. Relative use only.
3. **Real route-to-route variation is about 5× the synthetic measurement error.** The drill-to-drill behaviour behind it (stance, effort, coaching cue, pace) is unobserved.
4. **Generalizability is not test-retest.** The 102 within-route repeat cells may be re-runs after failures.
5. **No orientation:** stance type and first-step mechanics are not observable.
6. **Year is confounded with cohort and with position processing** (1/30-yd grid in 2023–24 vs smooth 2025).
7. **n = 90–107 WR.** CIs on shares explained are wide (−0.03 to 0.48).

## 9. Recommendation

| question | decision |
|---|---|
| Is the synthetic onset accurate enough for athlete-level relative comparisons? | **Yes:** onset +0.04 s; athlete rank 0.95. Magnitude bias −12% means relative scores only |
| Is route-launch acceleration redundant with official sprint measures? | **No:** \|r\| ≤ 0.15 with the 10-yd split, 40 time and tracked peak; together they explain about 11% of athlete variance |
| Is it redundant with straight-line early acceleration? | **Unresolved:** the tracked-40 launch reference is unreliable (ICC 0.02–0.18), so neither redundancy nor distinctness can be concluded |
| Is the residual athlete component repeatable? | **Moderately:** residual G(10) 0.69–0.70 [0.52, 0.77] across routes |
| **Overall** | **CONDITIONAL GO for one new pre-registration only.** Per the protocol, the measurement passes the redundancy and residual-reliability rules, but with the unresolved 40 reference and a construct that may reflect drill behaviour rather than capacity |

**What the pre-registration should contain (not carried out here):**
- **Exactly one WR regular-season outcome**, for example opportunity-adjusted separation at pass forward.
- **Predictor:** the frozen route-launch score (standardised, athlete mean over at least 8 routes).
- **Required covariates:** the official 10-yd split and 40 time.
- **Stated in advance:**
  - that redundancy with true early-sprint acceleration is unresolved;
  - the expected attenuation (G ≈ 0.69);
  - the ≈ 60-athlete power limit (|r| ≳ 0.36 detectable);
  - that a null result would not separate "no relation" from "drill behaviour rather than ability".
- **Not approved here.** It needs the lead's explicit approval before drafting. No outcome data were touched.
