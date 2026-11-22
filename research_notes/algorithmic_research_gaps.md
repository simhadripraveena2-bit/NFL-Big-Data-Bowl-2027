# Phase 8: algorithmic research-gap candidates

**Basis:**
- `related_work_full_text_review.md` and `existing_method_comparison.md`: literature at abstract or search level only; no full text read in Phase 8.
- Our completed empirical study: Phases 1–7.

**Caveat on every candidate.** "Insufficient existing methods" means *insufficient among the methods we could verify at abstract or search level*. **No candidate is claimed to be novel.** A full-text check of the closest work, listed per candidate, is a precondition.

## Empirical facts motivating the candidates (from our own study)

| fact | source |
|---|---|
| Game speed levels are far below combine levels; within-position rank transfer is only partial (peak vs game max ρ 0.13 for DB to 0.73 for DL) | Phase 2, `real_data_capacity_transfer.md` |
| Observed game maxima grow with exposure; game A0 by binning is implausible (> 15 yd/s²) for 22 % of high-exposure players | Phase 2 |
| Game braking and lateral values are *demonstrated envelopes*, not capacities (they make combine drills "impossible") | Phase 2 |
| Combine tracked peak speed is highly reliable within position (best-of-2 R_x 0.94–0.99); the official 40 is not identifiable from tracking | D3, `forty_test_retest.md` |
| Role and body weight drive much of the combine–game speed association (DL); context (route depth, coverage) and demand differ by position | H1-DL(b) audit; demand validation |
| Player-level signal is small relative to play noise in some outcomes (WR deep separation reliability 0.44) | H2 |
| The registered player bootstrap is over-dispersed in crossed (player × team-season) designs | Phase 4 (D2) |

## G1. Exposure-aware estimation of latent athlete speed capacity, with external validation

**Precise problem.** Each player i contributes plays j = 1…n_i with observed peak speeds y_ij. These are mostly sub-maximal:
- y_ij = θ_i − u_ij + ε_ij, where θ_i is the latent capacity, u_ij ≥ 0 the context- and effort-dependent deficit, and ε_ij tracking noise.
- The usual estimators (max_j y_ij, top-k mean, high quantile, M2 profiles) are order statistics. Their bias depends on n_i and on the **distribution of opportunities** (how many plays allow near-maximal speed).
- That distribution differs systematically by role, deployment and playing time.
- **The goal:** estimate θ_i, with calibrated uncertainty, for players with few or unequal opportunities, including unseen players.

**Why existing methods are insufficient (at the available evidence level):**
- **M1 and M2** ignore exposure, and treat noise heuristically (DBSCAN).
- **M2** shows session-type and position dependence but does not model it (Miguens 2024, A).
- **M3a** is a population envelope (S).
- **M3b** has no verified exposure model or uncertainty (S).
- **M4 (basic SFA)** has i.i.d. deficits and no athlete hierarchy. Above all, the *expected maximum of n draws* is not linked to n.
- **M7** models typical, not maximal, movement (S).
- Literature (S) says match peaks underestimate test maxima and depend on situation, but nothing found turns this into an estimator.

**Why it matters:**
- Every analysis that uses "game top speed" as an athlete trait, including pitch-control models that assign player-specific top speeds from matches (da Silva 2025, S), inherits exposure bias.
- Players who get fewer deep routes or fewer open-field chances look slower.
- For scouting and load management, the question "is he slower, or just not asked to run?" is decision-relevant.

**Can our data evaluate it? Yes; this is its main strength.**
- **External anchor:** combine tracked 40 peak speed for the same players, within-position R_x 0.94–0.99, about 330–418 players with game data.
- **Exposure varies naturally:** 2023–2025, players with 1–3 seasons, different roles.
- **Controlled sparsity:** subsampling a player's plays creates exposure regimes where the full-data estimate is a reference.

**Caveat.** Combine peak speed is not the same construct as game capacity (equipment, start type, straight line). Phase 2 found game levels are far lower. Validation should therefore target:
- **ranking and calibration** (within-position rank correlation, interval coverage after a learned position-level offset),
- **exposure-invariance**: the estimate should not drift with n_i or with opportunity mix,

rather than equality of levels.

**Possible contribution (to be designed only after approval):**
- A hierarchical (partially pooled) boundary model.
- Each play's peak is the capacity minus a non-negative deficit whose distribution depends on context. Candidate context features: route depth, coverage role, the demand measure D, time to throw.
- Tracking noise is explicit (possibly using a state-space-smoothed speed, M6).
- Capacity has a position-level prior, with optional pre-game covariates (weight) used carefully because of the DL collinearity.
- Inference via posterior or likelihood gives per-athlete intervals.
- The algorithmic core is to model **the observed maximum as the maximum of an exposure-dependent number of context-specific draws**. This is the piece missing from M2, M3 and M4, as far as could be verified.
- It must be written as pseudocode, with its complexity, at the design stage.

**Experiments that would demonstrate improvement:**
1. **Exposure-invariance test:** subsample plays per player (e.g. 10 %, 25 %, 50 %, 100 %). Measure the bias drift of each estimator relative to its own full-data value.
2. **External validity:** within-position Spearman correlation and calibrated-interval coverage against combine peak speed, on held-out players and season-forward.
3. **Unseen players:** predict capacity for players held out entirely (prior plus few plays).
4. **Simulation** with known θ_i and realistic opportunity distributions (Phase 4-style real-design skeletons).
5. **Baselines:** max, top-5 mean, 99th percentile, Miguens-style A–S S0, SFA, per-athlete quantile regression, and a hierarchical Gaussian mean model. Identical splits; paired significance tests.

