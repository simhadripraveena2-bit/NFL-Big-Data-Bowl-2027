# Phase 3.5: Simulation-Based Power Analysis

*Pipeline:*
- `scripts/run_power_analysis.py` (`calibrate`, then `simulate`), run `experiments/power_analysis/20261121T020640Z`, seed 3501;
- estimators `src/nfl_bdb/models/power.py` (tests in `tests/test_power.py`);
- notebook `notebooks/06_power_analysis.ipynb`;
- figures `reports/figures/power_*.png`.

**Firewall:**
- Game outcomes provide nuisance parameters only.
- Combine data provide only their own distribution.
- Effect sizes are a grid.
- **No combine value was joined to any game outcome.**

## 1. Bottom line
- **H1-WR (primary) is powered only for large task contrasts.** Minimum detectable Δ = ρ_deep − ρ_short at 80% power (α = 0.05, directional) is **0.27–0.33**, depending on the low-demand correlation (0.29–0.37 under Holm m = 3). Power is **0.44** at Δ = 0.2 and **0.79** at Δ = 0.3.
- **H2 (primary) is not adequately powered for plausible effects.**
  - A true-scale partial correlation of tracked peak speed with deep-route separation, given the 40, needs to be about **0.6** for 80% power. Power at 0.3 is 0.28–0.30.
  - The 95% CI half-width of the standardised coefficient is ≈ ±0.68.
  - **Three causes:**
    - deep-route separation barely differs between players (between-player SD 0.15 yd vs play-to-play SD 1.73 yd; reliability of a player mean 0.45);
    - tracked peak speed and the official 40 share most of their variance (true r ≈ 0.84);
    - there are only 57 WRs.
- **H1-DB is not powered** (Δ = 0.3 → power 0.29). The man and underneath-zone levels of the same DB are *negatively* correlated (true r = −0.33, an apparent role effect), which doubles the variance of the contrast. **H1-DB was moved to secondary before any association was seen** (protocol §2).
- **H5 comparison:**
  - The OL task contrast alone has an MDE ≈ 0.36.
  - The difference-in-contrasts WR − OL has an MDE ≈ 0.53, so it is weakly powered.
- **Players, not plays, are the binding constraint.** Five times more plays per WR raises power at Δ = 0.2 from 0.46 to 0.59. Doubling the number of players (to 120) raises it to 0.77.
- **The test behaves as intended under the null:**
  - Empirical directional size is 0.029–0.040 for WR/DB/DL/OL against a nominal 0.025, and 0.05 for TE (n = 17).
  - Percentile-bootstrap coverage is 0.92–0.94.
  - The slight liberalness is reported, not hidden.

## 2. Simulation design
### 2.1 What is held at observed values (outcome-only calibration)
REG season; eligible players per protocol §4; residualised on pre-snap covariates.

| Test | Position | Contexts (h / l) | Players | Median plays (h / l) | Within-player SD (h / l) | Between-player SD of true mean (h / l) | Reliability of player mean (h / l) | True cross-context r |
|---|---|---|---|---|---|---|---|---|
| H1 | WR | deep / short | 57 | 141 / 144 | 0.88 / 1.21 yd/s | 0.23 / 0.28 | 0.89 / 0.85 | 0.73 |
| H1 | TE | deep / short | 17 | 58 / 125 | 0.82 / 0.97 | 0.19 / 0.29 | 0.73 / 0.91 | 0.84 |
| H1 | DB | man / under-zone | 52 | 118 / 115 | 1.54 / 1.38 | 0.30 / 0.23 | 0.76 / 0.69 | **−0.33** |
| H1 | DL | pass rush / run | 53 | 214 / 205 | 1.09 / 1.38 | 0.24 / 0.22 | 0.90 / 0.81 | 0.73 |
| H5 | OL | pass block / run | 53 | 609 / 422 | 0.92 / 1.08 | 0.18 / 0.20 | 0.94 / 0.91 | 0.45 |
| H2 | WR | deep / short separation | 57 | 140 / 144 | 1.73 / 1.95 yd | **0.15** / 0.27 | **0.45** / 0.65 | 0.26 |

