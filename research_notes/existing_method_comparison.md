# Phase 8 / 8B: existing approaches to latent movement capacity from noisy, context-dependent observations

**Basis:** `related_work_full_text_review.md`.

**Evidence levels:**
- F = full text read (Phase 8B: M3a, M3b, M7-2026);
- A = abstract read;
- S = search-level only;
- K = standard formulation.

Cells marked "?" depend on details that are not verifiable at the available level.

**Phase 8B changes:**
- M3a, M3b and M7 upgraded to F; their "?" cells are resolved.
- New classes: M4b (random-effect / determinant SFA) and M10 (rate-of-occurrence EVT for best performances).
- §4 conclusions revised.

## 1. Method classes considered

| id | class | representative works (evidence) |
|---|---|---|
| M1 | observed maximum / top-k mean / high percentile of game speed | common practice; our Phase 2–4 (top-5 mean); match-peak studies (S); **TTA per-player v_max = 99th percentile (F)** |
| M2 | in-situ A–S profiling (per-bin maxima + linear fit) | Morin 2021 (A); Miguens 2024 (A, S) |
| M3a | conditional quantile regression, population envelope | **Gutiérrez-Pérez & Agudo 2026 (F; preprint)** |
| M3b | per-athlete quantile A–S curves | **Shteynberg et al. 2025 (F for the poster; student poster, not peer-reviewed)** |
| M4 | stochastic frontier analysis; order-α partial frontiers; boundary under observation error | Aigner 1977 (S/K); Daouia et al. (S); Hall & Simar 2002 (A); Kneip et al. 2015 (S) |
| M4b | SFA with unit random effects / Bayesian individual effects / covariate-dependent deficit | Greene 2005, Koop et al. 1997, Battese & Coelli 1995 (S/K; DOIs verified) |
| M5 | physics motion models with player parameters | Brefeld 2019 (S); Narizuka 2023 (S); Spearman 2018 (S); da Silva 2025 (S); the six TTA baselines (F via 2.1) |
| M6 | state-space smoothing of kinematics (Kalman) | SciSports 2018 (S); "Who Blocks Whom?" 2026 (S) |
| M7 | hierarchical Bayesian models of realised movement | **Nguyen & Yurko 2026 (F; preprint)**; Nguyen & Yurko 2025 (S); swimming shrinkage 2024 (S) |
| M8 | measurement-error corrections (SIMEX, regression calibration) | Cook & Stefanski 1994 (S/K); our Phase 1.6, Phase 4 |
| M9 | deep generative trajectory imputation | NAOMI 2019 (S) |
| M10 | EVT for best performances: endpoint estimation; point-process / GPD with occurrence rate and covariates | Einmahl & Magnus 2008 (A); Spearing et al. 2021 (A) |

## 2. Comparison