## G2. Noise-robust estimation of acceleration, braking and turning capacity with physical consistency

**Precise problem.** Estimate per-athlete acceleration, deceleration and lateral or turning capacity curves (as functions of speed) from 10 Hz positions, where:
- double differentiation amplifies noise (CLAUDE.md data facts);
- turning contributes 22–33 % of |a|² in sharp turns;
- observed envelopes are context-dependent.

**Why existing methods are insufficient:**
- **M2** fits only straight-line A–S, with heuristic outlier removal.
- **M6** smooths kinematics but imposes no capacity constraint, and its noise parameters must be estimated (S).
- **M3b** fits quantile curves without a noise model.
- **M5** physics models assume the movement-model form (S).
- None verified couples state-space denoising with a constrained, athlete-pooled *capacity boundary* in (speed, tangential, normal) acceleration space.

**Why it matters:** acceleration, braking and change of direction are central to football movement. Our Phase 2 showed these are not identifiable with current methods (game A0 implausible).

**Can our data evaluate it? Only partly.**
- Combine tracking gives straight-line acceleration (40 mono-exponential fits, R² > 0.95) and change-of-direction drills.
- But Phase 2 found combine change-of-direction timing has limited validity (3-cone r = 0.65; shuttle unusable).
- There is no ground truth for game braking or turning capacity. Validation would rest heavily on simulation.

**Possible contribution:** a state-space model with a latent per-athlete feasible-acceleration set (e.g. a speed-dependent friction-circle boundary) and an explicit observation-noise model, estimated hierarchically.

**Experiments:**
- simulated trajectories with known limits (Phase 1.6 infrastructure);
- test–retest stability across seasons;
- combine 40 acceleration as a partial anchor;
- baselines: M2, M3b, M6 + envelope.

## G3. Identifying capacity separately from deployment: role and context selection

**Precise problem.** Observed movement reflects capacity × deployment. Roles are partly *chosen because of* capacity (the H1-DL(b) audit: role and weight each remove most of the speed–movement association; role is a mediator). Estimate capacity, or bounds on it, that are robust to selection into roles and contexts.

**Why existing methods are insufficient:**
- M7 conditions on context as an exogenous covariate.
- M5 takes context from the initial state.
- None found treats role assignment as endogenous to capacity.

**Why it matters:** comparing players across roles (EDGE vs interior; slot vs outside; man vs zone) is a core scouting task. Naive adjustment can produce artefacts, such as the uninterpretable adjusted DL ρ.

**Can our data evaluate it? Weakly.**
- There is no exogenous variation in role and no ground truth.
- Evaluation would be largely semi-synthetic: plant role-selection mechanisms in real-design skeletons, as in Phase 4.
- Combine data can serve only as a pre-deployment anchor.

**Possible contribution:** a joint model of role assignment and movement given latent capacity (a selection-model or partial-identification bounds framework).

**Experiments:**
- coverage of the bounds or intervals under planted selection;
- a comparison with naive adjustment (which produced sign flips in our DL audit).

## G4. Bootstrap inference for nonlinear variance-component functionals in crossed designs

**Precise problem.** Our registered player-cluster bootstrap of a REML correlation estimand (ρ_c) was over-dispersed (SE 1.4–1.9× the sampling SD), because duplicated players share team-season levels (D2).

**Existing work** (S): the pigeonhole bootstrap (Owen 2007) and the Owen & Eckles (2012) reweighting bootstrap address crossed random-effects arrays. They are consistent or conservative for **means**. McCullagh (2000) shows no exact bootstrap exists.

**Remaining gap (if any):** behaviour for *nonlinear functionals of variance components* (ratios such as ρ = β/√(β² + Σ_b)) in unbalanced crossed designs with sparse clusters (36 of 71 WR team-seasons have a single player). **Not verified as open.** It needs a full-text check of Owen 2007, Owen & Eckles 2012, McCullagh 2000 and the parametric-bootstrap literature for mixed models.

**Can our data evaluate it? Yes, by simulation:** the Phase 4 real-design skeletons and the warp-speed machinery already exist.

**Possible contribution:** a calibrated resampling scheme (e.g. copy-specific cluster labels, a pigeonhole variant, or a parametric bootstrap) for ratio functionals, with coverage guarantees in simulation.

**Experiments:** null size, coverage and power against Owen–Eckles, the parametric bootstrap and the registered scheme, on identical simulated designs.

## Summary

| | G1 exposure-aware capacity | G2 noise-robust acceleration / braking / turning capacity | G3 capacity vs deployment | G4 crossed-design bootstrap |
|---|---|---|---|---|
| precise target | latent per-athlete top speed from sub-maximal, exposure-varying plays | per-athlete feasible-acceleration set from noisy positions | capacity robust to role selection | calibrated CIs for ratio functionals |
| closest existing work (must be read in full) | Gutiérrez-Pérez & Agudo 2026; Shteynberg 2025; Morin 2021; Miguens 2024; SFA / partial-frontier and panel SFA; Nguyen & Yurko 2026 | Miguens 2024; SciSports 2018; "Who Blocks Whom?" 2026; Brefeld 2019 | selection models (not reviewed); Nguyen & Yurko 2025/2026 | Owen 2007; Owen & Eckles 2012; McCullagh 2000 |
| external ground truth in our data | **yes** (combine peak speed, same players) | partial (combine 40 acceleration) | no | simulation |
| main risk | combine ≠ game construct; prior work may already cover it | identifiability; validation mostly synthetic | identification fundamentally weak | likely incremental; strong prior work |
