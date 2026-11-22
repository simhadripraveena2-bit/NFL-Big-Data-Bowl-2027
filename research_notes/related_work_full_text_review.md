# Phase 8: related-work review (latent movement capacity from noisy, context-dependent tracking)

**Status (Phase 8B, 2026-11-22): the three priority-1 works have now been read in full.** Access was recovered with a shell download through the session proxy (the page fetcher still fails DNS):
- §2.1 Gutiérrez-Pérez & Agudo 2026: complete arXiv HTML main text, plus the authors' code repository.
- §2.2 Shteynberg et al. 2025: the complete one-page poster.
- §3.5 Nguyen & Yurko 2026: complete arXiv HTML, including Appendices A–F.

**Still inaccessible, or not read:**
- the TTA supplement (§A.1–A.4), which is not in the arXiv HTML;
- the Shteynberg written report (eshteynberg.github.io), whose host is not reachable;
- the step-and-turn code repository (not requested);
- every other entry, which stays at its Phase 8 evidence level.

Phase 8B also verified DOIs and, where OpenAlex had them, read the abstracts of the extreme-value and panel-frontier works that bear on G1 (§2.3–2.5).

The downloaded sources were treated as untrusted data: read only, never executed, and not committed.

**Phase 8 header, kept for the record:** in Phase 8 no full text could be retrieved, because of DNS failures for arxiv.org, NCBI/PMC, EBI, Springer and doi.org. Entries not upgraded below remain provisional.

## 0. Evidence levels (used in every entry)

| code | meaning |
|---|---|
| **F** | full text read (Phase 8B): §2.1 main text and code (supplement inaccessible); §2.2 the complete poster (the written report inaccessible); §3.5 the complete paper with appendices |
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

