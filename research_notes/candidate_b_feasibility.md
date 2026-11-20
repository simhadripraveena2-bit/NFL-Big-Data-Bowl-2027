# Candidate B — Feasibility of Estimating Athletic Capacity (A–S Profile) from Game Tracking (Experiment 1)

*Simulation study only. No NFL outcome data were used. Code: `src/nfl_bdb/simulation/movement.py`,
`src/nfl_bdb/models/capacity_estimator.py`, `scripts/run_capacity_simulation.py`; analysis:
`notebooks/02_capacity_estimation_simulation.ipynb` (evaluation run `experiments/capacity_sim/20261120T195416Z`;
figures `reports/figures/sim_b_*.png`). Every number below is produced by that notebook.*

## 1. Bottom line
1. **Measurement and preprocessing dominate estimator choice.**
   - At the noise level that matches real NGS tracking, *every* published-style estimator overestimates top speed S0 by 5–8% with a 7-frame smoothing window, and by 15–21% with a 5-frame window.
   - Noise inflates the *maximum* accelerations at high speed, which flattens the fitted A–S line.
   - Window choice alone moves the bias of Morin binning from 15.5% to 2.5%. This matches the literature finding that acceleration processing is rarely reported (Ellens et al. 2022).
2. **Our proposed estimator is *not* uniformly better. Superiority is only partly supported, and only in simulation.**
   - **S0:** the SIMEX-corrected estimator beats same-preprocessing Morin binning in 21 of 23 cells (unpooled; the other 2 are ties) and in **all 23 cells** with pooling (95% CIs exclude 0). It halves the bias (base: +5.4% → +2.6–2.8%). Against the **naive maximum observed speed**, however, results split (pooled: 10 cells better, 9 worse, 4 ties). It only wins clearly when maximal efforts are scarce (≤ 25 plays, or one quarter of the maximal-effort rate).
   - **A0:** plain Morin binning is the best estimator (base RMSE 3.6%). The proposed estimator is **worse** in most cells (16 of 23 for the unpooled variant) and better only under tracking faults.
   - **Calibration:** the empirical-Bayes pooling step makes intervals badly over-confident (median coverage of nominal 90%: 41% for S0). The **unpooled SIMEX + jackknife** intervals cover conservatively (median 97% S0, 95% A0), but they are wide (base S0 width about 15% of S0).
3. **Model misspecification is the largest unaddressed risk.** If the true acceleration–speed frontier is curved (exponent 0.8 or 1.3 instead of linear), *all* linear estimators are biased about ±12–13% on A0. Real data cannot reveal which shape is true.
4. **Recommendation:**
   - Continue Candidate B only as a **measurement layer**: S0 from SIMEX-corrected binning *or* robust peak speed, A0 from Morin binning, uncertainty from the play jackknife without pooling.
   - **Drop the "new estimator" claim as currently formulated.**
   - Re-scope the algorithmic contribution to Candidate C, where it is stronger (see `feasibility_comparison.md`).

## 2. Methods reviewed and their assumptions
All target the frontier a_max(v) = A0 (1 − v/S0) (Hill–Keller form; Morin et al. 2021). Published procedures were known from abstracts only, so the baselines are our implementations of the described rules.

| Method | Source | Key assumptions |
|---|---|---|
| Max observed | — | athlete reaches S0 and A0 in the data |
| Morin binning | Morin et al. 2021 | each 0.2 m/s bin contains a near-maximal frame; noise ≪ signal at the maxima |
| CI / boxplot outlier rules | Cormier et al. 2023 | outliers are artefacts |
| DBSCAN + binning | inspired by Miguens et al. 2024 | artefacts are low-density points |
| Quantile regression (τ = 0.99) | Koenker & Bassett 1978 | the frontier is a fixed conditional quantile at every speed |
| **NCP-AS (proposed)** | this work | white position noise with known/estimable SD (SIMEX; Cook & Stefanski 1994); quadratic extrapolant; normal–normal pooling |

