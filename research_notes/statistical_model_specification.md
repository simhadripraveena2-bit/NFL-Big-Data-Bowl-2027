# Phase 3.5: Statistical Model Specification (H1, H2, H5)

*Companion to `preregistration.md` (which fixes what is tested and how decisions are made) and
`power_analysis.md` (what the sample can detect). This note gives the mathematics.*
- Code for contexts and covariates: `src/nfl_bdb/data/play_table.py`.
- Simulation counterparts of every estimator: `src/nfl_bdb/models/power.py`.

**No model below has been fitted to combine × game-outcome data.**

## 0. Notation
| Symbol | Meaning |
|---|---|
| *i* | player (the independent unit), *i* = 1…n_p within position *p* |
| *j* | play of player *i* (REG season, eligible opportunity) |
| *c* ∈ {h, l} | task context: high vs low speed demand (pre-registered pairs, §1.1) |
| *t(ij)* | team-season of play *ij* |
| x_i | tracked combine 40 **peak speed** (yd/s): the best valid attempt (fit R² > 0.95), standardised within position |
| F_i | official electronic **40-yard time** (s): sign-reversed and standardised within position, so higher = faster |
| y_ijc | play max speed (yd/s): WR/TE between snap and throw (`vmax_prepass`); DB/DL/OL over the play (`vmax_play`) |
| s_ij | `separation_at_pass_forward` (yd), WR deep routes |
| **w**_ij | pre-snap play covariates (exact list in `preregistration.md` §4) |
| a_ij | NFL experience year (season − draft year + 1), a play-level covariate |

**Indexing assumptions:**
- **Players are nested in position.** Every model is fitted separately by position; cross-position statements use separately estimated quantities.
- **Plays are crossed with team-season.** 14% of WRs played for more than one team (§4 of the power note).

## 1. H1: task-conditioned speed translation

### 1.1 Primary model (one per position; bivariate in context)
$$
y_{ijc} = \mu_c + \boldsymbol\gamma_c^\top \mathbf w_{ij} + \kappa_c\,a_{ij} + \beta_c\,x_i + b_{ic} + \tau_{t(ij)} + \varepsilon_{ijc}
$$
- $(b_{ih}, b_{il})^\top \sim N_2(\mathbf 0, \Sigma_b)$, with $\Sigma_b$ unstructured. This allows a player's high- and low-demand levels to differ, and to be correlated.
- $\tau_t \sim N(0, \sigma_\tau^2)$.
- $\varepsilon_{ijc} \sim N(0, \sigma_c^2)$, with variance specific to the context.
- **Estimation:** REML; `statsmodels` MixedLM or the equivalent lme4 formula
  `y ~ 0 + ctx + ctx:(w + a + x) + (0 + ctx | player) + (1 | team_season)`, with `weights = varIdent(ctx)`.

**Primary estimand (standardised translation in context *c*).** This is the correlation between capacity and the *true*, covariate-adjusted player-context level:
$$
\rho_c=\frac{\beta_c\,\mathrm{sd}(x)}{\sqrt{\beta_c^2\,\mathrm{var}(x)+\Sigma_{b,cc}}},\qquad \Delta_{\text{H1}}=\rho_h-\rho_l .
$$

Why the disattenuated scale is used:
- $\rho_c$ is free of within-player noise $\sigma_c^2/n_{ic}$.
- Contexts differ in play counts and noise. A contrast of raw (attenuated) correlations would mix the hypothesis with differential reliability.
- On the raw yd/s scale, slopes are not comparable when contexts have different between-player spread.

Also reported:
- the raw-scale interaction $\beta_h-\beta_l$ (yd/s per yd/s), with model-based and bootstrap CIs;
- $\rho_c$ multiplied by $1/\sqrt{R_x}$ with $R_x = 0.987$ (correction for predictor error; negligible).

**Pre-registered context pairs (h, l):**

