# Phase 8C: final novelty audit, opportunity-conditioned speed capacity

**Status:** literature audit only. Nothing was implemented, fitted or changed in the empirical study or the preregistration. The downloaded sources and code were treated as untrusted: read, never executed, and not committed.

**Central question.** Can a player's *attainable* speed be estimated conditional on the movement opportunity a particular play provided? Opportunity here means available acceleration distance, play duration, direction, turning constraints and task. And can a player's underlying speed capacity be told apart from that opportunity?

## 1. Access and evidence levels

| code | meaning |
|---|---|
| F | full text read |
| F-code | source code read (not executed) |
| P | partial full text (the sections read are listed) |
| A | abstract read |
| S | secondary description only (search result, glossary) |
| K | standard textbook formulation, not checked against the paper |

**Access in Phase 8C:**
- Five repository hosts were added to the environment allowlist (KU Leuven Lirias, ANU, UCLouvain DIAL, NYU Stern, Tilburg).
- Retrieval outcomes:
  - Spearing et al.: arXiv PDF retrieved.
  - Hall & Simar: the ANU copy is **restricted** (request-a-copy only).
  - Greene 2005 and Koop et al. 1997: **closed access**; OpenAlex lists no repository copy, and the Greene and Tilburg pages hold no PDF.
  - Kneip et al. 2015: the Lirias download was still refused after the allowlist change.
  - The step-and-turn repository was cloned.

