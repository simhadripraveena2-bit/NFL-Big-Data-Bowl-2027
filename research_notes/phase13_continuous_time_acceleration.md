# Phase 13: continuous-time estimation of post-turn acceleration (synthetic method validation)

**Status:** Stage E **failed** under the pre-specified criteria. **No estimator was frozen, and no real-athlete analysis (Stage F) was run.**

**Commits:**
- `91c923d`: generator, candidate estimators, dev stage and selection protocol. This was committed *before* any held-out run.
- Tests: `tests/test_phase13_ct_accel.py`, 8 tests.
- Full suite: 83/83 passing, including the code-freeze test.

**Runs** (aggregate synthetic outputs; git-ignored under `experiments/phase13_ct_accel/`):
- dev `dev_20261124T232259Z`;
- held-out `holdout_20261124T232533Z`.

**Code:**
- `src/nfl_bdb/simulation/shuttle_synth.py`: generator;
- `src/nfl_bdb/features/exit_accel_candidates.py`: E1–E3;
- `scripts/run_phase13_synthetic.py`;
- `configs/phase13_selection_protocol.json`: criteria, fixed before the held-out run.

**Scope:**
- **Game data:** no NFL game or outcome data were accessed.
- **Real combine data** were used only for:
  - the position-noise calibration (Section 3.3);
  - the ranges of trajectory geometry;
  - a descriptive realism comparison with the Phase 12 summaries (Section 7).
- **Not used:** real-athlete repeatability and official Combine results were not used to choose any estimator or parameter.
- **Unchanged:** Phase 11 and 12 code and results, and all frozen files.
- **Synthetic results** are not evidence of real-world validity.

## 1. Research motivation

Phase 12 found that the short shuttle gives a genuinely straight post-turn window: 11° of heading change and 2% centripetal share. But the acceleration estimated there had a within-position test-retest ICC of only 0.21. Across attempts, a window starting one 100-ms frame later was associated with about 0.8 yd/s² lower acceleration.

The question here: can a continuous-time estimator recover post-turn tangential acceleration accurately from 10 Hz positions when the true straight-exit moment falls between samples?

## 2. Existing estimator and its limitations (Stage A)

**Phase 12 definition, unchanged and reproduced here exactly as E1:**
- Savitzky–Golay smoothing of x and y (window 7, order 2); speed from the SG derivative.
- Drill axis = first principal direction; legs = |u| ≥ 1.5 yd/s.
- The first reversal sits between the first two opposite-sign legs.
- k0 = first frame after the speed minimum with speed ≥ 1 yd/s and velocity within 15° of the outgoing axis.
- Acceleration = OLS slope of SG speed over frames k0 … k0 + 5.
- Validity: every window frame straight, approach of at least 5 straight frames, window inside the recording.

**Reliability utilities:** `evaluation/repeatability.py` (ICC(3,1), ICC(2,1), typical error, within-position centring, player bootstrap).

**Limitations identified in Phases 11.1 and 12:**
1. **Window start is quantised to 0.1 s.**
2. **The SG kernel (±0.3 s) spans the turn** at the window start.
3. **Uncertainty is uncalibrated:** the slope's OLS interval ignores window-placement error.
4. **Unknown error source:** the real attempt-to-attempt typical error (0.63 yd/s²) was not decomposed into sampling, noise and genuine variation.

## 3. Synthetic trajectory design (Stage B)

### 3.1 Continuous-time model

Built on a 1 ms grid in the drill frame (u = along the outgoing axis, w = lateral):