| Position | h | l | Role in protocol |
|---|---|---|---|
| WR | deep routes | short routes | **primary H1-WR** |
| DB | man coverage | underneath zone | **primary H1-DB** |
| TE | deep | short | descriptive (n = 17–18) |
| DL | pass rush | run | secondary (role-sorting test, §1.4) |
| OL | pass block | run | secondary H5 (§3) |

For DB, deep zone is a third context. Three-context fits are reported as secondary.

### 1.2 Fast moment estimator (used in power simulations, and as a cross-check)
For each context *c*:
1. Residualise $y$ on the play covariates (pooled OLS within position).
2. Form the player-context means $\bar m_{ic}$, with counts $n_{ic}$ and pooled within-SD $\hat\sigma_c$.
3. Estimate the between-player variance and the correlation:
$$
\hat V_c=\widehat{\mathrm{var}}_i(\bar m_{ic})-\overline{\hat\sigma_c^2/n_{ic}},\qquad
\hat\rho_c=\frac{\widehat{\mathrm{cov}}_i(x_i,\bar m_{ic})}{\widehat{\mathrm{sd}}(x)\sqrt{\max(\hat V_c,\;0.05\,\widehat{\mathrm{var}}(\bar m_{ic}))}} .
$$

Properties and use:
- $\hat\rho_c$ is consistent for $\rho_c$ as *n* grows; the floor guards against negative variance estimates.
- If the REML and moment estimates of $\Delta_{\text{H1}}$ differ by more than half a bootstrap SE, both are reported and **the REML estimate stays primary**.

### 1.3 Inference
- **Player-cluster bootstrap:**
  - Resample players with all their plays, B = 2,000.
  - Refit with warm starts. If REML is too slow for B = 2,000, use the moment estimator inside the bootstrap; this is declared in the results.
  - CI: percentile and BCa, both reported. **Percentile is primary.** Simulated coverage of the percentile CI is 0.92–0.94 at n = 57, which is slightly below nominal; this is reported.
- **Test:** reject H0: Δ ≤ 0 if the (1 − α_Holm)-level two-sided CI excludes 0 and $\hat\Delta>0$. The Holm family is defined in the protocol.
- **Team-season effect:** the variance $\sigma_\tau^2$ is retained even when it is near zero. When a team-season has only one cohort player, the team effect is not separable from the player effect (51% of WR team-seasons); this is reported.

### 1.4 Extensions (all secondary)
- **Nonlinearity:**
  - Replace $\beta_c x_i$ by a natural cubic spline $f_c(x_i)$ with 3 df (knots at within-position tertiles).
  - Report the average derivative difference $\overline{f_h'}-\overline{f_l'}$ and a plot of $f_h, f_l$ with player-bootstrap bands.
  - Linear vs spline is compared by player-grouped CV (§4). It is not selected on in-sample fit.
- **Ceiling-robust outcome:**
  - Replace the play-level mean model with the player-context **upper speed expression**: the mean of the top-10% play maxima, with ≥ 20 plays per context.
  - Fit the bivariate player-level measurement-error model $\bar u_{ic} = \mu_c + \beta_c x_i + b_{ic}+e_{ic}$, with $\mathrm{var}(e_{ic})$ from a within-player bootstrap.
- **DL role sorting (H1-DL):**
  - Compare $\rho$ (pooled DL, both contexts) with $\rho$ from a model adding alignment (EDGE vs interior) × context fixed effects and standardised combine weight.
  - Prediction: a material drop (protocol §6).
- **Demand meta-regression (H1-global):**
  - Over all 11 position-context cells *k*, regress $\hat\rho_k$ on the cross-fitted demand $\hat D_k$ (protocol §3.3):
$$
\hat\rho_k=\alpha_{p(k)}+\lambda\,\hat D_k+\eta_k,\qquad \eta_k\sim N(0,\widehat{\mathrm{se}}_k^2+\omega^2).
$$
  - Fitted by REML random-effects meta-regression, with a cell-cluster bootstrap within position.
  - With 11 cells and 5 positions this is **descriptive**: no confirmatory test.

