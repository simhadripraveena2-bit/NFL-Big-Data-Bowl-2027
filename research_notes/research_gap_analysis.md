# Research Gap Analysis — Phase 1.5

*Each candidate is assessed against the literature in `literature_review.md` (cited as **[#n]**) and against what the
competition data actually contains (Phase 1 findings, plus one new count below). "Not found" means not found in
our structured search (PubMed + Crossref; Semantic Scholar only partly reachable). It is not proof of absence.*

## 0. Data constraints that bind all three candidates

| Constraint | Evidence | Consequence |
|---|---|---|
| **Same-drill repetitions are scarce.** Of 4,986 (player, drill) pairs, **3,723 (75%) have exactly 1 attempt**, 1,213 have 2, and 50 have ≥ 3. Only the 40-yd dash has 2 attempts for most players (90%). Shuttle and 3-cone: 24–25% have ≥ 2 attempts. | New count (Phase 1.5, `combine_tracking`) | Phase 1's "6–18 attempts per player" counts attempts *across different drills in a family*, **not repetitions of the same task**. Per-athlete variability across attempts is essentially unidentifiable in the combine. |
| One combine occasion per athlete | Phase 1 | Day-to-day (occasion) variance cannot be estimated. Any reliability estimate is *within-session* and therefore optimistic. |
| Unit of inference is the player | Phase 1 | n ≈ 63–77 per position with ≥ 100 regular-season plays (TE 21); n ≈ 418 with a tracked 40; n ≈ 160–170 for agility drills (self-selected) |
| `a` is unsigned; combine `dis` unusable; 10 Hz | Phase 1 | Braking and tangential acceleration must be derived by differentiation, which amplifies noise; contact-level events (≈ 0.1–0.25 s) are at the resolution limit |
| Game tracking covers only cohort players, with no ball; WR/TE rows are route-running dropbacks only | Phase 1 | Opponent-relative outcomes come from `player_play` (separation, cushion, pressure, get-off), not from tracking |
| **In-game repetitions are abundant** | Phase 1: 314,944 player-plays | Within-player *game* variability is identifiable, unlike combine variability |

---

## Candidate A — Movement consistency and repeatability across repeated combine attempts

**1. What is established**
- Reliability methodology for performance tests is mature: typical error, CV, ICC forms, the smallest worthwhile change, and the pitfalls of relative-reliability statistics [#68–#72, #74, #77].
- Combine-type agility and sprint tests are reliable when timed: Division-I football ICC 0.91–0.97, CV 1.2–1.9% [#18]; agility tests ICC 0.79–0.99 [#75]; soccer speed tests ICC > 0.75, CV < 3% [#76].
- Theory and some small-n evidence: skilled performers reduce variability in *task-relevant* dimensions and tolerate it in irrelevant ones [#61–#64]; variability is functional, not only noise [#57, #58, #60].
- Location-scale models estimate individual within-person variance as a trait [#78, #79]. In psychology, that trait predicts behaviour beyond the mean [#80], and a single ICC can misdescribe individuals [#81].

**2. What is not adequately investigated**
- The reliability of *tracking-derived* combine quantities (velocity-curve parameters, braking and turn kinematics), as opposed to stopwatch totals. Not found.
- Individual-level movement consistency as a predictor of on-field performance in team-sport athletes. Not found; the location-scale literature is psychology and health behaviour.
- Task-relevant vs task-irrelevant variability decomposition (UCM / TNC) applied to whole-body *trajectories* in field drills. Not found; existing work uses joint angles with 10–20 lab repetitions [#62, #64, #66].

**3. Does the 10 Hz combine dataset offer a new opportunity?**
**Only partially, and much less than Phase 1 implied.**
- With 1 attempt for 75% of (player, drill) pairs, an individual's *across-attempt* consistency cannot be estimated. A location-scale model needs many repetitions per person (7–40 in [#79, #80]).
- What the combine *does* support:
  - (i) population-level within-session reliability for the 40 (two attempts, n ≈ 375) and for a minority of other drills;
  - (ii) *within-attempt* repeated sub-movements (several cuts within one W-drill, 3-cone or shuttle; several catches within the gauntlet).
- The repetition-rich setting is **in-game**: hundreds of routes, pass-rush reps or coverage reps per player.

**4. Technical challenges**
- Identifiability: within-person variance from n = 1–2 per drill.
- Confounding of "consistency" with fatigue or learning across the combine day (attempt order) [#68, #70].
- Within-attempt sub-movements are not exchangeable: the cut angle differs within a drill.
- In-game "consistency" is confounded by assignment, opponent and context.

**5. Potential original contribution**
- (a) A **measurement-error foundation**: the first reliability / generalizability analysis of tracking-derived combine quantities, used to *correct* downstream analyses for regression dilution [#113].
- (b) A **re-scoped consistency hypothesis tested in games**: a location-scale model of repeated in-game actions of the same type (e.g. the same route), with combine data contributing a capacity covariate. This is a contribution, but it no longer uses "repeated combine attempts" as the primary data.

**6. Experimental demonstration**
- (a) Reliability coefficients with uncertainty, and a regression-dilution correction factor.
- (b) Bayes-factor or LOO comparison of homogeneous vs individual within-person variance [#81].
- Then test whether in-game scale (consistency) predicts outcomes beyond location (level), on a held-out draft class.

**Verdict:** **as literally specified (repeated combine attempts), Candidate A is not well supported by the data.** Its methods are valuable as a *supporting measurement layer* for B and C, or as an in-game consistency study.

---

## Candidate B — Transfer of combine acceleration and speed characteristics into NFL games

**1. What is established**
- Maximal sprints are well summarised by 2-parameter models (mono-exponential / linear A–S) [#15, #22, #27].
- At the NFL combine, v_max explains most of 40-yd time (r = 0.94) and fast and slow athletes share τ [#15]. Acceleration and max speed are partly separate qualities [#5].
- **In-situ** A–S profiles can be built from routine tracking:
  - linear, R² > 0.98 [#27];
  - reliable if near-maximal efforts are present [#28, #33];
  - automatable with outlier clustering [#29];
  - in agreement with isolated sprints [#30].
- **But** acceleration-side parameters are insensitive and only max speed is robust [#31].
- Match peak speed relates to test speed but sits at 85–94% of it [#35], or *exceeds* it [#36].
- Highest A0 occurs in games, highest S0 in speed sessions [#29].
- The combine → NFL success literature is weak, uses stopwatch summaries, and largely uses draft outcomes [#1–#14, #20].

**2. What is not adequately investigated**
- In-situ A–S profiling in American football. Not found.
- Linking an athlete's **combine-day tracking profile** to the same athlete's **in-game profile**. Not found.
- **Exposure-dependent censoring:** in-situ methods assume each athlete eventually produces near-maximal efforts [#28]. In the NFL, role strongly limits this; offensive linemen rarely sprint (Phase 1). No in-situ method models *opportunity*. The binning [#27], DBSCAN [#29] and boxplot/CI [#30] approaches treat the upper envelope heuristically, with no uncertainty propagated to downstream analyses.
- Whether the *gap* between tested capacity and expressed game capacity carries information. Not found; the literature reports only the relationship [#35, #36].

**3. Does the dataset offer a new opportunity?** **Yes, the strongest of the three.**
- About 418 athletes with tracked 40s (two attempts for 90%).
- In games (regular season + postseason), frames per player-season: median ≈ 19,300, interquartile range 5,900–40,600, 10th percentile ≈ 1,600, across 723 player-seasons. Exposure is very uneven, which is exactly the censoring problem.
- Phase 1's descriptive probe already shows measurable linkage (WR ρ = 0.59 for 40 peak speed vs game 99th-percentile speed), with the role-composition caveat.

**4. Technical challenges**
- (i) **Censored envelopes:** role-limited players never approach capacity, so the frontier is weakly identified.
- (ii) **Derived acceleration noise** [#31, #42, #55].
- (iii) **Separating capacity from role.** Expressed speed is a function of assignment.
- (iv) **Selection:** game exposure depends on draft capital, which depends on combine results [#4, #12].
- (v) **Novelty risk:** "fast at the combine → fast in games" is close to obvious. The contribution must come from the *method* and from what the capacity–expression *gap* explains.
- (vi) Ettema's critique [#24]: new parameters must add information beyond raw speed curves.

**5. Potential original contribution**
- **Algorithmic:** a hierarchical, exposure-aware **stochastic-frontier** estimator of individual A–S capacity from game tracking. It treats each frame as capacity minus a non-negative "effort shortfall" plus noise (frontier logic from [Aigner et al. 1977]), with partial pooling by position and an explicit opportunity model. It improves on heuristic envelope extraction [#27, #29, #30] by:
  - producing calibrated uncertainty;
  - remaining usable for low-exposure athletes;
  - jointly linking to the combine 40 profile.
- **Scientific:** quantify *transfer* (combine capacity → game capacity) per position, with measurement-error correction. Then test whether **capacity utilisation** (expressed ÷ latent capacity) has incremental validity for position-matched outcomes.

**6. Experimental demonstration**
- **(1) Simulation with known ground truth.** Synthetic athletes with true A0/S0, role-dependent effort distributions, and 10 Hz noise. Compare RMSE, coverage and bias against the binning, DBSCAN and quantile-regression baselines [#27, #29; Koenker & Bassett 1978].
- **(2) Real-data reliability.** Split-half by games and season-to-season ICC, compared with the baselines.
- **(3) Convergent validity.** Agreement of game S0 with combine-40 S0, measurement-error corrected.
- **(4) Incremental validity.** Pre-registered, player-level cross-validation, on a held-out 2025 class.

---

## Candidate C — Braking and change-of-direction mechanics and their relationship with NFL performance

**1. What is established**
- Horizontal deceleration has distinct, high-load mechanics, and braking-force control and attenuation are key [#38, #40]. High-intensity decelerations are frequent in match play [#39].
- COD deficit isolates COD from linear speed (r ≈ 0 with sprint time) [#44]. Deceleration deficit and percentage-based variants exist [#45, #46].
- Biomechanical determinants of faster COD are known from lab tasks: approach and exit velocity, braking and propulsive forces, contact time, trunk lean [#47, #49]. Only pre-planned tasks, small n [#49].
- Curvature costs speed, and individuals differ in how well they tolerate it [#52, #53].
- Match COD events can be extracted from tracking and characterised by angle with mixed models (soccer) [#51].

**2. What is not adequately investigated**
- COD and braking capacity derived from **continuous combine trajectories**, as opposed to stopwatch deficits. Not found; existing deficits are time differences needing only gates [#44–#46].
- A **physics-based, athlete-specific counterfactual**: how long *this* athlete *should* take to run *this* path given their own acceleration, speed, braking and curvature limits. Not found in sports. The tool exists in vehicle dynamics as minimum-time speed profiles on a fixed path [Velenis & Tsiotras 2008; Lipp & Boyd 2014].
- Combine COD mechanics → in-game COD behaviour in American football. Not found.
- Deceleration accuracy of NFL game tracking: no validation study found. LPS studies show the largest errors for deceleration [#54, #55].

**3. Does the dataset offer a new opportunity?** **Yes, but with measurement risk.**
- 3-cone and shuttle trajectories (160–170 self-selected athletes) and position skill drills with turns for all 510 (W-drill, backpedal-and-break, route breaks, OL/DL footwork).
- In games, hundreds of cuts per WR/TE route and per DB break.
- Phase 1 showed derived braking of −6 to −8 yd/s² in agility drills.
- The data cannot see foot contacts at 10 Hz.

**4. Technical challenges**
- Differentiating 10 Hz positions to get braking: noise and lag, with processing choices under-reported [#42].
- Heading is ill-defined at low speed (Phase 1, fig07).
- Curvature estimation from noisy paths.
- Self-selection into agility drills.
- Pre-planned (combine) vs reactive (game) COD [#49].
- Translating an *execution* metric to game outcomes that depend on scheme and opponent.
- Risk that the metric collapses to linear speed: 10-m time strongly predicts 505 [#50]. It must be shown to be *distinct*, as COD deficit was [#44].

**5. Potential original contribution**
- **Algorithmic:** a **capacity-constrained minimum-time (CCMT) COD model**. For each observed path, compute the athlete's own minimum feasible time using:
  - the acceleration–speed limit (from B);
  - a braking limit;
  - a speed-dependent lateral (centripetal) limit;
  - solved by a forward–backward pass or a convex speed optimisation along the path [Velenis & Tsiotras 2008; Lipp & Boyd 2014].
- The observed time then decomposes into:
  - **capacity cost** — the athlete's optimum minus a reference optimum;
  - **execution cost** — observed time minus the athlete's own optimum.
- This generalises the COD deficit [#44] from a time difference to a path- and athlete-specific counterfactual, and applies identically to combine drills and game cuts.
- **Scientific:** test whether *execution cost* (technique and braking efficiency) is distinct from linear speed, reliable, transfers from combine to game, and adds predictive value for position-matched outcomes, especially WR/TE separation and DB coverage.

**6. Experimental demonstration**
- **(1) Simulation.** Synthetic athletes running known paths with known limits plus a technique inefficiency, at 10 Hz with noise. The model should recover execution cost; COD deficit confounds it with path differences.
- **(2) Discriminant validity.** Correlation of execution cost with 40 time should be ≈ 0 (as for COD deficit [#44]), and its correlation with 3-cone time should be > 0.
- **(3) Reliability** on the athletes with two attempts, and across different drills (cross-drill consistency).
- **(4) Transfer.** The same metric on in-game cuts, correlated with combine values.
- **(5) Incremental validity** for matched outcomes against the baselines: total time, COD deficit, deceleration deficit, peak braking, and FPCA scores.

---

## Summary of gaps

| | A: consistency | B: speed/accel transfer | C: braking / COD |
|---|---|---|---|
| Literature maturity | Theory mature; no sports-test application of individual consistency | In-situ A–S mature in soccer and rugby; nothing in American football | Lab biomechanics mature; trajectory-based, athlete-specific COD absent |
| Genuine gap | Individual consistency as a trait in athletic tests | Exposure-aware frontier; combine↔game linkage | Physics-based counterfactual COD cost; combine↔game COD |
| Data fit | **Poor** for combine (1–2 reps); good in games | **Good** | **Moderate** (10 Hz, differentiation noise, self-selected agility subset) |
| Main risk | Unidentifiable at the individual level | Obviousness of the main effect; role confounding | Measurement noise; collapse onto linear speed |
