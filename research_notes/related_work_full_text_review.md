# Phase 8: related-work review (latent movement capacity from noisy, context-dependent tracking)

**Status: the full-text review requested in Task 1 could NOT be completed.**

In this session, no full text, and no publisher abstract page, could be retrieved directly. Every fetch to the hosts that serve the papers failed:
- arxiv.org, export.arxiv.org;
- www.ncbi.nlm.nih.gov, pmc.ncbi.nlm.nih.gov, www.ebi.ac.uk;
- link.springer.com, doi.org;
- repository mirrors.

All failures were DNS errors. The project lead approved adding these hosts to the environment (2026-11-22). The session's page fetcher still failed after the change, and a shell download was refused by the session's permission check. A new session on the updated environment may resolve this. **Until the papers are read in full, every statement below is provisional.**

## 0. Evidence levels (used in every entry)

| code | meaning |
|---|---|
| **F** | full text read: **none in this phase** |
| **A** | abstract read in Phase 1.5 (`literature_review.md`; abstract obtained via PubMed / publisher; DOI verified there) |
| **S** | search-level only (Phase 8): existence, authors, venue, identifier and a summary returned by a web-search engine. This is *secondary*: neither the paper's own abstract page nor its text was read |
| **K** | an established method whose generic formulation is standard textbook knowledge. The formulation shown is the standard form, **not checked against the paper** |

**Rules applied:**
- No finding is attributed to a paper beyond what its evidence level supports.
- Fields that cannot be filled from that evidence are marked "not verified".
- "What remains unsolved" is **our reading** and is labelled as such.

## 1. Athlete speed and acceleration estimation

### 1.1 Morin et al. (2021), in-situ acceleration–speed (A–S) profile