| # | work | type | evidence | not accessible |
|---|---|---|---|---|
| 1 | Spearing, Tawn, Irons, Paulden & Bennett (2021), JRSS A 184:368, [10.1111/rssa.12628](https://doi.org/10.1111/rssa.12628) | peer-reviewed article | **F**: arXiv 1910.10070v2 (22 Jun 2020), all sections + appendix | journal typeset version; 2025 correction ([10.1093/jrsssa/qnae154](https://doi.org/10.1093/jrsssa/qnae154)) |
| 2 | Greene (2005), J Econometrics 126:269, [10.1016/j.jeconom.2004.05.003](https://doi.org/10.1016/j.jeconom.2004.05.003) | peer-reviewed article | **K** only (DOI verified; closed access) | full text, abstract |
| 3 | Koop, Osiewalski & Steel (1997), J Econometrics 76:77, [10.1016/0304-4076(95)01783-6](https://doi.org/10.1016/0304-4076(95)01783-6) | peer-reviewed article | **K** only (DOI verified; closed access) | full text, abstract |
| 4 | Hall & Simar (2002), JASA 97:523, [10.1198/016214502760047050](https://doi.org/10.1198/016214502760047050) | peer-reviewed article | **A** | full text (repository copy restricted) |
| 4b | Kneip, Simar & Van Keilegom (2015), J Econometrics 184:379, [10.1016/j.jeconom.2014.09.012](https://doi.org/10.1016/j.jeconom.2014.09.012) | peer-reviewed article | **S** (title, DOI) | full text (host refused) |
| 5 | Nguyen & Yurko (2026), arXiv 2603.17866; code [github.com/qntkhvn/nfl-step-turn](https://github.com/qntkhvn/nfl-step-turn) | preprint + code | **F** (paper, Phase 8B) + **F-code** (all 12 R scripts) | — |
| 6a | Lee (2026), *Modelling athletic ageing relative to an estimated performance envelope* (RACE), arXiv 2608.06635v2 | preprint | **P**: abstract, §1, §2.1–2.2, §3, §4, §6.1, §7 | §2.3–2.4, §5, §6.2–6.5 and appendices not read |
| 6b | Postma, Wieling, Lemmink & Zaal (2022), *Distance over time in a maximal sprint: understanding athletes' action boundaries in sprinting*, Ecol Psychol, [10.1080/10407413.2022.2120397](https://doi.org/10.1080/10407413.2022.2120397) | peer-reviewed article | **A** | full text |
| 6c | MLB Statcast *Sprint Speed* ([glossary](https://www.mlb.com/glossary/statcast/sprint-speed)) | industry metric definition | **S** | method documentation beyond the glossary |
| 6d | Gyarmati & Hefeeda (2015), *Estimating the maximal speed of soccer players on scale*, MLSA@ECML-PKDD, CEUR 1970:96 | workshop paper | **S** (bibliographic record and summary) | full text (host not allowed) |
| 6e | Match peak speed vs sprint distance (soccer GPS studies, e.g. [PMC11167479](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11167479/)) | peer-reviewed articles | **S** | full texts |
| 6f | In-situ / GPS acceleration–speed and force–velocity profiling validity (e.g. [PMC11478346](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11478346/), [PMC12136470](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12136470/)) | peer-reviewed articles | **S** | full texts |
| — | Phase 8B works: TTA (Gutiérrez-Pérez & Agudo 2026), Shteynberg 2025 poster, Morin 2021, Miguens 2024, Clark 2019 | — | as in `related_work_full_text_review.md` | as recorded there |

## 2. Findings per work

### 2.1 Spearing et al. (2021): F

**Model:**
- Event-level non-homogeneous Poisson point process for the best swim times (negated) above a threshold u_e (the 200 best per event).
- Intensity λ(t, x) has GEV parameters µ(t), σ(t) that vary linearly with time, plus swimsuit indicators. The shape ξ is shared across events.
- Parameters are pooled across 34 events through smooth functions of the threshold time (a monotone P-spline for the GPD scale).
- Interval censoring for 0.01 s rounding.

**What "exposure" means here:**
- The **rate of occurrence** of exceedances per year. It absorbs both genuine improvement and database coverage (more competitions recorded in later years).
- Exposure is **not** athlete-specific. The data keep only the **fastest time per swimmer per event**. Swims are assumed independent even when they come from the same swimmer; the authors bound the variance understatement by a factor of 2.

**Estimands:**
- r-value ranking of individual swims: the rate of better swims;
- event-level endpoints (an "ultimate time", via ξ̂ = −0.147 < 0);
- next world-record distribution and waiting times;
- swimsuit-adjusted times.

**Validation:** pooled PP plots, observed vs expected annual exceedance rates, parametric bootstrap (250 datasets; 240 retained after discarding infeasible ones), and 10-fold CV for the spline penalty. No external measurement.

**Stated limitations:**
- one time per swimmer;
- independence across events for the same swimmer;
- threshold uncertainty not quantified;
- frequentist (no predictive uncertainty).

**Relation to the central question:**
- It conditions on *covariates of the population of performances* (time, technology), not on a performance's own opportunity.
- It has **no athlete random effects, no per-athlete endpoint, and no notion of within-competition opportunity.**
- It shows that rate-aware EVT with covariates and endpoints is established (as already recorded at A level in Phase 8B). It does not estimate player-specific capacity conditional on opportunity.

### 2.2 Greene (2005) and Koop et al. (1997): K only

- **Inaccessible** (closed access, no repository copy). Only standard-formulation knowledge applies (K):
  - "true random effects" SFA separates unit heterogeneity from inefficiency;
  - Bayesian SFA with individual effects gives posterior per-unit efficiency.
- **No claim about their content beyond K is made.** In particular, we cannot say from the papers whether they treat frontiers whose shape depends on per-observation opportunity. Nothing in this audit depends on that detail: the decision in §5 holds whether or not they do.

### 2.3 Hall & Simar (2002): A

- With additive observation error of variance σ², boundary estimates are biased at O(σ). Their correction reduces this to O(σ²).
- The frontier is "generally not even identifiable unless the error distribution is known".
- Full text restricted.
- **Relevance:** any opportunity-conditioned boundary estimated from noisy 10 Hz peaks inherits this identifiability limit, unless the error law is pinned down. Our Phase 1.6 base noise of 0.01 yd and the spike rule are partial knowledge, not a known error law.

### 2.4 Nguyen & Yurko (2026): implementation (F-code)

**Repository contents:** README + 12 R scripts (data preparation, step model, turn model, ratings, model comparison, yards model, tuning, comparison, simulation, metrics, alternative simulation, simulation comparison). Read in full, not executed.

**Implementation details that matter here, beyond the paper:**
1. **Time step is 0.3 s, not 0.1 s.** Frames run from 6 frames before the handoff to the end event, and are subsampled with `frameId_corrected %% 3 == 0`. Simulated speed is `pred_step_length / 0.3`. The paper's "distance between successive locations" therefore means 0.3-s displacements.
2. **Transform with a sample-bounded support:**
   - `asin(sqrt((s − min)/(max − min)))`, where min and max are the pooled-sample extremes.
   - Back-transformation maps every prediction into [min, max] of the observed sample. The model therefore has an **implicit population ceiling equal to the largest observed 0.3-s step**. There is no player-specific ceiling.
3. **Step model:**
   - `brm(step_length_asin ~ prev_step + ... + (1|bc_id) + (1|defensiveTeam))`, Gaussian, QR decomposition, 4 × 5,000 iterations, seed 14.
   - Fixed effects: lagged step (raw scale); ball-carrier field position and distance to the first down; counts of defenders and teammates to the left and in front; nearest-defender position, distance, speed and angle.
   - A random intercept only: no player-specific slopes or variances.
4. **Turn model:** von Mises; the mean has the same fixed effects plus the lagged angle; `kappa ~ step_length + (1|bc_id)`.
5. **Validation in code:**
   - Movement models: R-hat, ESS, posterior predictive checks, and Gamma / log-normal alternatives. **No held-out split.**
   - The yards model is tuned by 5-fold CV grouped by game. The final model is trained on all frames and then predicts those same frames for the "observed" values, i.e. in-sample.
6. **Simulation:** `sample_new_levels = "uncertainty"` for a generic player; 100 draws per frame; positions clipped to the field.

**Opportunity representation:**
- Implicit only, through the lagged step (momentum), field position, first-down distance and nearby-player configuration.
- No covariate for available acceleration distance, remaining play time, or direction relative to the run-up.
- **No capacity estimand.**

**Applicability to our data: not directly reproducible.** Half its covariates (nearest defender, player counts) need all 22 players. Our game tracking contains only the 510 cohort players, with no ball and no other players (CLAUDE.md data facts). A reduced version (own-kinematics only) would no longer be the published model.

### 2.5 Other opportunity-conditioned speed work (§6 of the request)

- **MLB Statcast Sprint Speed (S).**
  - It handles opportunity by **rule-based selection** of "competitive runs": runs likely to need full effort, such as two or more bases on non-homers, or home-to-first on weakly hit grounders.
  - It then averages the fastest one-second window over roughly the top two-thirds of those runs (sources conflict: top half vs two-thirds).
  - This is an established, deployed, opportunity-filtered capacity metric. It uses a filter, not a model.
- **RACE (Lee 2026, P).**
  - Stage 1 is a population "performance envelope" (age-conditional 95th centile of Statcast sprint speed, GAMLSS). Stage 2 is a hierarchical nonlinear mixed model of each athlete's level and ageing tempo relative to that envelope.
  - Bolt rate is weighted by competitive opportunities.
  - The unit is the athlete-season. The input is already opportunity-filtered (Statcast). There is no external measurement. Selection into continued play is unmodelled (stated).
  - **This is a 2026 precedent for "envelope + hierarchical athlete effects" on speed capacity.**
- **Postma et al. (2022, A).**
  - Lab maximal sprints (LPS): they map each person's maximal speed and acceleration to the *distance coverable in a given time* ("action boundaries"). They propose a non-linear macroscopic sprint model.
  - This is an opportunity-to-attainable-displacement mapping under maximal effort. It is not estimated from sub-maximal game play.
- **Mono-exponential sprint kinematics** (Clark 2019, A; Samozino 2016, A; GPS/LPS profiling validity, S):
  - v(t) = v_max(1 − e^{−t/τ}), and hence attainable speed after distance d.
  - This is the standard way to turn "available acceleration distance" into an attainable speed for given athlete parameters. Validity is good for maximal speed and weaker for early acceleration (S).
- **Soccer match studies (S):**
  - Near-maximal speed needs about 30–40 m of sprinting, and depends on position and tactical purpose.
  - Match peaks sit below test maxima.
  - These quantify the opportunity effect descriptively; none turns it into an estimator (search level).
- **Gyarmati & Hefeeda (2015, S):** per-player in-game maximal speed from event data at scale. It reports that about 8 games suffice, and that some teams need about 50 % more games. It is an exposure-sufficiency statement, not an opportunity model. Full text not read.
- **TTA (Gutiérrez-Pérez & Agudo 2026, F, Phase 8B):**
  - A *population* Q_0.01 of arrival time, conditional on current speed, acceleration, target distance and bearing, i.e. **conditional on the geometric opportunity**.
  - Player specificity enters only as a plug-in 99th-percentile v_max.
  - **This is the closest existing estimator of "attainable movement given opportunity".**

## 3. Answers to the six questions

**Q1. Does existing work already estimate player-specific movement capacity conditional on available opportunity?**
- **Partly, by pieces; not as one validated estimator.**
- Already existing:
  - opportunity-conditioned *population* attainability: TTA (F) for arrival time given distance, bearing and speed; Postma 2022 (A) for distance coverable over time;
  - *player-specific* attainable speed as a deterministic function of distance: mono-exponential models with athlete v_max and τ (A/K);
  - *rule-based* opportunity filtering for player capacity: Statcast (S);
  - envelope + hierarchical athlete effects for speed capacity: RACE (P);
  - player random effects for movement given context: step-and-turn (F).
- Not found: a player-specific, uncertainty-quantified capacity estimated from sub-maximal game plays by *modelling* each play's opportunity. That is an absence in our searches, not evidence of absence.

**Q2. How do existing methods represent acceleration distance, turning, direction and task context?**

| method | acceleration distance / time | turning / direction | task context | player specificity |
|---|---|---|---|---|
| TTA (F) | target distance d and horizon Δt as inputs; current v and a in the heading frame | bearing cos θ, sin θ (turning cost learned) | none (slowness from intent discarded by Q_0.01) | plug-in v_max |
| step-and-turn (F, F-code) | lagged 0.3-s step only | lagged turn angle; κ depends on step length | defenders, teammates, field and first-down position | random intercepts |
| poster QR (F) | none (acceleration vs speed) | none | none (stated limitation) | independent per-player fits |
| mono-exponential / A–S (A/K) | explicit t or d from a standing start | none (straight line) | none | athlete v_max, τ |
| Postma 2022 (A) | distance over time | forward vs backward running | maximal lab task | per person |
| Statcast (S) | via the run type (≥ 2 bases, home-to-first) | implicit | rule-based task filter | per player, averaged |
| Spearing (F) | none (event distance is a stratum) | none | time, technology | none (event level) |
| RACE (P) | none | none | age; Statcast opportunity filter | hierarchical level / tempo |

**Q3. Can an existing method be applied directly to our NFL tracking data?**
- **Yes:**
  - order statistics (max, top-k, 99th percentile = the TTA plug-in);
  - per-player QR / QGAM (poster);
  - mono-exponential / A–S fits;
  - Statcast-style rule filters (e.g. deep routes only, a minimum straight-line segment);
  - random-effects or frontier models on per-play peaks;
  - a RACE-style envelope + hierarchy across seasons;
  - TTA retrained on own kinematics (it needs only the player's own state and target).
- **Not as published:** step-and-turn. Its covariates need all 22 players, and our tracking has only the cohort player.
- **Not meaningfully:** Spearing's event-level model. It could be re-specified per athlete, but that is a new model, not the published one.

**Q4. Does combine tracking provide an independent validation measurement that existing studies lack?**
- **Among the closest works, yes:** TTA, step-and-turn, the poster, Spearing and RACE have no same-athlete external capacity measurement.
- **But not in general.** In-situ profiling studies (Morin 2021, Miguens 2024: A/S) compare in-situ estimates against dedicated sprint or radar tests, and soccer studies compare match peaks with test maxima (S).
- So the combine anchor is a **data advantage at NFL scale** (about 330–418 players, within-position R_x 0.94–0.99). It is **not a methodological novelty**.
- Its known limits also apply: different construct (straight line, standing start, no pads); our Phase 2 within-position transfer was ρ 0.13–0.73.

**Q5. Is there a technically defensible algorithmic contribution beyond combining known QR, hierarchical models, stochastic frontiers and EVT?**
- **No.** The most specific candidate is the "opportunity-conditioned frontier": each play's peak speed bounded by a player-specific kinematic attainable speed g(θ_i, τ_i; d_ij), with d_ij the play's available straight-line distance, a one-sided effort deficit, and hierarchical player effects. Its parts:
  - **the frontier shape** is the mono-exponential sprint model (A/K);
  - **player-specific frontier parameters with pooling** are random-parameter / Bayesian SFA (K) and RACE-style hierarchy (P);
  - **the one-sided deficit with covariates** is Battese–Coelli determinants (K);
  - **noise in the boundary** is Hall & Simar (A);
  - **opportunity-conditioned population attainability** is TTA (F).
- Writing these together is a model specification within existing classes, not a new algorithm.
- **There is also an identification problem that a specification cannot solve with our data:**
  - The available distance d_ij measured from the player's *own realised trajectory* is endogenous. A player who eases off produces shorter straight-line segments, so "low opportunity" and "low effort" are observationally confounded.
  - Exogenous opportunity proxies in our data are coarse: route type and depth (frozen classes), time to throw, position.
  - Turning or direction constraints from opponents cannot be measured, because other players are absent from game tracking.
  - Hall & Simar's result adds that the boundary is not identifiable without a known error law.
- An algorithmic claim would therefore rest on an assumption the data cannot check.

**Q6. Can the proposed method be evaluated against strong existing baselines on held-out players?**
- **Yes, as an empirical benchmark.** Plays can be split by player (grouped CV) and season-forward, using the Phase 3–4 infrastructure. Baselines: max / top-k / 99th percentile (TTA input); Statcast-style filtered top-k; per-player QR (poster); a hierarchical mean (a reduced step-and-turn style model); random-effects SFA; a mono-exponential frontier fit.
- Targets:
  - within-position agreement with combine peak speed;
  - drift under exposure subsampling of the player's own plays;
  - calibration of the intervals.
- **Power is limited.** About 60–77 players per position. Phase 3.5 found a minimum detectable Δρ ≈ 0.30 at this size; paired comparisons on the same players help, but only partly. Small differences between estimators will not be detectable.

## 4. What remains genuinely open (our reading)

1. **An empirical question:** in NFL game tracking, do player speed traits drift with exposure and opportunity, and do opportunity-filtered or hierarchical estimators track an independent same-athlete measurement better than plain order statistics?
   - This is answerable with our data.
   - It is not answered by the reviewed works.
   - It is partly anticipated by our own Phase 2 findings: maxima grow with exposure; within-position transfer is partial.
2. **No algorithmic gap:** every model component exists, and the decisive difficulty (opportunity endogeneity, plus the absence of other players) is a data-identification limit, not a missing algorithm.

## 5. Decision

**B. An empirical contribution is defensible, but no new algorithm is justified.**

- The opportunity-conditioned capacity idea is **rejected as an algorithmic contribution.**
  - Its components are established (§3 Q5).
  - Its key separation, opportunity vs effort, is not identifiable from own-trajectory opportunity measures in our data.
  - TTA (F) already provides opportunity-conditioned population attainability; Statcast (S) already provides rule-based opportunity filtering for a player capacity metric.
- What remains defensible is the empirical benchmark G1′ (see `algorithmic_research_gaps.md`, `phase8_recommendation.md`).
  - It does **not** meet CLAUDE.md research standard 3 (a new algorithm).
  - It should be presented as an evaluation of existing estimators against an independent anchor, without a novelty claim.

**Why not C:**
- The empirical question is well posed, testable on held-out players with strong baselines, and not answered by the reviewed works.
- If the project lead requires standard 3 to be met, the answer for this track is **C**: no sufficiently strong algorithmic contribution is supported.

## 6. Not claimed

- Novelty of any model or of the combine validation design.
- Anything about the full texts of Greene 2005, Koop et al. 1997, Hall & Simar 2002, Kneip et al. 2015, Postma et al. 2022 or Gyarmati & Hefeeda 2015, or about the unread sections of RACE.
- That the Statcast filter or TTA would perform well or badly on NFL data. Neither was tested.