**The demand-moderated coefficient.** The methodological proposal is to replace the five position-specific slopes with a single task-conditioned coefficient:
$$
\beta_{p}(c)=\beta_{0p}+\beta_1\,D(c)\quad\text{(raw scale)},\qquad \rho_p(c)=\alpha_p+\lambda D(c)\quad\text{(standardised)}.
$$
- It is benchmarked against two baselines: (B1) one slope per position, and (B2) one slope per position-context.
- The criterion is player-grouped CV log-likelihood and RMSE on held-out players' context means (§4).
- B2 is the saturated benchmark. The demand model is useful if it matches B2 with fewer parameters, and if it beats B1.

## 2. H2: incremental value of tracked peak speed beyond the 40 (WR, deep routes)

### 2.1 Primary model
$$
s_{ij} = \mu + \boldsymbol\gamma^\top\mathbf w_{ij} + \kappa\,a_{ij} + \beta_F F_i + \beta_P x_i + b_i + \tau_{t(ij)} + \varepsilon_{ij},\quad b_i\sim N(0,\sigma_b^2),\ \varepsilon_{ij}\sim N(0,\sigma^2),
$$
- Fitted on deep-route plays with a separation value.
- **Primary parameter:** $\beta_P$, the effect of tracked peak speed holding the official 40 fixed.
- **Reported scale:** $\beta_P^{*}=\beta_P\,\mathrm{sd}(x)/\sqrt{\beta_F^2\mathrm{var}(F)+\beta_P^2\mathrm{var}(x)+2\beta_F\beta_P\mathrm{cov}(F,x)+\sigma_b^2}$, together with the **true-scale partial correlation** $r_{P\cdot F}$ and $\Delta R^2$ of the true between-player deep-separation level.
- **Inference:**
  - player-cluster bootstrap CI (B = 2,000; percentile);
  - Wald test with Satterthwaite df as a check;
  - two-stage equivalent: WLS of EB-centred player means on $(F_i, x_i)$ with HC3 errors and weights $1/(\hat\sigma_b^2+\hat\sigma^2/n_i)$.

### 2.2 Incremental predictive value (what decision-makers care about)
- **Target:** each held-out player's covariate-adjusted deep-route separation level, shrunk toward the mean with a variance estimated on the training folds.
- **Models:**
  - M0: position mean;
  - M1: $F$;
  - M2: $F + x$;
  - M2s: $F$ + spline($x$), with 3 df;
  - M3: $F$ + 10-yd split (a reference, not a test).
- **Metrics:**
  - $\Delta R^2_{CV}$ = $R^2_{CV}(M2) − R^2_{CV}(M1)$;
  - ΔRMSE;
  - Spearman ρ between predicted and held-out levels;
  - mean log predictive density.
- **CV scheme:**
  - **player-grouped 10-fold, repeated 20 times;**
  - leave-one-player-out, closed-form PRESS, as a check;
  - uncertainty from a player bootstrap of the whole CV procedure (B = 500).

### 2.3 Measurement error in the official 40
The official 40's test–retest reliability is unknown in this dataset (single official value).
- **Why it matters:** if $R_F<1$ and separation depends only on true 40 speed, $\hat\beta_P$ is biased away from 0. A more precise speed measure looks "incremental".
- **Pre-specified sensitivity:** errors-in-variables (regression-calibration / SIMEX) refits assuming $R_F \in \{0.90, 0.95, 0.99\}$, with $R_x = 0.987$.
- **Interpretation:** a $\beta_P$ that survives only at $R_F = 0.99$ is reported as "tracked peak speed is a more precise speed measurement". It is **not** reported as "a different athletic construct".

### 2.4 Short routes (descriptive)
- The same model is fitted on short routes, with the contrast $\beta_P^{deep}-\beta_P^{short}$.
- Adjusted short-route separation reliability was 0.22 in Phase 3 (screening definition). The contrast is **descriptive**: no confirmatory claim.