- **Citation:** Morin J-B, Le Mat Y, Osgnach C, Barnabò A, Pilati A, Samozino P, di Prampero PE. *Individual acceleration-speed profile in-situ: a proof of concept in professional football players.* J Biomech 123:110524. [10.1016/j.jbiomech.2021.110524](https://doi.org/10.1016/j.jbiomech.2021.110524).
- **Evidence:** A (Phase 1.5), plus S ([search record](https://lida.sport-iat.de/ta/Record/4070585)).
- **Problem:** estimate an individual's acceleration capacity as a function of speed from routine GPS data, without dedicated sprint tests.
- **Data:** 16 professional football (soccer) players, GPS from several training sessions.
- **Formulation (K + A):**
  - For speeds from 3 m/s in 0.2 m/s bins, keep the maximal acceleration in each bin.
  - Fit the linear profile a_max(v) = A0 − (A0/S0)·v.
  - A0 is the theoretical maximal acceleration; S0 is the theoretical maximal speed.
- **Algorithm:** binning → per-bin maximum (A level reports two maximal points per bin; not verified) → linear regression → extrapolation to A0 and S0.
- **Assumptions:** maximal efforts at every speed occur in the pooled sessions; the profile is linear.
- **Baselines / metrics:** profiles highly linear (R² > 0.98, A level); 2-week reliability reported (A level).
- **Limitations (stated):** not verified (no full text).
- **Unsolved (our reading):**
  - The per-bin maximum is an order statistic. Its expectation depends on how many near-maximal opportunities the athlete had (exposure).
  - There is no model of effort or context.
  - There is no per-athlete uncertainty for A0 and S0 beyond repeated sub-fits.

### 1.2 Miguens et al. (2024), automated in-situ A–S profiling (rugby union)

- **Citation:** *Individual In-Situ GPS-Derived Acceleration-Speed Profiling: Toward Automatization and Refinement in Male Professional Rugby Union Players.* Sports Med Open 10:6. [10.1186/s40798-023-00672-7](https://doi.org/10.1186/s40798-023-00672-7).
- **Evidence:** A (Phase 1.5), plus S ([PMC record](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10784250/); [DOAJ](https://doaj.org/article/d97f3324cc1b4dbfa34e9affffa23c0b)).
- **Problem:** automate and refine Morin-type profiling; quantify measurement error.
- **Data:** 49 professional rugby union players; 51 training sessions and 11 games (S).
- **Formulation:** the linear A–S profile, as in 1.1.
- **Algorithm (S):**
  - DBSCAN marks points with no neighbours in the A–S plane as measurement errors.
  - A 3σ rule handles further outliers.
  - Regression on the cleaned upper points.
  - Repeated sub-fits estimate the error in A0 and S0.
  - Code: [github.com/NthnMgns/acceleration-speed-profiling](https://github.com/NthnMgns/acceleration-speed-profiling).
- **Metrics / results (A + S):**
  - All profiles near-linear (r² > 0.81).
  - 2-week ICC 0.72–0.92.
  - A0 highest in games and S0 highest in speed sessions, i.e. the estimates depend on session type and position.
- **Unsolved (our reading):**
  - The dependence of A0/S0 on session type is the exposure/context confound in direct form. It is reported, not modelled.
  - Outlier removal is heuristic.
  - Uncertainty comes from resampling only the athlete's own data, with no pooling across athletes.

### 1.3 Clark et al. (2019), combine 40 velocity curves

- **Citation:** *The NFL combine 40-yard dash: how important is maximum velocity?* JSCR 33(6):1542–1550. [10.1519/JSC.0000000000002081](https://doi.org/10.1519/jsc.0000000000002081).
- **Evidence:** A (Phase 1.5), plus S ([record](https://lida.sport-iat.de/ta/Record/4054398)).
- **Formulation (K):** v(t) = v_max(1 − e^(−t/τ)), fitted to the 9.1 / 18.3 / 36.6-m split times of the 2016 combine.
- **Results (A):**
  - v_max correlates with the split times (r = 0.72, 0.83, 0.94).
  - τ is similar in fast and slow groups.
- **Unsolved (our reading):** this is a three-point curve reconstruction. It uses no tracking data and gives no link to game movement.
  - *Our own Phase 2 analysis* fitted the same model to full combine tracking.

### 1.4 Samozino et al. (2016), macroscopic sprint inverse dynamics

- **Citation:** Scand J Med Sci Sports 26:648. [10.1111/sms.12490](https://doi.org/10.1111/sms.12490).
- **Evidence:** A.
- **Content:** force–velocity–power estimates from spatiotemporal sprint data, validated against force plates (bias < 5 %, A level).
- **Unsolved (our reading):** it requires an all-out sprint with a known start. Game movements are not such sprints.

### 1.5 GNSS / LPS validity for acceleration (background)

- **Evidence:** S. Narrative and scoping reviews:
  - [Applied Sciences 2024 review](https://www.mdpi.com/2076-3417/14/22/10573);
  - [BMJ Open SEM scoping review](https://bmjopensem.bmj.com/content/6/1/e000794);
  - 5/10 Hz validation studies ([PubMed 22122431](https://pubmed.ncbi.nlm.nih.gov/22122431/)).
- **Content (S):** errors in acceleration and deceleration grow with acceleration magnitude and are worst for change of direction. Sampling rate ≥ 10 Hz and smoothing reduce the error.
- **Relevance:**
  - Game tracking here is 10 Hz optical/RFID, not GNSS. Its error model is not verified by these reviews.
  - *Our own Phase 1–2 data facts:* double-differentiated acceleration is noisy; implausible game A0 values grow with exposure.

### 1.6 Match peak speed vs maximal sprint speed (background)

- **Evidence:** S. Soccer studies:
  - [PMC11694206](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11694206/);
  - [research.ed.ac.uk record](https://www.research.ed.ac.uk/en/publications/to-measure-peak-velocity-in-soccer-let-players-sprint-peak-veloci/);
  - [Djaoui et al. (record)](https://researchgate.net/profile/Leo-Djaoui/publication/309232669_Maximal_Sprinting_Speed_of_Elite_Soccer_Players_During_Training_And_Matches/links/59c4cb5a0f7e9bd2c004ebe3/Maximal-Sprinting-Speed-of-Elite-Soccer-Players-During-Training-And-Matches.pdf).
- **Content (S, secondary):**
  - Match peak speed is typically below test maximal speed: one study reports about 92 %.
  - Match peaks come from flying starts.
  - Reaching the maximum requires suitable match situations, and depends on position.
- **Relevance:** this is direct support for the *exposure and opportunity* problem. It is not quantified as an estimation model in any work found.

## 2. Latent physical capacity, frontiers and effort

### 2.1 Gutiérrez-Pérez & Agudo (2026), motion feasibility via quantile regression

- **Citation:** *Learning Human Sports Motion Feasibility via Quantile Regression on Tracking Data.* arXiv 2610.36183.
- **Evidence:** S ([arXiv](https://arxiv.org/abs/2610.36183)); code reported at github.com/mguti97/TTA-Quantile.
- **Problem (S):** time-to-arrival (TTA), the shortest plausible time for a player to reach a location given the current kinematic state.
- **Data (S):**
  - PFF FC World Cup 2022 (64 matches, 30 fps);
  - plus NBA SportVU 2015–16 and one NFL Big Data Bowl 2019 game.
- **Formulation (S + K):**
  - Conditional quantile regression of locomotion time at a very low quantile, τ = 0.01 (a "lower envelope"), minimising the pinball loss ρ_τ(u) = u(τ − 1{u < 0}).
  - A lightweight MLP.
- **Baselines (S):** six player-motion models from the literature, plus a learned reachable-hull baseline. The MLP reportedly beats all physics baselines; cross-sport transfer is asymmetric.
- **Assumptions / limitations:** not verified. The search summary notes that tracking errors cluster in the fast tail, exactly where the model is fitted.
- **Unsolved (our reading; must be checked against the full text):**
  - The estimand appears to be a **population** (feature-conditional) feasibility envelope, not an athlete-specific latent capacity.
  - Exposure, effort and per-athlete uncertainty are not described in the material seen.
- **This is the closest recent work. It must be read in full before any novelty claim.**

### 2.2 Shteynberg, Snavely & Solorzano (2025), effort in NFL running backs (student report, not peer-reviewed)

- **Citation:** *Tracking the Intangible: Quantifying Effort in NFL Running Backs.* CMU SURE program report and poster.
- **Evidence:** S ([report](https://eshteynberg.github.io/Football-Effort/report); [poster](https://www.stat.cmu.edu/cmsac/sure/2025/showcase/football_effort/poster.pdf)). The host was unreachable for reading.
- **Problem (S):** estimate each running back's A–S limit from tracking, and measure how often the player operates near it as an effort proxy.
- **Data (S):** Big Data Bowl 2025, 2022 weeks 1–9, 10 Hz; 69 running backs with ≥ 20 carries.
- **Formulation (S):**
  - Quadratic quantile regressions for the 0.95 quantiles of acceleration and deceleration as functions of speed;
  - a quantile GAM.
- **Stated motivation (S):** the soccer in-situ method gives no credit for low-speed plays, penalises athletic players, and does not separate acceleration from deceleration.
- **Unsolved (our reading):** this is the closest *football* precedent for separating capacity from realised effort. Opportunity and exposure, context and uncertainty are not verified. It is not peer-reviewed.

### 2.3 Stochastic frontier analysis (SFA)

- **Citation:** Aigner D, Lovell CAK, Schmidt P (1977). *Formulation and estimation of stochastic frontier production function models.* J Econometrics 6(1):21–37. [10.1016/0304-4076(77)90052-5](https://doi.org/10.1016/0304-4076(77)90052-5).
- **Evidence:** S + K ([IDEAS](https://ideas.repec.org/a/eee/econom/v6y1977i1p21-37.html)).
- **Formulation (K):** y_i = f(x_i; β) + v_i − u_i, with v ~ N(0, σ_v²) noise and u ≥ 0 a one-sided "inefficiency" (half-normal or exponential). Estimated by maximum likelihood.
- **Relevance (our reading):** capacity = frontier; effort or opportunity = u.
  - Classical SFA treats u as i.i.d. with a fixed distribution.
  - It has no hierarchical athlete-level frontier, no context-dependent u, and no exposure-driven order statistics.
  - Panel SFA variants exist but were **not reviewed** here.

### 2.4 Order-α (partial) quantile frontiers and extreme-value frontier estimation

- **Citations:**
  - Aragon, Daouia & Thomas-Agnan (2005);
  - Daouia & Ruiz-Gazen (2006), Statistica Sinica 16:1233–1253 ([pdf](https://www3.stat.sinica.edu.tw/statistica/oldpdf/A16n48.pdf));
  - Daouia, Florens & Simar (2010), Bernoulli;
  - the R package *npbr* ([vignette](https://vps.fmvz.usp.br/CRAN/web/packages/npbr/vignettes/npbrvignette.pdf)).
- **Evidence:** S.
- **Formulation (S + K):**
  - Partial frontier = the α-quantile of Y given X, which tends to the full frontier as α → 1.
  - It is robust to outliers, unlike envelope (free disposal hull, FDH) estimators.
  - Extreme-value theory gives the asymptotics as α → 1.
- **Relevance (our reading):**
  - This is a robust statistical vocabulary for "capacity = upper boundary".
  - It is developed for production frontiers with i.i.d. units, not for per-athlete boundaries pooled hierarchically with an exposure-dependent number of draws.

## 3. Context-dependent movement modelling

### 3.1 Brefeld, Lasek & Mair (2019), probabilistic movement models and zones of control

- **Citation:** Machine Learning 108:127–147. [10.1007/s10994-018-5725-1](https://doi.org/10.1007/s10994-018-5725-1).
- **Evidence:** S ([Leuphana record](https://fis.leuphana.de/en/publications/probabilistic-movement-models-and-zones-of-control/); [mlanthology](https://mlanthology.org/mlj/2019/brefeld2019mlj-probabilistic)).
- **Content (S):**
  - Estimates **individual** movement models from positional data, replacing deterministic reachable regions.
  - Turns them into probabilistic zones of control (soccer).
  - "Accounts for characteristic traits of players"; scalable.
- **Unsolved (our reading; not verified):** whether the movement model separates capacity from effort or context, and its uncertainty per player.

### 3.2 Narizuka, Takizawa & Yamazaki (2023), validating a sprint motion model with tracking data

- **Citation:** Sci Rep. [10.1038/s41598-023-27999-1](https://doi.org/10.1038/s41598-023-27999-1); arXiv 2205.04511.
- **Evidence:** S ([PMC record](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9845223/)).
- **Content (S):**
  - Tests the Fujimura–Sugihara physical motion model (arrival regions) against soccer tracking.
  - The arrival boundary is circular, and depends on initial speed as the model predicts.
  - Proposes estimating the model's kinetic parameters from tracking data.
- **Unsolved (our reading):** estimation from observed (sub-maximal) movement inherits the exposure problem. Per-player uncertainty is not verified.

### 3.3 Spearman (2018), pitch control; da Silva et al. (2025), player-specific top speed

- **Evidence:** S.
- **Spearman (2018):** a physics-based arrival-time model with a logistic arrival-time uncertainty (implementation constant 0.45; [code](https://www.github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking/blob/master/Metrica_PitchControl.py)). Reaction-time and max-speed details are not verified.
- **da Silva et al. (2025)**, Sci Rep [10.1038/s41598-025-22778-6](https://doi.org/10.1038/s41598-025-22778-6) ([arXiv 2504.18250](https://arxiv.org/abs/2504.18250)):
  - Assigns each player a **top speed measured from match tracking**.
  - Scales it with a "stamina factor"; reports role effects (defenders accrue the most pitch control).
- **Unsolved (our reading):** match-measured top speed is used as if it were capacity, which is the exposure-biased quantity.

### 3.4 Nguyen & Yurko (2025), Bayesian circular mixed-effects model of NFL turn angles

- **Citation:** arXiv 2507.06122.
- **Evidence:** S ([arXiv](https://arxiv.org/abs/2507.06122v1); [project page](https://cmsac-research-lab.github.io/papers/nfl-cod/nfl-cod.html)).
- **Formulation (S):**
  - A von Mises model for ball-carrier turn angles.
  - Mean and concentration both depend on spatiotemporal and contextual covariates.
  - Player random effects on concentration, nested in position.
  - Data: 2022 weeks 1–9.
- **Relevance:** hierarchical Bayesian modelling of *realised* directional movement with context and player effects. It does not target maximal capacity (our reading).

### 3.5 Nguyen & Yurko (2026), Bayesian multilevel step-and-turn models

- **Citation:** arXiv 2603.17866, *NFL step-and-turn: A generative framework for evaluating player movement in American football*.
- **Evidence:** S ([arXiv](https://arxiv.org/abs/2603.17866v1); [project page](https://cmsac-research-lab.github.io/papers/nfl-step-turn/nfl-step-turn.html)).
- **Formulation (S):**
  - Frame-level multilevel models for step length and turn angle.
  - Posterior predictive simulation of hypothetical ball-carrier steps.
  - Evaluation of observed movement against simulated alternatives.
  - Data: 2022 weeks 1–9.
- **Relevance (our reading):**
  - This is the closest NFL **hierarchical generative movement model**, with player-level random effects and context.
  - Whether it models an upper capacity (a feasible-step boundary) or only typical steps is **not verified**.
  - **It must be read in full before any novelty claim.**

## 4. Sports tracking trajectory analysis (NFL)

### 4.1 Chu, Reyers, Thomson & Wu (2020), route identification

- **Citation:** JQAS; arXiv 1908.02423.
- **Evidence:** A (Phase 1.5) + S ([arXiv](https://arxiv.org/abs/1908.02423v1)).
- **Formulation (S):** model-based curve clustering. A Gaussian mixture with Bernstein-polynomial cluster centres, fitted by EM, on 34,698 routes.
- **Relevance:** context labelling (route type). Not capacity.

### 4.2 Yurko et al. (2020), "Going Deep"

- **Citation:** JQAS 16(2):163–182, [10.1515/jqas-2019-0056](https://doi.org/10.1515/jqas-2019-0056); arXiv 1906.01760.
- **Evidence:** S.
- **Formulation (S):** an LSTM for the expected end-of-play yard line, plugged into expected-points and win-probability models.
- **Relevance:** valuation, not capacity.

### 4.3 Big Data Bowl winners and finalists (competition work, not peer-reviewed)

- **Evidence:** S ([2019 recap](https://operations.nfl.com/the-game/big-data-bowl/2019-big-data-bowl); [2020 recap](https://operations.nfl.com/stats-central/stats-articles/2020-big-data-bowl-recap); [Ploenzke 2020](https://operations.nfl.com/media/4204/bdb_ploenzke.pdf); [Ha & Calestini 2019, speed and fatigue](https://operations.nfl.com/media/3673/big-data-bowl-calestini_ha-v2.pdf); [2026 winner news](https://news.rice.edu/news/2026/classroom-combine-champion-rice-student-wins-nfl-analytics-title)).
- **2020:**
  - Winners Singer & Gordeev used a 2D CNN on relative positions, speeds and accelerations at handoff.
  - Finalist Ploenzke found the ball carrier's "effective acceleration" the most important feature.
- **2019 finalist (Ha & Calestini):** speed usage and fatigue.
- **2026:** a movement-prediction leaderboard track. Its winners were not identified.
- **Relevance (our reading):**
  - These works use speed and acceleration as features or outcomes.
  - None found estimates a latent per-player capacity with uncertainty.
  - **Coverage of finalists is incomplete:** no list of all finalists was retrieved.

### 4.4 "Here Comes the STRAIN" (2023) and "Who Blocks Whom?" (2026)

- **Citations:** arXiv 2305.10262; arXiv 2609.33664.
- **Evidence:** S.
- **STRAIN:** a pass-rush metric (distance-rate ratio).
- **"Who Blocks Whom?":** reportedly applies a **Kalman smoother** with latent state (position, velocity, acceleration) to NFL trajectories before modelling (search summary of its appendix).
- **Relevance:** precedent for state-space denoising of NFL kinematics.

## 5. Measurement error and uncertainty quantification

### 5.1 Cook & Stefanski (1994), SIMEX

- **Citation:** JASA 89(428):1314–1328. [10.1080/01621459.1994.10476871](https://doi.org/10.1080/01621459.1994.10476871).
- **Evidence:** S + K. Nonparametric extension: arXiv 2111.02863 (S).
- **Formulation (K):**
  - Add simulated error of variance λσ_u² to the error-prone covariate.
  - Re-estimate θ(λ) over a grid of λ.
  - Extrapolate to λ = −1.
  - This assumes a known (or estimable) additive covariate-error variance.
- **Relevance (our reading):**
  - It addresses error in **covariates**, not the bias of an **upper-tail statistic (a maximum or high quantile) of noisy observations**.
  - Our Phase 1.6 simulations used SIMEX for S0 (it halved the bias).

### 5.2 Hedeker et al. (2008), mixed-effects location-scale model

- **Citation:** Biometrics 64(2):627–634. [10.1111/j.1541-0420.2007.00924.x](https://doi.org/10.1111/j.1541-0420.2007.00924.x).
- **Evidence:** A.
- **Formulation (K + A):** y_ij = x_ij′β + b_i + e_ij, with log σ²_ij = w_ij′τ + ω_i, and the subject-level random scale effect ω_i correlated with b_i.
- **Relevance:** subject-specific variability. Relevant if effort variability is part of the capacity model.

### 5.3 Owen (2007), pigeonhole bootstrap; Owen & Eckles (2012)

- **Citations:**
  - Owen (2007), Ann Appl Stat 1(2):386–411, [10.1214/07-AOAS122](https://doi.org/10.1214/07-AOAS122) (arXiv 0712.1111);
  - Owen & Eckles (2012), Ann Appl Stat 6(3) ([arXiv 1106.2125](https://arxiv.org/pdf/1106.2125)).
- **Evidence:** S.
- **Content (S):**
  - Resample rows and columns of a crossed design independently.
  - Consistent for the mean under heteroscedastic, unbalanced crossed random effects; overestimates the variance (by about twice the naive bias).
  - Citing McCullagh (2000), no bootstrap is exact even for linear statistics.
  - Owen & Eckles: a reweighting bootstrap for arrays with any number of factors, conservative.
- **Relevance:** directly relevant to our documented crossed-design bootstrap over-dispersion (D2). **Much of that problem is already studied.**

### 5.4 Hierarchical shrinkage for sparse athlete data

- **Citation:** *Modelling between- and within-season trajectories in elite athletic performance data.* arXiv 2405.17214 (swimming).
- **Evidence:** S ([arXiv](https://arxiv.org/abs/2405.17214)).
- **Content (S):** a Bayesian hierarchical model with global–local shrinkage priors, which estimates athlete trajectories even with few or no observations in a season.
- **Relevance:** principled borrowing of strength for sparse athletes. The model is about mean performance, not a capacity boundary (our reading).

## 6. Sparse trajectory reconstruction

### 6.1 Liu, Yu, Zheng, Zhan & Yue (2019), NAOMI

- **Citation:** NeurIPS 2019; arXiv 1901.10946.
- **Evidence:** S ([NeurIPS pdf](https://papers.nips.cc/paper/2019/file/50c1f44e426560f3f2cdcb3e19e39903-Paper.pdf)).
- **Content (S):**
  - Non-autoregressive, coarse-to-fine recursive imputation of long sequences, with adversarial training.
  - On basketball (107,146 training sequences), a reported 60 % lower error than autoregressive baselines.
  - The authors note that L2 error is not a good realism measure.
- **Relevance (our reading):** imputation of *positions*. It provides no physical-capacity constraint and no uncertainty about capacity.

### 6.2 SciSports (2018), football kinematics with a Kalman filter

- **Citation:** arXiv 1808.04550.
- **Evidence:** S.
- **Content (S):**
  - Newtonian model with a Kalman filter.
  - Velocity is less noisy than with finite differences.
  - The noise parameters (acceleration variance, measurement error) are unknown and must be estimated.

## 7. Hierarchical and Bayesian athlete modelling

The entries are covered above: 3.4, 3.5, 5.2, 5.4. A Bayesian critical-velocity model ([SFU paper](https://www.sfu.ca/~tswartz/papers/crit_vel.pdf), S) shows priors combined with sparse field data for speed-duration models.

**No work was found that fits a hierarchical (athlete-pooled) model of a *maximal-capacity boundary* in which:**
- the observed in-game maxima are explicitly modelled as exposure-dependent;
- capacity is validated against an independent standardised test for the same athletes.

This is an **absence in our searches, not evidence of absence.** See §8.

## 8. What this review can and cannot support

**It can support:**
- The established approaches are identified (§§1–6), along with their standard formulations.
- The three most relevant recent works are identified, all needing full-text reading:
  - Gutiérrez-Pérez & Agudo 2026 (quantile feasibility envelope);
  - Nguyen & Yurko 2026 (multilevel step-and-turn);
  - Shteynberg et al. 2025 (quantile A–S effort, NFL).
- Prior work supports that match peak speed underestimates maximal sprint speed, and that this depends on situation and position.
- The crossed-design bootstrap issue has substantial prior work (Owen 2007; Owen & Eckles 2012).

**It cannot support:**
- **Any novelty claim.** The CLAUDE.md rule requires full-text reading of the closest work, and none was possible.
- Details of assumptions, baselines, metrics and stated limitations for the S-level entries.
- A complete survey of Big Data Bowl finalists.
- A check of whether panel or hierarchical SFA, or extreme-value methods for athlete maxima, already solve the candidate gap.

**Required next step before Phase 8 can be closed:** in a session where the allowed hosts actually resolve, read in full:
- 2.1, 2.2 and 3.5 (priority 1);
- 1.1, 1.2, 2.3/2.4 and their panel/hierarchical extensions, 3.1 and 3.2 (priority 2);
- then update this file's evidence levels to F.