| criterion | M1 max / top-k | M2 in-situ A–S | M3a population QR (TTA) | M3b athlete QR (effort poster) | M4 SFA / partial frontier | M4b RE / determinant SFA | M7 hierarchical Bayes (step-and-turn) | M10 EVT best performances |
|---|---|---|---|---|---|---|---|---|
| **what is estimated** | an order statistic | athlete A0, S0 | Q_0.01 of arrival time given geometry (population); v_max only as an input | per-player 0.95 quantile of acceleration and deceleration given speed; effort = mean proximity score | boundary f(x) + one-sided u | boundary + unit effect + u whose mean depends on covariates | random intercepts on the conditional **mean** of arcsine step length; player random effect on turn concentration | endpoint; tail of best performances with an occurrence rate |
| **key assumption** | maximal efforts occur; equal exposure | maximal effort per bin; linear | fast tail of observed arrivals = feasible; slowness from intent, fatigue and tactics discarded | 0.95 quantile ≈ the player's own frontier | i.i.d. u, Gaussian v | parametric u and v; exchangeable units | Gaussian (transformed) steps; exchangeable players; context as fixed effects | GPD tail; regular variation |
| **sparse observations** | poor | poor | n/a (population); unseen players get the median v_max | **poor**: independent per-player fits, ≥ 20 runs; backups score highest (exposure artefact is plausible, untested) | moderate | **good** (pooling) | **good** (partial pooling) | good for events (shared covariates); athlete level ? |
| **context** | none | not modelled | via geometry features | **none** (stated limitation) | via x | via x and deficit determinants | **yes**: defender and teammate features, defensive-team effect, lag | via covariates (time, technology) |
| **measurement error** | none | heuristic outlier removal | SG smoothing, hard bounds, SUVAT label filter; tail errors acknowledged | none | v term; Hall–Simar: noise biases the boundary at O(σ) | v term | through the likelihood | not addressed (A) |
| **exposure / opportunity** | ignored | ignored | ignored (code comment on "cameo players") | **ignored** | not the *number* of draws | not the number of draws | not targeted | **yes**: occurrence rate is modelled (event level, A) |
| **uncertainty per athlete** | none | repeated sub-fits | none for players; cluster bootstrap over matches for MAE | **none** | asymptotic | **posterior** | **full posterior** | likelihood / asymptotic |
| **unseen athletes** | impossible | impossible | population model + median v_max | impossible | via covariates | via prior | yes (new random-effect draw) | ? |
| **external validation of capacity** | sometimes vs sprint tests (S) | vs radar or sprint tests (A/S) | **none** (physics baselines only) | **none**; effort vs outcomes ≈ −0.08 | none typical | none typical | **none** (face validity, PPC) | world records (A) |
| **leakage / design issues found** | n/a | n/a | canonical code computes v_max within the match, test matches included ("look-ahead leakage", per the config) | individual standards limit cross-player comparison (stated) | n/a | n/a | no held-out validation of the movement models | n/a |

## 3. Strongest existing approaches (by sub-problem)

| sub-problem | strongest approach found | what it does not do (F-level where marked) |
|---|---|---|
| athlete speed / acceleration capacity from routine tracking | M2 (Morin 2021; Miguens 2024) | exposure and effort not modelled; no pooling (A) |
| feasibility envelope from tracking | **M3a** (TTA, F) | population envelope; per-player capacity only as a plug-in input; no exposure, pooling, uncertainty or external validation (F) |
| capacity vs realised effort | **M3b** (F, poster) and M4/M4b | M3b: no pooling, uncertainty or context (F). M4b: the deficit can depend on context and units can be pooled (K), so **this part of G1 is existing method** |
| sparse athletes, uncertainty | **M7** (step-and-turn, F) and M4b (K) | M7 targets the conditional mean, not a boundary (F) |
| exposure-dependent extremes | **M10** (A) | event-level, not athlete-level from within-game tracking; no independent same-athlete validation (A; full text not read) |
| tail noise in boundary estimation | Hall & Simar 2002 (A); Kneip et al. 2015 (S) | identifiable only if the error distribution is known (A) |
| inference in crossed designs | Owen 2007; Owen & Eckles 2012 (S) | nonlinear variance-component functionals not verified |

## 4. Conclusions for gap analysis (revised in Phase 8B)

1. **The specific G1 problem is not solved by any of the three closest works (F).**
   - TTA treats per-player v_max as an exposure-naive known input (and the canonical code leaks it from test matches).
   - The effort poster fits independent per-player quantile curves for a different estimand.
   - Step-and-turn pools players hierarchically, but for typical, not maximal, movement.
   - None validates a capacity estimate externally.
2. **The statistical building blocks of G1 do exist:**
   - hierarchical player effects (M7, F);
   - random-effect frontiers with covariate-dependent deficits (M4b, K);
   - boundary estimation under noise (M4, A);
   - exposure-aware EVT with covariates and endpoints (M10, A).
   
   A G1 method that *assembles* these is an application of existing methods, not a new algorithm. This follows the project lead's rule that combining existing methods is not an original contribution.
3. **External validation remains rare.** None of the F-level works, and none of the A-level frontier or EVT works, checks per-athlete capacity estimated from game data against an independent standardised measurement of the same athletes. The competition data has one: combine tracked 40 peak speed, within-position R_x 0.94–0.99.
4. **Inference in crossed designs:** strong prior work (unchanged).