| phase | model | varied (uniform ranges) |
|---|---|---|
| approach | half-sine acceleration pulse from −u₀ to −v_entry | u₀ 0.3–0.9 yd/s; v_entry 2.7–3.6 yd/s (initial running speed); duration 0.7–1.0 s |
| braking | constant deceleration D_in until \|u\| = u_c | D_in 6–10 yd/s²; u_c 0.4–0.9 |
| turn (reversal geometry) | u from −u_c to +u_c2 on a smoothstep (plant: zero along-axis acceleration at both ends); lateral reach W·sin(πτ); incoming direction deviation δ, blended to 0 across the turn | turn duration 0.15–0.45 s; u_c2 0.3–0.8; W 0.05–0.5 yd/s; δ ±10° (straight-exit direction) |
| outgoing | **du/dt = A₀(1 − u/V)** (athlete force–velocity profile) until t_b, then blended over 0.25 s to −D_out | t_b 0.65–0.95 s after the turn (puts the leg's speed peak about 1.0 s after the minimum, as in real data); D_out 5–8 |
| straight-running deviations | lateral sway S·sin(2πft), S 0–0.15 yd/s, f 1.5–2.5 Hz; along-axis step oscillation 0–0.4 yd/s at 3.5–4.5 Hz, faded in above 1 yd/s | amplitudes calibrated in 3.3 |

**Athletes and repeats:**
- A₀ ~ N(9.5, 8% CV) and V ~ N(9.0, 3% CV), representing one position group.
- The CVs are the within-position spreads implied by inverting official 10-yd and 40-yd times with a mono-exponential sprint model; the absolute levels from that inversion are not used.
- The A₀ level was set so the simulated E1 matches the real E1 median (6.1 vs 6.2 yd/s²).
- Each athlete has 2 trials with independent trial geometry, sampling phase and noise.

**Physical consistency:**
- Velocity is rotated into world coordinates; positions are its trapezoid integral; acceleration is its derivative.
- The unit test checks position against velocity to < 2 × 10⁻³ yd/s, and that θ equals the mean of a_t to within 0.05.

**Sampling:**
- 10 Hz, with phase uniform on [0, 100 ms).
- Positions are linearly interpolated from the 1 ms grid (error < 10⁻⁵ yd).
- 20 and 50 Hz are diagnostics only.

### 3.2 Ground-truth definitions (stored per trajectory)

- **t_rev:** the time u crosses zero.
- **t_min:** the time of minimum true speed.
- **t_exit:** the first time after t_min with true speed ≥ 1 yd/s and true velocity within 15° of the true outgoing axis (same criteria as Phase 12).
- **θ₀₅** = mean true tangential acceleration on [t_exit, t_exit + 0.5]. This is the target of E1 and E2.
- **θ₂₇** = mean true tangential acceleration on [t_exit + 0.2, t_exit + 0.7]. This is the target of E3, which uses the interval fixed in the brief.
- **A₀:** the athlete's force–velocity intercept; the athlete-level truth.

### 3.3 Noise calibration (geometry only; no repeatability, no outcomes)

**Position grid:**
- **2023 and 2024 positions lie exactly on a 1/30-yd grid** (100% of shuttle and 40-yd x values). Quantisation alone has SD (1/30)/√12 = 0.0096 yd.
- **2025 positions are continuous.**

**Local-quadratic residual SD** (5 frames, centre point, corrected for leverage):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| 40-yd dash, frames ≥ 7 yd/s | 0.0096 | 0.0095 | 0.0012 |
| shuttle, mid-leg frames ≥ 3 yd/s | 0.0107 | 0.0110 | 0.0072 |

**What this implies:**
- 2023–24 noise is essentially the quantisation.
- 2025 data are smooth, apparently pre-filtered.
- Shuttle legs contain extra true high-frequency motion of about 0.005–0.007 yd, which the step-oscillation amplitude (0–0.4 yd/s) was calibrated to reproduce. Without it, noise-free synthetic data give only 0.0013–0.0016.

**Noise scenarios evaluated:**

| scenario | definition |
|---|---|
| ideal | no noise, no step oscillation |
| Gaussian | 0, 0.0025, **0.005**, 0.01, 0.02, 0.03 yd |
| **quant30** | 1/30-yd rounding after 0.002 yd jitter |
| step-oscillation sensitivity | quant30 with step amplitude 0 and 0–0.8 |

**Calibrated scenarios:** quant30 (2023–24) and gauss005 (above the 2025 estimate).

## 4. Estimators (Stage C)

| | E1 frame-based (Phase 12) | E2 sub-frame exit time | E3 continuous-time fit |
|---|---|---|---|
| exit time | first eligible frame k0 | linear interpolation of each failing criterion's margin (speed − 1 yd/s; 15° − deviation) between k0−1 and k0; latest crossing | first time, on a 1 ms grid of the fitted curve, after the fitted speed minimum with fitted speed ≥ 1 yd/s and fitted heading within 15° of the drill axis |
| model | SG window 7, order 2 | same SG speeds | cubic smoothing splines x(t), y(t) (`scipy.make_smoothing_spline`, penalty λ∫f″², **λ = 10⁻⁴** at 10 Hz, scaled by fs/10) on a **fixed span** of frames [minimum − 0.5 s, minimum + 1.5 s], identical for every attempt |
| acceleration | OLS slope over 6 frames (0.5 s) from k0 | [v(t̂ + 0.5) − v(t̂)]/0.5, with v interpolated between SG frame speeds | mean of a_t(t) = v·a/\|v\| over **[t̂ + 0.2, t̂ + 0.7]** |
| boundaries | Phase 12 validity rules | as E1 | invalid if the span leaves the recording, if the interval comes within 0.3 s of the span end, or if any fitted heading in the interval deviates > 15° |
| 95% interval | OLS t-interval (df 4) | E1's standard error, df 4 | parametric bootstrap: Gaussian residuals at the fitted residual SD, refit, re-detect exit; B = 100; percentile |

**λ choice:** made on the **dev** seeds (101–103, 300 athletes, 1,200 trajectories per scenario), by the rule "minimum mean RMSE against θ₂₇ over the two calibrated scenarios". Candidates: GCV, 10⁻⁵, 3·10⁻⁵, 10⁻⁴, 3·10⁻⁴, 10⁻³. Dev RMSE: 0.276 at 10⁻⁴, against 0.289–0.336 for the others.

No real data were involved, and no fourth estimator was introduced.

## 5. Synthetic test results (dev, for design only)

- The dev pattern matched the held-out results below to two decimals: E1 R_meas 0.68, E2 0.69, E3 0.62/0.73 in the two calibrated scenarios.
- With no noise and no step oscillation, E3 recovers θ₂₇ almost exactly (RMSE 0.06, R_meas 0.97).

## 6. Held-out evaluation (Stage D)

**Design:** seeds 2001–2003, 600 synthetic athletes, 1,200 trajectories per scenario. Not used for any choice.

**Pre-specified criteria** (`configs/phase13_selection_protocol.json`), all required in both calibrated scenarios:
- **R_meas** = var(truth) / [var(truth) + var(error)] ≥ 0.80;
- **|bias|** ≤ 0.30 yd/s²;
- **failure rate** ≤ 10%.

Desirable: 95% coverage between 0.90 and 0.98, and R_meas ≥ 0.70 at 0.02 yd noise.

### 6.1 Main results, 10 Hz, calibrated scenarios

| | E1 frame-based | E2 sub-frame exit | E3 continuous-time |
|---|---|---|---|
| target | θ₀₅ (SD 0.51) | θ₀₅ | θ₂₇ (SD 0.41) |
| bias (quant30 / gauss005), yd/s² | −0.47 / −0.47 | −0.37 / −0.37 | **+0.05 / +0.05** |
| MAE | 0.50 / 0.50 | 0.42 / 0.42 | 0.24 / 0.19 |
| RMSE | 0.59 / 0.59 | 0.50 / 0.51 | 0.31 / 0.25 |
| **R_meas** (required ≥ 0.80) | **0.68 / 0.69** | **0.69 / 0.69** | **0.63 / 0.73** |
| Spearman, true vs estimate (trial) | 0.72 / 0.72 | 0.73 / 0.72 | 0.69 / 0.81 |
| 95% coverage (desirable 0.90–0.98) | 0.47 / 0.46 | 0.57 / 0.57 | 0.62 / 0.55 |
| failure rate | 0 / 0 | 0 / 0 | 0 / 0 |
| R_meas at 0.02 yd noise | 0.66 | 0.68 | 0.40 |
| synthetic test-retest ICC(3,1), 2 trials | 0.85 / 0.86 | 0.85 / 0.86 | 0.53 / 0.64 |
| synthetic typical error (yd/s²) | 0.15 / 0.14 | 0.15 / 0.14 | 0.26 / 0.20 |
| athlete-level Spearman with true A₀ | 0.92 / 0.93 | 0.93 / 0.93 | 0.74 / 0.80 |

**Exit-time error** against true t_exit (quant30):

| | mean | SD |
|---|---|---|
| E1 | +29 ms | 33 ms |
| E2 | −22 ms | 14 ms |
| **E3** | **−4 ms** | **11 ms** |

**Decision under the protocol: no estimator meets the required criteria.** E1 and E2 fail on R_meas and bias; E3 fails on R_meas. All three fail coverage. **Stage E fails.**

### 6.2 Error by factor (quant30, RMSE)

| factor | E1 | E2 | E3 |
|---|---|---|---|
| sampling phase, five 20-ms bins | 0.58–0.61 | 0.49–0.53 | 0.30–0.32 |
| turn duration ≤ 0.25 / 0.25–0.35 / > 0.35 s | 0.57 / 0.59 / 0.60 | **0.39** / 0.51 / 0.60 | 0.30 / 0.32 / 0.32 |
| lateral reach W ≤ 0.2 / 0.2–0.35 / > 0.35 | 0.60 / 0.58 / 0.58 | 0.50 / 0.50 / 0.51 | 0.33 / 0.32 / 0.29 |

**Position noise (Gaussian, 10 Hz), R_meas:**

| noise (yd) | E1 | E2 | E3 |
|---|---|---|---|
| 0 | 0.69 | 0.70 | 0.78 |
| 0.0025 | 0.69 | 0.70 | 0.76 |
| 0.005 | 0.69 | 0.69 | 0.73 |
| 0.01 | 0.68 | 0.69 | 0.63 |
| 0.02 | 0.66 | 0.68 | 0.40 |
| 0.03 | 0.63 | 0.64 | 0.22 |

**Step-oscillation amplitude (quant30), R_meas:**

| amplitude (yd/s) | E1 | E2 | E3 |
|---|---|---|---|
| 0 | 0.86 | 0.87 | 0.60 |
| 0–0.4 (reference) | 0.68 | 0.69 | 0.63 |
| 0–0.8 | 0.58 | 0.59 | 0.64 |

### 6.3 Higher sampling frequency (diagnostic only; not available in the competition data)

| R_meas (bias) | ideal: 10 / 20 / 50 Hz | gauss005: 10 / 20 / 50 Hz |
|---|---|---|
| E1 | 0.87 / 0.93 / 0.95 (−0.47 / −0.40 / −0.29) | 0.69 / 0.71 / 0.72 |
| E2 | 0.88 / 0.86 / 0.88 | 0.69 / 0.69 / 0.70 |
| E3 | **0.97 / 0.97 / 0.97** (+0.04) | 0.73 / 0.75 / 0.77 |

### 6.4 What the synthetic results show

1. **Sampling phase is not the dominant error source.**
   - E1's RMSE barely varies across sampling-phase bins (0.58–0.61).
   - Raising the rate to 50 Hz improves E1's synthetic test-retest ICC (0.86 → 0.95) and bias. But accuracy against the trial-level truth hardly moves (0.69 → 0.72 with noise).
   - **E3 is identical at 10, 20 and 50 Hz.** The 10 Hz grid does not limit it.
2. **What does limit accuracy:**
   - **Step-frequency oscillation.** The true tangential acceleration oscillates at about 4 Hz with stride. A 0.5-s window holds about two steps, so the step phase is part of the trial-level truth, and no smoother at 10 Hz recovers it.
   - **Position noise, for E3.** E3 differentiates positions twice. It is accurate when the data are clean (bias +0.05, RMSE 0.06 with no noise and no steps) but degrades quickly above 0.005 yd. The 2023–24 1/30-yd quantisation is at the margin.
3. **Sub-frame exit timing works but helps little.** E2 cuts exit-time error from +29 ± 33 ms to −22 ± 14 ms. E3 gets it to −4 ± 11 ms. But E2's acceleration gain is small (RMSE 0.59 → 0.50), and limited to short turns. Phase 12's "0.8 yd/s² per frame" was a cross-sectional association, not the causal effect of sampling phase.
4. **Intervals do not cover.** The OLS intervals (E1, E2) ignore placement and smoothing bias. The E3 bootstrap treats step oscillation as noise around a smooth truth. **No estimator's 95% interval is usable** (coverage 0.46–0.62).
5. **E1 vs E3 at athlete level.** E1 tracks the athlete parameter A₀ well (ρ 0.92) and gives a high synthetic test-retest ICC (0.85), because its smoothed early window averages over steps and sits where acceleration ≈ A₀. But this was not a pre-specified selection criterion, and it is not used post hoc. Phase 12 already measured E1's real repeatability: 0.46 pooled, 0.21 within position. E3's late interval [0.2, 0.7] s after exit is less athlete-specific in this generator (ρ with A₀ 0.74–0.80).

## 7. Real-data results

**Not run.** Stage E failed, so no estimator was frozen and the protocol does not allow Stage F.

**Descriptive comparison of synthetic vs real Phase 12 summaries** (not used for any choice):

| | real (Phase 12, R1) | synthetic E1, quant30 |
|---|---|---|
| attempt-level SD of E1 | 0.79 pooled; **0.61 within position** | 0.38 (one position group) |
| attempt-to-attempt typical error | **0.63 yd/s²** | **0.15 yd/s²** |
| test-retest ICC(3,1) | 0.46 pooled; 0.21 within position | 0.85 |
| E1, 5th / 50th / 95th percentile | 4.91 / 6.20 / 7.31 | 5.46 / 6.08 / 6.67 |
| minimum speed, median (5th–95th percentile) | 0.29 (0.09–0.58) | 0.27 (0.05–0.45) |
| minimum-to-window gap | median 0.2 s (0.1–0.3) | t_exit − t_min median 0.19 s |

**Interpretation, with stated uncertainty:**
- **Sampling, noise and modelled variation are not enough.** Sampling phase, measured position noise (including the 1/30-yd grid), step oscillation and the modelled trial-to-trial variation in turn geometry together produce a typical error of about 0.15 yd/s². The real attempt-to-attempt typical error is 0.63.
- **About 6% of the real within-athlete variance** is reproduced by these sources.
- **The rest is outside the generator.** It is either genuine attempt-to-attempt variation in how athletes accelerate out of the turn, or processes the generator does not include, such as different foot strategies, slips or vendor processing.
- **Estimators are not the main lever.** This points away from estimator design as the main route to better real repeatability, but it is a generator-dependent conclusion.

## 8. Limitations

- **The generator is a model.**
  - Force–velocity outgoing acceleration, a smoothstep plant, sinusoidal steps and sway, and an exponential-sprint-based spread across athletes are all simplifications.
  - Real within-athlete behavioural variation, foot placement and vendor filtering are not modelled. That is the main reason synthetic test-retest (0.85) far exceeds real (0.21–0.46).
- **2025 positions** look pre-filtered (residual 0.0012 yd on the 40). Their true noise structure, autocorrelated rather than iid, is not represented.
- **Different targets.** E1/E2 (θ₀₅) and E3 (θ₂₇) target different estimands, as the brief specifies. Their R_meas values are each relative to their own target's variance.
- **Ranges and the population.** A₀ CV and other ranges were fixed from combine geometry and official-time spread before evaluation. Different population assumptions would change R_meas and rank correlations.
- **Smoothing choice.** E3 was tried with one smoothing family (cubic smoothing spline) and one λ selected on dev data. Other model classes were not tried, by design: no fourth estimator.
- **Synthetic only.** None of this establishes real-world validity.

## 9. Recommendation

| question | decision |
|---|---|
| Freeze any of E1, E2 or E3 for real-athlete use | **NO-GO.** None meets the pre-specified held-out criteria. The best trial-level accuracy is E3 under the 2025-like noise (R_meas 0.73); under the 2023–24 quantisation it is 0.63. Bias is acceptable only for E3. Coverage is 0.46–0.62 for all three |
| Stage F (real-data repeatability with a frozen estimator) | **Not run**, as the protocol requires |
| Continuous-time estimation as a remedy for Phase 12's low repeatability | **NO-GO.** In synthetic data, the 10 Hz sampling phase is not the dominant error. E3's accuracy does not improve with higher sampling rate. Sampling plus noise reproduce only about a quarter of the real attempt-to-attempt typical error |
| Further method work on post-turn acceleration from combine 10 Hz tracking | **NO-GO** unless the lead approves a new question, for example characterising real within-athlete variation directly. Step-frequency structure and the real attempt-to-attempt variability, not frame timing, set the ceiling |
| Outcome validation | **NO-GO** (not attempted) |