**Predictor distributions** (combine only, all participants):
- tracked peak speed SD 0.28 (WR), 0.28 (DB), 0.35 (OL), 0.60 (DL), 0.30 (TE) yd/s;
- observed peak vs official 40: r = −0.81 (WR), −0.80 (DB), −0.90 (OL), −0.98 (DL), −0.91 (TE);
- peak-speed reliability 0.987 (Phase 2).

**Play counts per player** are resampled from the observed eligible players. Each sample size quoted is the real eligible n: WR 57, TE 17–18, DB 52–56, DL 53, OL 53.

### 2.2 Data-generating processes and tests
Exact equations are in `statistical_model_specification.md` §1–2 and the `power.py` docstring.

**H1 / H5:**
- **Generation:**
  - true capacity z;
  - observed peak = √0.987·z + error;
  - true player-context means with correlations ρ_h, ρ_l to z, plus residual player effects correlated across contexts, so that the true cross-context r equals its observed value;
  - observed means = true + mean of n_ic within-player residuals.
- **Test:**
  - moment estimator of the disattenuated ρ_c (spec §1.2);
  - **player-cluster percentile bootstrap** (400 resamples per simulated dataset, 2,000 datasets per grid cell);
  - reject if the two-sided CI excludes 0 and Δ̂ > 0.
- **Effect grid:** ρ_low ∈ {0.1, 0.3, 0.5}; Δ ∈ {0, 0.1, …, 0.5}.

**H2:**
- **Generation:**
  - true 40 speed F and peak P with corr = observed / √(R_F·R_P);
  - true deep-separation level = a·F + b·P⊥ + residual, where a = corr with F ∈ {0, 0.3} and b gives a true partial correlation of P given F in {0, …, 0.7};
  - observed level = true + play noise;
  - observed F and P carry measurement error, with R_F ∈ {0.90, 0.95, 0.99} and R_P = 0.987.
- **Test:** OLS on the observed 40 and peak, with HC3 SE (2,000 datasets per cell). Leave-one-player-out ΔR² is recorded.

### 2.3 Is the player-level shortcut valid?
For WR and DB at Δ = 0.2, every play was simulated with (i) normal residuals and (ii) **resampled empirical residuals**, which are skewed and heavy-tailed. Results agree with each other and with the shortcut:

| Position | Residuals | Mean Δ̂ (true 0.199) | SD Δ̂ | Power (α 0.05) |
|---|---|---|---|---|
| WR | normal | 0.208 | 0.111 | 0.47 |
| WR | empirical | 0.206 | 0.114 | 0.47 |
| DB | normal | 0.193 | 0.232 | 0.14 |
| DB | empirical | 0.206 | 0.225 | 0.18 |

## 3. H1 results
Power at ρ_low = 0.3, α = 0.05, directional.

| True Δ | WR (57) | TE (17) | DB (52) | DL (53) | OL (53) |
|---|---|---|---|---|---|
| 0 (size) | 0.040 | 0.053 | 0.033 | 0.032 | 0.029 |
| 0.1 | 0.15 | 0.10 | 0.07 | 0.13 | 0.12 |
| 0.2 | 0.44 | 0.22 | 0.16 | 0.41 | 0.35 |
| 0.3 | **0.79** | 0.39 | 0.29 | 0.76 | 0.63 |
| 0.4 | 0.98 | 0.62 | 0.51 | 0.96 | 0.90 |
| 0.5 | 1.00 | 0.80 | 0.77 | 1.00 | 0.99 |

**Minimum detectable Δ** (80% power), by ρ_low:

