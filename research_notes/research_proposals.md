# Research Proposals — Phase 1.5 (candidates; **no hypothesis is finalised**)

*References like [#n] point to `literature_review.md`. Each hypothesis is written so that it can fail.
Thresholds are proposals to be fixed in a pre-registration before any outcome data are examined.
All "novel" statements are relative to what our search retrieved, and must be re-checked against the full
texts of the closest papers.*

Shared design rules (from CLAUDE.md and Phase 1):
- **Unit of inference:** the player.
- **Validation by player:** confirmatory tests on a **held-out draft class** (proposed: 2023 + 2024 for development, 2025 for confirmation, or a pre-registered alternative).
- **Measurement error modelled explicitly.**
- **Role conditioning** via `player_play` context.
- **Exclusions:** game 2025101205 (plays 1289/1314) and speed spikes.
- **Multiplicity** controlled by a small pre-registered primary set plus FDR on secondary tests.

---

## Proposal A — Precision before prediction: generalizability of combine tracking measures and individual movement consistency in NFL play

**Research problem.**
- Combine-based prediction has been weak [#3, #10, #12]. One untested explanation is *measurement*: single-occasion combine quantities may be too imprecise to predict anything [#68, #77, #113].
- Separately, motor-control theory suggests skilled performers are *consistent in task-relevant dimensions* [#61–#64]. That idea has never been tested as an individual trait predicting team-sport performance.
- Phase 1.5 found that the combine contains only 1–2 repetitions per drill (75% single attempts). Individual consistency therefore cannot be estimated *from the combine*; it must be studied where repetitions exist, **in games**.

**Research questions.**
1. How reliable (within-session) are tracking-derived combine quantities, compared with official stopwatch results?
2. Is within-player variability of repeated in-game actions heterogeneous between players (a "consistency trait")?
3. Does in-game consistency add explanatory value for performance beyond the player's average level?

**Testable hypotheses.**
- **H-A1.** For the 40 (two attempts, n ≈ 375), tracking-derived peak speed has a within-session typical error ≤ 2% and an ICC(3,1) ≥ 0.85. Acceleration-side parameters (τ, A0) have a larger typical error than peak speed. This extends the expectation from [#31].
- **H-A2.** In a mixed-effects location-scale model of a repeated in-game action, an individual random effect on the residual SD improves expected log predictive density (LOO) over a homogeneous-variance model [#78, #81]. Examples of repeated actions: route-break braking on a given route type for WR/TE; get-off time for DL.
- **H-A3.** Lower task-relevant variability (scale) is associated with better position-matched outcomes, after adjusting for location, at |standardised β| ≥ 0.15 on the held-out class. Examples: separation at pass forward for WR/TE; time to pressure for DL.

**Research gap.**
- No reliability study of tracking-derived combine quantities was found.
- No location-scale (individual-consistency) model of athletic movement in team sports was found; the existing literature is psychology and health behaviour [#79, #80].

**Proposed methodology.**
1. *Reliability.* ICC(3,1) and (2,1) with confidence intervals [#70, #71]; typical error and CV [#68]. A small G-study with facets *attempt* and *side* (left/right drill variants) where the design allows [#83]. Day-to-day variance is **not estimable** (single combine).
2. *Location-scale model.* Bayesian hierarchical model: action-level outcome ~ Normal(μ_ij, σ_ij), where
   - log σ_ij = γ0 + u_j^σ + context terms;
   - μ_ij = β0 + u_j^μ + context terms;
   - (u^μ, u^σ) correlated [#78].
   Weakly informative half-t priors on SDs [#118]. Context includes down/distance, alignment and coverage from `player_play`.
3. *Prediction.* Player-level outcomes regressed on posterior location and scale, with uncertainty propagated (no plug-in point estimates).

**Baseline methods.** Raw within-player SD or CV; ICC with homogeneous variance; mean-only mixed model; official combine results.

**Potential novel contribution.**
- The first reliability benchmark for combine tracking quantities, which is useful to every other analysis as a regression-dilution correction [#113].
- A location-scale "consistency trait" for football movement.

**Experimental validation.**
- LOO and Bayes-factor comparison of homogeneous vs heterogeneous variance.
- Posterior predictive checks.
- Held-out-class test of H-A3.
- Simulation showing how many repetitions are needed to recover individual σ, which also documents why the combine cannot support it.

**Limitations.**
- The combine contributes only reliability, not consistency; this is a re-scoping of the original candidate.
- Within-session reliability overstates true test–retest reliability.
- In-game variability mixes motor consistency with scheme, opponent and assignment variability.
- Defining "the same action" requires labels (route type exists for WR/TE; other positions are harder).

**Practical NFL applications.**
- Error bars on combine tracking numbers, so scouts know which differences are real.
- A consistency profile for route runners and pass rushers, which coaches may value alongside peak ability.

---

## Proposal B — From capacity to expression: an exposure-aware hierarchical frontier model linking combine and in-game acceleration–speed profiles

**Research problem.**
- The combine measures *capacity* (maximal 40); games show *expression* under role constraints.
- In-situ A–S profiling estimates capacity from routine tracking [#27–#33]. It assumes athletes eventually perform near-maximal efforts [#28], uses heuristic envelope extraction [#27, #29, #30], and gives poor acceleration-side sensitivity [#31].
- In the NFL, opportunity to express capacity depends on role, so these assumptions fail, and the combine↔game link has never been quantified.

**Research questions.**
1. Can individual A–S capacity be estimated from NFL game tracking with calibrated uncertainty when exposure to maximal efforts varies by role?
2. How strongly does combine-day capacity (40 profile) transfer to in-game capacity, per position, after correcting for measurement error?
3. Does *utilisation* (expressed game performance relative to latent capacity) explain position-matched outcomes beyond capacity itself?

**Testable hypotheses.**
- **H-B1 (methodological; primary).** In simulations with role-dependent effort distributions and 10 Hz noise, the proposed estimator achieves:
  - lower RMSE for S0 and A0 than the binning, DBSCAN-cleaned [#29] and 95th/99th-percentile quantile-regression baselines;
  - 90% interval coverage within 85–95%.

  On real data, its split-half (by game) reliability for S0 is higher than the baselines'.
- **H-B2 (transfer).** The within-position correlation between combine-40 S0 and game S0, corrected for measurement error, is ≥ 0.5 for WR, TE and DB. We expect it to be weaker for OL, where game S0 is censored.
- **H-B3 (asymmetry).** Transfer is weaker for A0 than for S0, consistent with [#31].
- **H-B4 (discovery candidate; exploratory on 2023–24, confirmatory on 2025).** Utilisation has an incremental association with a pre-specified position-matched outcome, beyond combine capacity, draft pick and exposure (ΔR² or Δ log-likelihood with 95% CI excluding 0). Utilisation = posterior mean of game expression ÷ capacity in role-comparable situations. Outcomes: WR/TE separation at pass forward; DB cushion maintenance; DL time to pressure.

**Research gap.**
- In-situ A–S profiling has not been applied to American football.
- No combine↔game kinematic linkage was found.
- No in-situ method models opportunity or censoring, or propagates uncertainty.
- The combine literature has not used tracking [#11].

**Proposed methodology.**
1. *Signals.* Tangential acceleration a_t = ds/dt from smoothed speed (the provided `a` is an unsigned magnitude; Phase 1). The filter is chosen by simulation, with all processing documented [#42].
2. *Combine model.* Mono-exponential fit to each 40 attempt [#15] gives S0^c and A0^c, with attempt-level error from the two attempts. This is also Proposal A's H-A1.
3. *Game frontier model (the proposed algorithm).* For player j and frame i at speed s_ij:

   a_ij = A0_j (1 − s_ij / S0_j) − u_ij + ε_ij

   - u_ij ≥ 0 is the effort shortfall: exponential or half-normal, with a rate depending on context (play phase, assignment, route type).
   - ε_ij ~ N(0, σ²) is measurement noise.
   - (log A0_j, log S0_j) ~ bivariate normal by position (partial pooling).
   - An opportunity model: the probability that a frame belongs to a "maximal-intent" state.

   This adapts the stochastic-frontier formulation [Aigner et al. 1977] to the A–S line.
   - Fitted in Stan / NumPyro on subsampled frames, or by a variational approximation if needed.
   - Low-exposure players borrow strength and get *wide* intervals instead of biased point estimates.
   - A joint version links S0^game_j and S0^combine_j through a latent correlation, which gives H-B2 directly with error correction.
4. *Utilisation.* Posterior of expressed speed and acceleration in matched contexts ÷ latent capacity, carried forward as a distribution.

**Baseline methods.**
- Morin binning plus linear fit [#27];
- DBSCAN-cleaned fit [#29];
- boxplot-rule fit [#30];
- per-player quantile regression [Koenker & Bassett 1978];
- simple maxima (peak game speed; Phase 1 probe);
- official 40 time and 10-yd split [#5, #15].

**Potential novel contribution.**
- **Algorithm:** an exposure-aware hierarchical stochastic-frontier A–S estimator with calibrated uncertainty. It is a principled successor to heuristic in-situ profiling.
- **Science:** the first quantification of combine→NFL kinematic transfer, and a test of whether capacity *utilisation* carries performance information.

**Experimental validation.**
- Simulation benchmark (H-B1): RMSE, bias, coverage; sensitivity to exposure level and noise.
- Real-data reliability (split-half, season-to-season).
- Convergent validity with the combine (H-B2 and H-B3).
- Pre-registered incremental validity on the held-out class (H-B4), with permutation-based null distributions.
- Ablations: without hierarchy, without opportunity model, without the joint combine link.

**Limitations.**
- The main transfer result (H-B2) may be unsurprising; its discovery value rests on H-B4, which may be null.
- Utilisation can still encode role or scheme despite conditioning.
- Selection: exposure depends on draft capital.
- Game-tracking accuracy for acceleration is unvalidated [#54, #55].
- S0 for OL is weakly identified by design.

**Practical NFL applications.**
- Uncertainty-aware speed and acceleration capacity for every player, including low-snap players.
- "Is he playing as fast as he is?", a utilisation flag for coaching, deployment or medical follow-up.
- A bridge between scouting (combine) and pro evaluation (game) on one physical scale.

---

## Proposal C — The cost of turning: a capacity-constrained minimum-time model separating braking/COD execution from athletic capacity, from combine drills to NFL cuts

**Research problem.**
- COD ability is measured as total time or as a time-difference deficit [#44–#46]. These ignore *the path actually run* and *the athlete's own physical limits*.
- Lab biomechanics identifies braking and approach/exit speed as determinants [#47, #49], but only in pre-planned lab tasks.
- Combine agility and position drills, and every in-game cut, are recorded as trajectories. That allows an athlete-specific, physics-based counterfactual: how fast *could this athlete* have run *this path*?

**Research questions.**
1. Can observed COD time be decomposed into a **capacity cost** (physical limits) and an **execution cost** (deviation from the athlete's own minimum-time profile), estimated reliably from 10 Hz tracking?
2. Is execution cost distinct from linear speed and stable across drills and attempts?
3. Does combine execution cost transfer to in-game cuts, and does it explain position-matched outcomes beyond speed and standard COD metrics?

**Testable hypotheses.**
- **H-C1 (methodological; primary).** In simulation (synthetic athletes with known limits plus a known execution inefficiency on realistic drill paths, sampled at 10 Hz with noise), the CCMT execution cost recovers the true inefficiency with r ≥ 0.8. The COD deficit and peak-braking baselines are confounded by path geometry and linear speed (lower r).
- **H-C2 (discriminant validity).** On combine data, |r(execution cost, 40 time)| ≤ 0.2, while r(execution cost, 3-cone time) ≥ 0.4. This mirrors the COD-deficit logic of [#44] on a path-aware basis.
- **H-C3 (stability).** Execution cost has cross-drill consistency (agility vs skill drills) and attempt reliability (two-attempt subset) higher than COD deficit computed on the same attempts.
- **H-C4 (transfer and incremental validity; exploratory 2023–24 → confirmatory 2025).**
  - Combine execution cost correlates positively with in-game execution cost on matched cut types.
  - It adds explanatory value for WR/TE separation at pass forward, and DB cushion or coverage outcomes, beyond 40 time, 3-cone time, COD deficit, draft pick and the Proposal B capacity estimates.

**Research gap.**
- No trajectory-based, athlete-specific COD measure in the retrieved sports literature.
- The minimum-time-on-path idea exists in vehicle dynamics [Velenis & Tsiotras 2008; Lipp & Boyd 2014] but was not found applied to human COD.
- Combine COD mechanics have not been linked to in-game COD in American football.
- Deceleration measurement validity for NFL tracking is unestablished.

**Proposed methodology.**
1. *Path and signal processing.*
   - Smoothing spline or penalised regression on x(t), y(t) gives arc length s, curvature κ(s), speed v(s) and tangential and normal acceleration.
   - The smoothing parameter is selected in simulation, and all steps are reported [#42].
   - Frames with v < v_min are excluded from heading-based quantities (Phase 1).
2. *Athlete limits.*
   - Forward: the A–S line (A0, S0) from Proposal B.
   - Braking: D_j.
   - Lateral: C_j(v), a speed-dependent centripetal limit; bend sprinting shows curvature costs speed and differs between individuals [#52, #53].
   - D_j and C_j are estimated as frontiers (same machinery as B) over in-game and combine data.
3. *CCMT solver (the proposed algorithm).*
   - Given path κ(s) and the limits, compute the maximal feasible speed profile v*(s) by:
     - a curvature cap v ≤ √(C_j/κ);
     - a forward pass limited by A0(1 − v/S0);
     - a backward pass limited by D_j;
     - their pointwise minimum.
   - This is the forward–backward scheme used for minimum-time profiles on a fixed path [Velenis & Tsiotras 2008]; a convex formulation is also available [Lipp & Boyd 2014].
   - T*_j = ∫ ds / v*(s).
4. *Decomposition.*
   - Execution cost = T_obs − T*_j(own limits).
   - Capacity cost = T*_j(own limits) − T*_ref(position reference limits).
   - Uncertainty is propagated by sampling limits from the B/C posteriors.
5. *Game application.* Cuts are segmented from route-running (WR/TE) and backpedal-break (DB) sequences using curvature and braking events, typed by angle as in [#51]. The same decomposition is applied.
6. *Inference.* Hierarchical models for reliability and transfer; pre-registered player-level incremental-validity tests, with measurement error from Proposal A.

**Baseline methods.**
- Total drill time (official and tracking);
- COD deficit [#44] and percentage COD deficit [#46];
- deceleration deficit [#45];
- peak braking and peak |a|;
- FPCA scores of drill speed curves [#89, #91];
- DTW distance to a position template [#108].

**Potential novel contribution.**
- **Algorithm:** CCMT, an athlete-specific, physics-constrained counterfactual that turns any trajectory into capacity and execution components. It applies equally to standardised drills and in-game cuts.
- **Science:** evidence on whether *how* an athlete turns, separately from how fast they are, transfers from combine to NFL and relates to separation and coverage. That would be a non-obvious finding if supported.

**Experimental validation.**
- Simulation recovery (H-C1), with sensitivity to sampling rate, noise and smoothing.
- Discriminant validity (H-C2).
- Reliability and cross-drill consistency (H-C3).
- Transfer and pre-registered incremental validity on the held-out class (H-C4).
- Ablations: constant vs speed-dependent lateral limit; with vs without athlete-specific limits; CCMT vs COD deficit.

**Limitations.**
- 10 Hz cannot resolve foot contacts; mechanics are inferred at centre-of-mass level only.
- Curvature from noisy positions is fragile.
- Agility-drill participants are self-selected (≈ 1/3 of players).
- Combine COD is pre-planned while game COD is reactive [#49].
- Separation depends on defenders and scheme.
- Game deceleration accuracy is unvalidated [#54, #55].
- CCMT depends on B's capacity estimates, so B is a prerequisite.

**Practical NFL applications.**
- A scouting metric for "wasted time in cuts" that is not just speed, with error bars.
- Coaching feedback that locates where in a cut time is lost (entry speed vs braking vs re-acceleration).
- Comparison of a prospect's combine COD execution with how pros execute game cuts.
- A potential load-monitoring link to braking demands [#38, #40] (outside our outcome data; not claimed).