**Designs we tried and rejected on development seeds** (notebook 02 §3; reported so that nothing is hidden):
- a bin-maximum frontier with exposure-scaled shortfall;
- a frame-level stochastic frontier (Aigner et al. 1977 form) with a mixture shortfall — A0 bias −22% at realistic noise, −8.7% even on perfect kinematics;
- an extreme-value bin model;
- a rational SIMEX extrapolant (unstable).

The frontier models failed because the shortfall distribution of real-like efforts (a point mass at the frontier plus a broad sub-maximal spread) is badly approximated by exponential forms.

## 3. Synthetic trajectory generator (`simulation/movement.py`)
- **Athletes:** (S0, A0) drawn per position from mono-exponential fits to the **real combine 40s** (792 attempts; median R² = 0.996). Example: WR S0 11.64 ± 0.44 yd/s, A0 8.89 ± 1.23 yd/s²; OL S0 9.77 ± 0.42, A0 7.50 ± 1.20.
- **Plays:** median duration 7.0 s (real median about 70 frames). Each play is a sequence of effort, cruise and braking segments, with heading changes limited by centripetal acceleration.
- **Efforts:** intensity e ∈ (0, 1]; acceleration = e·A0(1 − v/S0) with a 0.1-s first-order lag. A small, role-dependent probability p_max that an effort is maximal (WR/DB 0.06, TE/DL 0.04, OL 0.015). **This is an assumption.**
- **Exposure:** 10–500 plays per athlete, plus a "mixed" cell drawn from the real player-season distribution (median 263 plays).
- **Measurement:** positions recorded at 10 Hz (also 5 and 25 Hz), white noise per axis, rounding to 0.01 yd, optional tracking-fault bursts. Kinematics from Savitzky–Golay derivatives.
- **Noise calibration against real data:** 0.01 yd matches the robust SDs of position and speed second differences in real 2025 game tracking (0.030 yd and 0.059 yd/s while running). This is approximate, because the values are quantised.

## 4. Results (evaluation seeds; 5 replicates × 100 athletes per cell; 24 cells)
### 4.1 Base cell (100 plays, noise 0.01 yd, 10 Hz, window 7): % error vs truth
| Estimator | S0 bias | S0 RMSE | A0 bias | A0 RMSE | S0 90% coverage | A0 90% coverage |
|---|---|---|---|---|---|---|
| max observed | −3.0 | 3.8 | −19.6 | 20.0 | — | — |
| Morin binning | +5.4 | 5.6 | −0.8 | **3.6** | — | — |
| binning + CI rule | +5.3 | 5.4 | −0.4 | 3.4 | — | — |
| DBSCAN + binning | +8.0 | 8.5 | −12.7 | 15.4 | — | — |
| quantile reg. 0.99 | +7.1 | 7.5 | −3.8 | 6.0 | — | — |
| binning + jackknife | +5.4 | 5.6 | −0.8 | 3.6 | 0.04 | 0.76 |
| **SIMEX + jackknife (no pooling)** | **+2.8** | **3.6** | −1.5 | 4.6 | **0.96** | **0.98** |
| **NCP-AS (SIMEX + pooling)** | +2.6 | 4.1 | −0.6 | 7.1 | 0.51 | 0.86 |

### 4.2 Paired tests vs the strongest same-preprocessing baseline
Squared-error difference per athlete, with 95% bootstrap CI. "Better" or "worse" is claimed only if the CI excludes 0.

| Comparison (23 cells with measurement noise) | Better | No difference | Worse |
|---|---|---|---|
| NCP-AS vs binning, **S0** | **23** | 0 | 0 |
| NCP-AS vs binning, **A0** | 2 (tracking-fault cells) | 3 | **18** |
| SIMEX (no pooling) vs binning, S0 | 21 | 2 | 0 |
| SIMEX (no pooling) vs binning, A0 | 1 | 6 | 16 |
| SIMEX (no pooling) vs max observed, S0 | 11 | 2 | 10 |
| NCP-AS vs max observed, S0 | 10 | 4 | 9 |

