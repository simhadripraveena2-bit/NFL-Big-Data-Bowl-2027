# Phase 8: existing approaches to latent movement capacity from noisy, context-dependent observations

**Basis:** `related_work_full_text_review.md`.
- Evidence levels: A = abstract read (Phase 1.5); S = search-level only; K = standard formulation. **No full text was read in Phase 8.**
- Cells that depend on paper-specific details not verifiable at S level are marked "?".
- Statements about what a *method class* does follow from its standard formulation (K).

## 1. Method classes considered

| id | class | representative works (evidence) |
|---|---|---|
| M1 | observed maximum / top-k mean / high percentile of game speed | common practice; our Phase 2–4 (top-5 mean); match-peak studies (S) |
| M2 | in-situ A–S profiling (per-bin maxima + linear fit) | Morin 2021 (A); Miguens 2024 (A, S) |
| M3a | conditional quantile regression, population envelope | Gutiérrez-Pérez & Agudo 2026 (S) |
| M3b | per-athlete quantile A–S curves | Shteynberg et al. 2025 (S; student report) |
| M4 | stochastic frontier analysis; order-α partial frontiers | Aigner et al. 1977 (S/K); Daouia et al. 2006/2010 (S) |
| M5 | physics motion models with player parameters (arrival regions, pitch control) | Brefeld 2019 (S); Narizuka 2023 (S); Spearman 2018 (S); da Silva 2025 (S) |
| M6 | state-space smoothing of kinematics (Kalman) | SciSports 2018 (S); "Who Blocks Whom?" 2026 (S) |
| M7 | hierarchical Bayesian models of realised movement | Nguyen & Yurko 2025, 2026 (S); swimming shrinkage 2024 (S) |
| M8 | measurement-error corrections (SIMEX, regression calibration) | Cook & Stefanski 1994 (S/K); our Phase 1.6, Phase 4 |
| M9 | deep generative trajectory imputation | NAOMI 2019 (S) |

## 2. Comparison

| criterion | M1 max / top-k | M2 in-situ A–S | M3a population QR | M3b athlete QR | M4 SFA / partial frontier | M5 physics motion | M6 Kalman | M7 hierarchical Bayes | M8 SIMEX / RC | M9 imputation |
|---|---|---|---|---|---|---|---|---|---|---|
| **what is estimated** | an order statistic of observed speed | athlete A0, S0 of the upper A–S envelope | feature-conditional lower or upper quantile (e.g. TTA at τ = 0.01) | athlete-specific high-quantile A–S curve | boundary f(x) plus one-sided deficit u | player kinematic parameters, reachable sets | latent (x, v, a) path | athlete random effects on *typical* movement | error-corrected regression parameters | missing positions |
| **key assumption** | maximal efforts occur; exposure equal | maximal effort in each speed bin; linear profile | quantile of observed data = feasibility | 0.95 quantile ≈ limit | u i.i.d. with known shape; v Gaussian | physics form correct; observed movement informative about limits | linear-Gaussian dynamics, known or estimated noise | exchangeable athletes; parametric likelihood | known additive covariate error variance | training distribution = target |
| **sparse observations** | poor: biased low, high variance | poor: needs many sessions (≈ 2 matches reported, S) | n/a (population) | ? (needs per-athlete data) | moderate (pooled), no athlete hierarchy in the basic form | ? | per path, fine | **good** (partial pooling) | depends on the model | fine for positions |
| **context** | none | reported, not modelled (session type, position) | via features | via features (blockers, S) | via covariates x | via initial state | none | **yes** (covariates, random effects) | none | implicit |
| **measurement error** | none; the tail is noise-inflated | heuristic outlier removal (DBSCAN, 3σ) | not modelled (tail errors noted, S) | ? | v term (symmetric noise) | ? | **yes**, explicit | via the likelihood | **yes**, for covariates | implicit |
| **exposure / opportunity** | ignored (bias grows or shrinks with opportunities) | ignored | ignored | ? | partly: u captures sub-maximality, but not that the *number* of draws changes the expected maximum | ignored | n/a | not targeted | n/a | n/a |
| **uncertainty per athlete** | none (bootstrap possible) | repeated sub-fits | quantile model uncertainty ? | ? | asymptotic SEs | ? | posterior state covariance | **full posterior** | sandwich / bootstrap | sample diversity |
| **unseen athletes** | impossible | impossible | **yes** (population) | no | via covariates | via population parameters | n/a | **yes** (prior from covariates) | n/a | yes |
| **external validation of "capacity"** | sometimes vs sprint tests (S) | vs sprint or radar tests (A/S) | physics baselines (S) | ? | none typical | arrival-region fit (S) | none | posterior predictive | simulation | L2 or realism |

## 3. Strongest existing approaches (by sub-problem)

| sub-problem | strongest approach found | why | what it does not do (our reading) |
|---|---|---|---|
| athlete speed or acceleration capacity from routine tracking | **M2**, in-situ A–S profiling (Morin 2021; Miguens 2024) | established, validated reliability, open code | exposure and effort are not modelled; outlier removal is heuristic; no pooling across athletes; context dependence is shown but uncorrected |
| feasibility envelope from tracking | **M3a** (Gutiérrez-Pérez & Agudo 2026) | beats six physics motion models (S); multi-sport | population envelope, not athlete capacity (to be verified in full text) |
| separating capacity from realised effort | **M3b** (Shteynberg 2025) and **M4** (SFA) | an explicit limit-versus-realised split | M3b is not peer-reviewed and has no uncertainty (?); M4 has no athlete hierarchy or exposure (basic form) |
| sparse athletes, uncertainty | **M7** hierarchical Bayes | partial pooling and posterior uncertainty; already used on NFL movement | targets typical movement, not a boundary or capacity (to be verified for Nguyen & Yurko 2026) |
| derivative noise | **M6** Kalman smoothing | principled state-space treatment | noise parameters must be estimated; no capacity constraint |
| inference in crossed designs | Owen pigeonhole / Owen–Eckles bootstrap | consistent and conservative for means | nonlinear variance-component functionals (our ρ) are not verified as covered |

## 4. Conclusions for gap analysis

1. **No class jointly handles the four properties our empirical study showed to matter:**
   - capacity as an upper boundary;
   - exposure-dependent observed maxima;
   - context or role;
   - per-athlete uncertainty with pooling for sparse athletes.
   M2 + M4 + M7 cover pieces. *This is a statement about the methods found, at S/A evidence; see the review's §8.*
2. **External validation is rare.** Capacity estimates from tracking are seldom checked against an independent standardised measurement for the same athletes. The competition data contains one: **combine tracked 40 peak speed for 418 players**, within-position reliability 0.94–0.99 (D3).
3. **For inference in crossed designs, strong prior work exists** (Owen 2007; Owen & Eckles 2012). A contribution there would be incremental, and its novelty is uncertain.