## 3. H5: offensive linemen as a comparison group
H5 asks whether OL behave as the demand model predicts. It does **not** assume a null.

| Quantity | Definition | Estimation |
|---|---|---|
| $\Delta_{OL}$ | OL task contrast, pass block vs run (§1.1 model) | as H1 |
| $\Delta_{WR}-\Delta_{OL}$ | difference-in-contrasts (independent samples) | difference of estimates; CI from independent player bootstraps |
| $\rho_{OL}^{pooled}$ vs $\hat\rho_{OL}^{pred}$ | OL overall translation vs the value predicted by the demand meta-regression fitted **without OL cells** | prediction interval: $\hat\alpha+\hat\lambda D_{OL}$ ± t·√(se² + ω² + se_fit²), with $\hat\alpha$ the mean position intercept |

**Interpretation (protocol §6.3):**
- *Consistent with the demand model:* $\Delta_{OL}$ is near 0, as both OL contexts have D ≈ 0.01, and $\rho_{OL}$ lies inside the out-of-position prediction interval.
- *Informative departure:* OL translation clearly above the prediction. Combine speed would then carry information in a low-demand task, pointing to a non-demand mechanism such as general athleticism or body composition.
- *Uninformative:* the prediction interval is too wide to discriminate. This is the expected outcome given 11 cells; it is stated in advance.

## 4. Validation (all models)
| Layer | Scheme | Purpose |
|---|---|---|
| Player-grouped CV | 10-fold by player, repeated 20 times, stratified by draft class | model comparison (demand vs per-position slopes; M1 vs M2) |
| Season-forward | fit on 2023 + 2024 REG seasons; evaluate on the 2025 REG season | temporal replication: sign and CI of $\Delta_{\text{H1}}$, $\beta_P$; held-out prediction metrics |
| New-player subset | the 2025 draft class (not in any training season) | descriptive only (WR 23, DB 25 with any snap) |
| Negative controls | permuted context labels within player; OL contrast; WR short-route β_P | detect mechanical artefacts |
| Robustness grid | thresholds 50/100/200; with/without time-to-throw; REG vs REG+POST; leave-one-team-out; ceiling-robust outcome; spline | stability of sign and magnitude |

**Leakage rules:**
- All residualisation coefficients (γ), the cross-fitted demand $D$ and shrinkage variances are re-estimated **inside each training fold**.
- Players never contribute to both a training and a test fold.
- In season-forward validation, 2025 data never enter estimation.

## 5. Complexity
- **REML LMM:** $O(\#\text{plays}\cdot q^2 + n\,q^3)$ per iteration with q ≤ 3 random effects. Plays ≈ 2×10⁴ per position, so seconds per fit.
- **Bootstrap:** ×2,000.
- **Moment estimator:** $O(\#\text{plays})$; vectorised bootstrap $O(B\,n)$.
- **Full CV:** 200 fits per model.
- Everything runs on the 4-CPU / 15 GB machine, one position at a time (memory rule).

## 6. Pseudocode: demand-conditioned translation estimator (DCT)
```
input: plays (player i, context c, outcome y, covariates w), capacity x_i, folds K
for each training fold:
    gamma  <- OLS(y ~ w) within position                      # residualisation, train only
    D_c    <- crossfit_demand(train plays)                   # §3.3 of protocol
    fit LMM_c: y_res ~ 0 + ctx + ctx:x + (0+ctx | player) + (1 | team_season)
    rho_c  <- beta_c sd(x) / sqrt(beta_c^2 var(x) + Sigma_b[c,c])
    (alpha_p, lambda) <- meta-regression of rho_c on D_c across cells
predict held-out players' context means from alpha_p + lambda D_c (DCT) vs per-cell slopes (B2) vs per-position (B1)
score: held-out log-likelihood / RMSE; bootstrap over players for CIs
```