### 4.3 Sensitivity to the amount of data (`sim_b_exposure.png`)
- **S0:** NCP-AS RMSE stays about 4–5% from 10 to 500 plays. Max-observed degrades from 3.8% (100 plays) to 10.8% (10 plays).
- **A0:** all estimators degrade sharply below 50 plays (about 20% RMSE at 10 plays; −18 to −19% bias). Acceleration capacity is **not** estimable for low-snap players.
- **Censoring diagnostic** (mixed-exposure cell): athletes with no play reaching ≥ 95% of S0 (8% of athletes) still get S0 within about 4.4% RMSE from NCP-AS (binning 5.9%). Their A0 RMSE is about 11–12%.

### 4.4 Sensitivity to noise, smoothing and sampling (`sim_b_noise_window_fs.png`)
| Cell | Binning S0 bias / RMSE | NCP-AS S0 bias / RMSE |
|---|---|---|
| noise 0 | +0.2 / 0.7 | n/a |
| noise 0.005 | +2.8 / 3.0 | +1.5 / 2.6 |
| noise 0.01 (base) | +5.4 / 5.6 | +2.6 / 4.1 |
| noise 0.02 | +11.6 / 11.8 | +4.7 / 6.7 |
| noise 0.03 | +18.9 / 19.3 | +7.5 / 9.1 |
| window 5 / 9 | +15.5 / 15.8 and +2.5 / 2.6 | +6.5 / 8.1 and +1.0 / 2.4 |
| 5 Hz / 25 Hz | +3.2 / 3.4 and +3.4 / 3.5 | +1.7 / 3.1 and +1.4 / 2.7 |

- With noiseless positions the pipeline is unbiased.
- SIMEX with the noise SD mis-specified by ×0.5 removes only part of the bias (+4.6% S0 bias, vs +2.6% with the correct SD). With ×1.5 it over-corrects slightly (−0.6%).

### 4.5 Robustness
- **Curved frontier (exponent 0.8 / 1.3):** A0 bias ≈ −12% / +13% for every linear estimator. S0 bias stays below 5% for NCP-AS.
- **Tracking faults** (1% / 3% of plays): binning fails or explodes (A0 RMSE 26–43%; failures 7–9%). The quantile regression is the most robust A0 estimator (RMSE about 5.8%). Pooled NCP-AS protects S0 (bias ≤ 1.7%) but not A0 (RMSE 11–29%). **Faults must be removed upstream** (as planned for game 2025101205).
- **Fewer maximal efforts** (p_max × 0.25): A0 bias −5.6% (binning), −4.7% (NCP-AS). S0 is barely affected for NCP-AS (+1.7%).

## 5. Assumptions that cannot be validated with the available dataset
1. **Shape of the true frontier.** Linear A–S is supported for *maximal sprints* (combine 40 fits), but untested over the full speed range in games; misspecification costs about ±12% on A0.
2. **Structure of NGS noise and the vendor's smoothing filter.** Only two summary statistics were matched. SIMEX needs the noise SD and assumes white noise.
3. **Frequency and duration of maximal efforts in games** (p_max). These drive whether peak speed ≈ S0, i.e. whether the simple max-speed estimator suffices.
4. **Combine capacity = game capacity.** Dillon et al. (2021, AFL) found match peak velocity *above* test peak velocity (abstract), so the equality is not guaranteed.
5. **Within-season stability of capacity** (fatigue, injury, training) is not modelled.

## 6. What the experiment does and does not establish
- **Establishes (in simulation):**
  - Noise-driven bias is the dominant problem, and SIMEX removes most of it for S0.
  - Exposure limits A0 more than S0.
  - Pooling as implemented harms calibration.
  - No estimator is robust to tracking faults or to curvature of the frontier.
- **Does not establish:**
  - real-data accuracy (no ground truth exists);
  - that capacity estimates relate to performance (not tested, by design);
  - that the proposed estimator is a new algorithm that "improves on existing approaches" in general. **For A0 it does not.**