- **Citation:** Marc Gutiérrez-Pérez, Antonio Agudo (Institut de Robòtica i Informàtica Industrial, CSIC-UPC). *Learning Human Sports Motion Feasibility via Quantile Regression on Tracking Data.* arXiv 2610.36183v1 (26 Oct 2026, cs.AI). [arXiv HTML](https://arxiv.org/html/2610.36183); code [github.com/mguti97/TTA-Quantile](https://github.com/mguti97/TTA-Quantile).
- **Publication status:** **preprint.** The repository README states ACCV 2026 acceptance. This was not verified (no proceedings record was checked), so the work is treated as a non-peer-reviewed preprint.
- **Evidence: F** for the main text (§1–5, tables, figures, references) and **code inspected** (see below).
  - **Inaccessible:** Supplementary §A.1 (smoothing windows and kinematic thresholds), §A.2 (closed forms of the six physics baselines), §A.3 and §A.4 (structural-audit protocol). They are referenced but not included in the arXiv HTML. Statements relying on them are marked.
- **Problem:** time-to-arrival (TTA), the minimum plausible time for a player in kinematic state k = (p, v, a) to reach a target x. It is the input that pitch-control and space models need.
- **Estimand (paper, Eq. 1):**
  - τ(g) = Q_0.01(Δt | g(k, x)), the 1st percentile of observed arrival time given the state–target geometry g.
  - In the authors' words, "the conditional lower envelope of arrival times, not a per-observation minimum".
  - Intent, fatigue, tactics and obstacles "all act in the conservative direction", so they are discarded by the low quantile, not modelled.
  - Reachable set: R(Δt) = {x : τ(x) ≤ Δt}.
- **Features:** six heading-frame inputs: d/120, cos θ, sin θ, v/12, a_x/10, a_y/10.
- **Data:**
  - PFF FC World Cup 2022: 64 matches, 30 fps, split by match 45/10/9, about 154M self-supervised samples (five horizons per state, uniform in [0.1, 8] s).
  - NBA SportVU 2015–16: 631 games, 25 fps.
  - NFL BDB 2019: a **single game**, 10 fps, 729,510 samples, split **by player** (within-game).
- **Preprocessing:**
  - Savitzky–Golay smoothing, then finite differences.
  - Exclusion of frames that break hard kinematic bounds (thresholds are in the inaccessible §A.1).
  - Code: a SUVAT label filter (8 m/s², 9 m/s) removes about 0.3 % of samples.
  - The authors state that identity swaps and position jumps "sit precisely at the fast tail from which our τ = 0.01 objective learns".
- **Model and algorithm:**
  - An MLP 6→64→64→1 with ReLU and a Softplus output.
  - Loss: pinball at τ = 0.01, plus a differentiable area-aware term (λ = 0.01, β = 0.25 s, horizons {3, 5} s).
  - Adam (code: LR 1e-3, batch 4096, ≤ 200 epochs, patience 12, seed 42).
- **Personalisation ("player-profile MLP", §3.6):**
  - A 7th input: the player's v_max = **99th percentile of that player's cleaned speeds pooled over the 45 training matches**.
  - This is a plug-in order statistic. It has no shrinkage, no exposure adjustment and no uncertainty.
  - Unseen players get the median (code).
- **Baselines:**
  - Six literature motion models, re-expressed as TTA predictors and refitted with a reachable-area objective at a matched 0.99 correctness gate.
  - The Anzer–Bauer learned reachable hull.
  - A control giving the physics models the same per-player v_max (two-segment + v_max is the "personalised baseline").
- **Metrics:** MAE, RMSE and pinball at τ = 0.01 on held-out matches; reachable area at matched coverage; structural audit (connectedness, star-shapedness, monotonicity).
- **Results (World Cup test split):**
  - MLP MAE 2.596 s; profile MLP 2.577 s.
  - Best physics model 2.883 s; two-segment + v_max 2.900 s; hulls 3.065 s.
  - Profile gain 0.025 s, 95 % CI [0.019, 0.030], from a paired cluster bootstrap over test matches.
  - Personalised physics still trails the profile MLP by 0.30 s.
  - NFL in-domain MAE 1.297 vs 1.608 for two-segment. Cross-sport transfer is asymmetric.
  - Audit: 100 % connected and star-shaped; 1.4 % monotonicity violations.
- **Ablations:** quantile level and area term; profile vs non-profile; physics with vs without v_max.
- **Stated limitations / future work:**
  - "Natural next steps include richer conditioning for player personalization".
  - The code notes that conditional coverage falls below target in sparse far bands when the area term is on.
- **Code inspection (repository cloned, read only, not executed):**
  - Objective: `PINBALL_TAU = 0.01`, `PLAYER_VMAX_PCT = 99.0`.
  - Splits: `SPLIT_MODE` ∈ {match, player, block}.
  - **The canonical `VMAX_SCOPE = "match"` computes the per-player percentile within each match, test matches included.** The config itself calls this "look-ahead leakage". The leakage-free `"train_split"` scope is the one the paper describes. *Which scope produced the published numbers was not determined from the code.*
  - A comment names "cameo players whose 99th percentile rests on a handful of frames", i.e. the authors note the exposure problem informally without modelling it.
  - An a_max profile was removed for "no between-player spread".
  - Stale documentation: the README says the 95th percentile, and the `loss.py` docstring says τ = 0.05.
- **Relation to G1 (our reading, F-level):**
  - **Solves:** a population, feature-conditional *feasibility envelope* by conditional quantile regression, with strong physics baselines and held-out evaluation.
  - **Does not address:**
    - a latent per-athlete capacity as the estimand: per-player v_max is an *input*, taken as known;
    - exposure or opportunity: the 99th percentile is exposure-naive, and "cameo" players are acknowledged only in a code comment;
    - hierarchical shrinkage, or per-athlete uncertainty;
    - separating capacity from effort or context: these are absorbed by the low quantile;
    - validation of any capacity quantity against an independent measurement.

### 2.2 Shteynberg, Snavely & Solorzano (2025), effort in NFL running backs (student poster, not peer-reviewed)

- **Citation:** Emily Shteynberg (NYU), Luke Snavely (Robert Morris), Sheryl Solorzano (Amherst). *Tracking the Intangible: Quantifying Effort in NFL Running Backs.* CMU Statistics & Data Science SURE 2025 showcase poster. [poster pdf](https://www.stat.cmu.edu/cmsac/sure/2025/showcase/football_effort/poster.pdf).
- **Publication status:** **undergraduate summer research poster.** Not peer-reviewed, and not a paper.
- **Evidence: F for the poster** (one page, read in full).
  - **Inaccessible:** the written report at eshteynberg.github.io/Football-Effort/report, whose host is not reachable. Any details only in the report (code, exact QGAM settings, uncertainty) are unknown.
- **Problem:** an objective *effort* measure for running backs, defined as how often a player comes close to, or exceeds, **their own** A–S frontier.
- **Data:** BDB 2025, 2022 weeks 1–9, 136 games, 10 fps. Running plays with an RB ball carrier; RBs with ≥ 20 runs (69 RBs).
- **Formulation:**
  - The starting point is Morin 2021 (in-situ A–S, with S0/A0). The poster lists its drawbacks: no credit for low-speed points; unrealistic theoretical max speeds; "players are penalized for being athletic" (high-A0 players get a low % of effortful points); no separation of acceleration and deceleration.
  - **Metric 1:** per-player quadratic quantile regressions at τ = 0.95 for acceleration and for deceleration as functions of speed.
    - d_i = vertical distance from each point to its curve; d_i = 0 for points beyond the curve.
    - Ψ_i = 1/(1 + d_i) for acceleration, and ½ · 1/(1 + d_i) for deceleration (deceleration "deemed less effortful", citing Hader 2016).
    - Effort = mean of Ψ over frames.
  - **Metric 2:** the same with QGAMs (adaptive splines) at 0.95.
- **Baselines / validation:** the two metrics against each other (positively correlated). Correlation with play outcomes: QGAM effort vs YAC −0.081, EPA −0.103, rushing yards −0.079. Mean speed correlates 0.38–0.52.
- **Results:**
  - "Back-up RBs consistently lead in both effort metrics." The authors' explanations: more out of limited opportunities, less fatigue, or starters not needing to exert as much.
  - Effort metrics do not correlate with outcomes.
- **Stated limitations:** the model "does not fully account for in-play context"; individualised A–S curves "hold players to different standards → limits cross-player comparison".
- **Uncertainty:** none reported.
- **Relation to G1 (our reading, F-level for the poster):**
  - Capacity is a **per-player, independently fitted 0.95 quantile curve**: no pooling, no exposure model, no uncertainty, no external validation.
  - The backup-RB result is exactly the pattern an exposure artefact would produce. Players with fewer frames have quantile curves fitted to fewer points, so more points lie near or above them. The poster does not test this explanation, and we do not claim it is the cause.
  - **It addresses a different estimand (effort), and leaves the capacity estimand unsolved.**

### 2.3 Stochastic frontier analysis (SFA)

- **Citation:** Aigner D, Lovell CAK, Schmidt P (1977). *Formulation and estimation of stochastic frontier production function models.* J Econometrics 6(1):21–37. [10.1016/0304-4076(77)90052-5](https://doi.org/10.1016/0304-4076(77)90052-5).
- **Evidence:** S + K ([IDEAS](https://ideas.repec.org/a/eee/econom/v6y1977i1p21-37.html)).
- **Formulation (K):** y_i = f(x_i; β) + v_i − u_i, with v ~ N(0, σ_v²) noise and u ≥ 0 a one-sided "inefficiency" (half-normal or exponential). Estimated by maximum likelihood.
- **Relevance (our reading):** capacity = frontier; effort or opportunity = u.
  - Classical SFA treats u as i.i.d. with a fixed distribution.
  - It has no hierarchical athlete-level frontier, no context-dependent u, and no exposure-driven order statistics.
- **Panel / random-effects / determinants extensions (Phase 8B; DOIs verified via Crossref; no abstract available through OpenAlex, so evidence S + K):**
  - Battese & Coelli (1995), Empirical Economics 20:325, [10.1007/BF01205442](https://doi.org/10.1007/BF01205442). K: the mean of the one-sided u depends on covariates ("inefficiency determinants"), i.e. **a context-dependent deficit is standard**.
  - Koop, Osiewalski & Steel (1997), J Econometrics 76:77, [10.1016/0304-4076(95)01783-6](https://doi.org/10.1016/0304-4076(95)01783-6). K: Bayesian frontier with individual effects, i.e. **posterior per-unit uncertainty with hierarchical priors is standard**.
  - Greene (2005), J Econometrics 126:269, [10.1016/j.jeconom.2004.05.003](https://doi.org/10.1016/j.jeconom.2004.05.003). K: "true random effects" SFA, separating a unit-level heterogeneity term from inefficiency.
- **Consequence for G1 (our reading):** a frontier with a per-athlete random level, a covariate-dependent one-sided deficit, and Bayesian per-athlete intervals is an **existing model class**. It does not by itself model an *exposure-dependent number of draws*.

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
- **Boundary estimation with observation error (Phase 8B):**
  - Hall & Simar (2002), JASA 97:523, [10.1198/016214502760047050](https://doi.org/10.1198/016214502760047050). **Evidence A** (abstract via OpenAlex).
    - With additive error of variance σ², frontier estimates are biased at order σ. A simple method reduces this to O(σ²).
    - The frontier "is generally not even identifiable unless the error distribution is known".
  - Kneip, Simar & Van Keilegom (2015), J Econometrics 184:379, [10.1016/j.jeconom.2014.09.012](https://doi.org/10.1016/j.jeconom.2014.09.012). **Evidence S** (DOI verified; title only): frontier estimation with measurement error of unknown variance.
  - **Consequence:** the noise-inflated-tail problem (spikes, identity swaps) in boundary estimation is a studied problem, with a known identifiability limit.

### 2.5 Extreme-value theory for athlete performance (Phase 8B)

- **Einmahl & Magnus (2008)**, *Records in athletics through extreme-value theory.* JASA 103:1382, [10.1198/016214508000000698](https://doi.org/10.1198/016214508000000698). **Evidence A.**
  - Estimates the **ultimate (endpoint) performance** per event from all top performances, with nonparametric EVT, and derives limiting distributions.
- **Spearing, Tawn, Irons, Paulden & Bennett (2021)**, *Ranking, and other properties, of elite swimmers using extreme value theory.* JRSS A 184:368, [10.1111/rssa.12628](https://doi.org/10.1111/rssa.12628) (correction 2025, [10.1093/jrsssa/qnae154](https://doi.org/10.1093/jrsssa/qnae154)). **Evidence A.**
  - Best swim times are modelled "through their **rate of occurrence**", with a GPD for the best times.
  - The GPD parameters vary with covariates (event, date, technology), and information is shared across events.
  - It estimates the "ultimate possible time".
- **Consequence for G1 (our reading, A level):**
  - Covariate-dependent point-process / GPD models of the best performances, which explicitly model *how often* performances occur, together with endpoint estimation, are **established**.
  - What we did not find (absence in search, not evidence of absence):
    - an application to *per-athlete* endpoints from within-game tracking, with athlete-level random effects;
    - validation against an independent test of the same athletes.
  - A full-text check would be needed to see whether Spearing et al. include athlete-level effects. The abstract describes event-level covariates.

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

- **Citation:** Quang Nguyen, Ronald Yurko (Carnegie Mellon University). *NFL step-and-turn: A generative framework for evaluating player movement in American football.* arXiv 2603.17866. [arXiv HTML](https://arxiv.org/html/2603.17866); code stated at github.com/qntkhvn/nfl-step-turn (**not inspected**).
- **Publication status:** **preprint** (arXiv). No journal version was identified.
- **Evidence: F.** The complete HTML was read: §1–5, Appendices A–F, references. Figures were seen only through captions and surrounding text.
- **Problem:** evaluate ball-carrier movement frame by frame, by comparing the observed next step with posterior-predictive hypothetical next steps, valued by an expected end-of-play yard line model.
- **Data:** BDB 2025, 2022 weeks 1–9; 5,400 run plays, 136 games; ball-carrier sequences from handoff to tackle, out of bounds or touchdown; RBs with ≥ 70 rushes for the leaderboards.
- **Formulation:**
  - **Step length** s_ijt (distance between successive 10 Hz positions, i.e. speed × 0.1 s), scaled-arcsine transformed:
    - s̃_ijt ~ N(μ, σ²), with μ = α + X β + u_j + v_k;
    - u_j ~ N(0, τ_u²) is a ball-carrier random intercept, and v_k ~ N(0, τ_v²) a defensive-team random intercept;
    - X contains ball-carrier and closest-defender features, player counts per direction, and the **lagged step length**.
  - **Turn angle:** von Mises, with a tan-half link on the mean and log κ = γ0 + γ1 s_ijt + w_j (a player random effect on concentration).
  - Fitting: Bayesian, with brms/Stan (NUTS; 4 chains × 5,000 iterations with 2,500 warm-up). Priors: half-t3 on the SDs, defaults elsewhere.
- **Simulation and evaluation:**
  - One-step-ahead posterior predictive draws (H = 100), with a *new* random effect for a generic player (Appendix F: the player's own effect).
  - Other players are held fixed.
  - Valued by a CatBoost multinomial end-of-play yard line model (grouped 5-fold CV by game, Appendix E).
  - Metrics: δ̄ (yards vs the hypothetical), yards success rate, explosiveness (the frame-level outcome above the 95th percentile of hypotheticals).
- **Validation:**
  - Posterior predictive checks of the step-length distribution: arcsine vs Gamma vs log-normal (Appendix A).
  - MCMC diagnostics (Appendix B); prior sensitivity, with rankings unchanged (Appendix C).
  - Face validity of the leaderboards against scouting descriptions.
  - **No held-out predictive validation of the movement models, and no external measurement.**
- **Stated limitations:**
  - One-step simulation only, with other players fixed: full forward simulation would need a tackle model and multi-agent movement, and fixing other players biases simulation.
  - Nine weeks of data.
- **Relation to G1 (our reading, F level):**
  - **Solves, for NFL tracking:** player random effects with partial pooling and full posterior uncertainty for a speed-like quantity (step length), conditional on frame-level context and opponent.
  - **What it estimates is the conditional *mean* (transformed) step length**, i.e. typical speed given context. It is not an upper boundary or capacity, and the paper does not claim one.
  - u_j is a "long strides" trait, confounded with role and usage (e.g. the Jonathan Taylor vs McCaffrey discussion).
  - No exposure model, no external validation. The Gaussian mean model is the natural "hierarchical mean" baseline for G1, now with a concrete NFL precedent.

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

**Phase 8B revision.** Each ingredient of such a model is now verified as existing:
- hierarchical athlete effects with posterior uncertainty on NFL speed-like movement: §3.5, F;
- conditional low or high quantile envelopes: §2.1 and §2.2, F;
- covariate-dependent one-sided deficits and random-effect frontiers: §2.3, S/K;
- boundary estimation with observation error: §2.4, A;
- rate-of-occurrence (exposure-aware) EVT for best performances, with covariates and endpoint estimation: §2.5, A.

**No work was found that applies these jointly to per-athlete game-tracking speed capacity and validates the result against an independent standardised test of the same athletes.** This is an absence in our searches, not evidence of absence. Because the ingredients exist, assembling them is **not** treated as an algorithmic contribution (see `algorithmic_research_gaps.md`).

## 8. What this review can and cannot support (revised in Phase 8B)

**It can support:**
- At F level: none of the three closest recent works estimates a per-athlete latent speed capacity with exposure modelling, pooling and uncertainty, or validates one externally.
  - §2.1 uses an exposure-naive 99th-percentile v_max as a known input.
  - §2.2 fits independent per-player 0.95 quantile curves to measure effort.
  - §3.5 estimates a hierarchical *mean* step length.
- At A/S/K level: the statistical ingredients of G1 already exist in the frontier and EVT literatures (§2.3–2.5). A G1 that only combines them is not an algorithmic contribution.
- Match peak speed underestimates maximal sprint speed, depending on situation and position (S).
- The crossed-design bootstrap issue has substantial prior work (Owen 2007; Owen & Eckles 2012; S).

**It cannot support:**
- **Any novelty claim.** Absence of an application in our searches is not evidence that none exists, and the priority-2 works are still not read in full.
- Claims about the TTA supplement (§A.1–A.4), the Shteynberg written report, or the step-and-turn code.
- Whether Spearing et al. 2021 include athlete-level effects, or whether panel SFA papers model the number of draws (abstract or title only).
- A complete survey of Big Data Bowl finalists.

**Remaining full-text gaps (priority 2):**
- 1.1, 1.2, 2.3 (Greene 2005, Koop et al. 1997, Battese & Coelli 1995);
- 2.4 (Hall & Simar 2002, Kneip et al. 2015);
- 2.5 (Spearing et al. 2021, Einmahl & Magnus 2008);
- 3.1, 3.2.