| Position | ρ_low 0.1 | 0.3 | 0.5 | Holm (m = 3), ρ_low 0.3 | SD of Δ̂ under H0 |
|---|---|---|---|---|---|
| WR | 0.33 | **0.30** | 0.27 | 0.35 | 0.12 |
| DL | 0.35 | 0.32 | 0.28 | 0.36 | 0.12 |
| OL | 0.40 | 0.36 | 0.29 | 0.40 | 0.15 |
| DB | > 0.5 | > 0.5 | 0.40 | > 0.5 | 0.25 |
| TE | > 0.5 | 0.50 | > 0.5* | > 0.5 | 0.24 |

\*ρ_high is capped at 0.95, so the grid stops at Δ = 0.4 for ρ_low = 0.5.

**Precision:** the 95% CI half-width for Δ is about ±0.23 (WR, DL), ±0.29 (OL) and ±0.48 (DB, TE).

**Raw (attenuated) vs disattenuated contrast:**
- The raw correlation contrast has slightly higher power: WR 0.83 vs 0.79 at Δ = 0.3.
- It is **not** used as primary. When the two contexts have different reliabilities, the raw contrast mixes the hypothesis with measurement noise. Here the WR reliabilities are similar (0.89 / 0.85), so the two will rarely disagree, and both are reported.

**What size of Δ is plausible?**
- This is reasoned *a priori*, not from outcome data.
- Only 1% of WR short-route plays reach 90% of the player's top speed, against 17% of deep routes.
- If short-route speed is mostly set by route geometry, ρ_short could be well below ρ_deep. A Δ of 0.2–0.3 is the natural range under H1. **Power in that range is 0.44–0.79**, so H1-WR has a reasonable but far from guaranteed chance of detection.

## 4. H2 results
Power (α = 0.05, directional) by true partial correlation r(P, deep separation | 40).

| R_F (official-40 reliability) | corr(40, sep) | 0 (size) | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.7 | MDE |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.90 | 0.0 | 0.023 | 0.06 | 0.13 | 0.24 | 0.38 | 0.56 | 0.73 | 0.85 | 0.66 |
| 0.90 | 0.3 | **0.039** | 0.10 | 0.17 | 0.30 | 0.47 | 0.63 | 0.78 | 0.88 | 0.62 |
| 0.95 | 0.0 | 0.020 | — | — | 0.26 | — | — | — | — | 0.59 |
| 0.95 | 0.3 | 0.031 | — | — | 0.28 | — | — | — | — | 0.60 |
| 0.99 | 0.0 | 0.023 | — | — | 0.28 | — | — | — | — | 0.58 |
| 0.99 | 0.3 | 0.023 | — | — | 0.29 | — | — | — | — | 0.59 |

Full grid in the notebook (§4).

**Findings:**
- **MDE ≈ 0.58–0.66** (true-scale partial r). The SD of the standardised coefficient is ≈ 0.34–0.35.
- **False "incremental value":**
  - Suppose separation depends only on true 40 speed (corr 0.3) and the official 40 has reliability 0.90. Tracked peak speed then appears incremental 3.9% of the time, against a nominal 2.5%.
  - The inflation is modest *at this n*, because power is low overall. It would grow with n.
  - Hence the protocol's errors-in-variables sensitivity and its interpretation rule (protocol §12).
- **Leave-one-player-out ΔR² is a noisy criterion.** At a true partial r of 0.3, ΔR²_LOO > 0 in only 46–55% of datasets; at 0.5, 82–86%.

**Power vs number of WRs** (partial r, R_F = 0.95, corr(40, sep) = 0.3):

| WRs | 0.2 | 0.3 | 0.4 |
|---|---|---|---|
| 30 | 0.09 | 0.17 | 0.23 |
| 57 | 0.18 | 0.30 | 0.46 |
| 120 | 0.32 | 0.55 | 0.80 |
| 200 | 0.48 | 0.79 | 0.96 |

Detecting a moderate incremental association (partial r ≈ 0.3) would need **≈ 200 WRs**, roughly the number of drafted receivers in 6–8 draft classes.

## 5. Players vs plays (WR / DB / OL, true Δ = 0.2, α = 0.05)
| WR players | 0.5× plays | 1× | 2× | 5× |
|---|---|---|---|---|
| 30 | 0.20 | 0.32 | 0.31 | 0.39 |
| 57 | 0.34 | 0.46 | 0.55 | 0.59 |
| 80 | 0.49 | 0.63 | 0.66 | 0.72 |
| 120 | 0.62 | 0.77 | 0.86 | 0.88 |

- Beyond the observed ~140 plays per context, more plays barely help: the player means are already 85–90% reliable.
- Power is limited by **between-player sampling of the true correlations**, which only more players can reduce.
- DB shows the same pattern at a lower level: 57 players → 0.14–0.20 at any play multiple.

## 6. H5 (OL comparison group)
- **OL own contrast (pass block vs run):** MDE ≈ 0.36 (α 0.05).
  - The protocol's equivalence criterion (90% CI within ±0.15) is **not attainable**: the 90% half-width is ≈ 0.24.
  - H5(a) is therefore estimation.
- **Difference in contrasts (Δ_WR − Δ_OL),** from independent samples with SE = √(0.12² + 0.146²) ≈ 0.19:

| True difference | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 |
|---|---|---|---|---|---|
| Power (α 0.05) | 0.08 | 0.18 | 0.35 | 0.56 | 0.75 |

- **OL vs the demand-model prediction (H5c)** depends on the 11-cell meta-regression. It was not simulated: with 11 cells and 5 positions the prediction interval will be wide. The protocol states in advance that "uninformative" is the expected outcome.

## 7. Multiple testing and its cost
- **Primary analysis:** a fixed sequence (H1-WR → H2), each at α = 0.05. FWER is controlled because H2 is tested only if H1-WR is rejected.
- **Alternative Holm (m = 3, including H1-DB):** lowers H1-WR power at Δ = 0.3 from 0.79 to 0.67, with no compensating gain, because H1-DB and H2 are unlikely to be rejected.
- **Probability of reaching H2 at all:**
  - under Δ_WR = 0.3: 0.79;
  - then H2 power at partial r 0.3 is 0.28, so P(confirm H2) ≈ 0.22.
  - Under Δ_WR = 0.2 the P(confirm H2) is ≈ 0.12.

## 8. Falsification is also hard
- **H1-WR "falsified" (protocol §12)** requires the 90% CI upper bound < 0.15, i.e. Δ̂ < ≈ −0.05.
  - If the true Δ = 0, this happens with probability ≈ 0.34; "inconclusive" is otherwise likely.
- **H2 cannot be falsified** at this n: a 90% CI entirely below a partial r of 0.10 is essentially unreachable.

## 9. Implications (carried into the protocol)
1. **H1-WR is the study's only adequately powered confirmatory test**, and only for Δ ≳ 0.3. It is ordered first.
2. **H2 is kept as primary** (as approved), second in sequence, with an explicit statement that it is very likely inconclusive. It is reported as estimation with its CI and the precision statement; no claim of absence.
3. **H1-DB was demoted to secondary**, before any association, because of power.
4. **TE stays descriptive.**
5. Robustness to the simulation assumptions:
   - normal vs empirical residuals: verified;
   - estimator: the moment estimator vs the REML LMM; the protocol requires checking their agreement before the confirmatory run.
6. **No design change can manufacture power.**
   - Lowering the eligibility threshold to 50 adds 6 WRs (power +≈ 0.03).
   - Pooling WR + TE (n ≈ 74) is a pre-specified *exploratory* sensitivity, because TE contexts differ (deep share 30% vs 52%).

## 10. Limitations of this power analysis
- Effect sizes are hypothetical. Nuisance parameters come from the same data that will be analysed: outcome-only, but the variance components are estimated, not known.
- The simulation omits:
  - team-season clustering beyond what the player means already contain;
  - selection into eligibility.
  Both would *reduce* power further.
- The bootstrap uses 400 resamples per simulated dataset (2,000 in the real analysis), which slightly widens the Monte Carlo error of power: ±0.01 at 2,000 datasets.
