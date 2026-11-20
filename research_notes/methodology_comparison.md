# Methodology Assessment and Candidate Comparison — Phase 1.5

*References like [#n] point to `literature_review.md`. The fit judgements use the data facts from Phase 1 and
Phase 1.5:*
- *n ≈ 500 players;*
- *1 attempt per drill for 75% of (player, drill) pairs;*
- *two 40 attempts for 90% of 418 sprinters;*
- *one combine occasion;*
- *10 Hz;*
- *hundreds of in-game repetitions per player;*
- *unsigned `a`.*

## 1. Which methods genuinely fit the available data?

| Method | What it needs | What our data offers | Verdict | Where it fits |
|---|---|---|---|---|
| **Functional data analysis (smoothing, derivatives)** | Densely sampled curves; a principled smoother | 10 Hz curves of 2–21 s; derivatives needed for braking | **Fits, and is essential.** Penalised smoothing with derivative estimation is the right way to get a_t, curvature and braking from positions; it is the core preprocessing for B and C [#84, #85] | B, C (signal layer) |
| **FPCA** | Many comparable curves on a common domain, registered | The 40: n ≈ 418 comparable curves. Skill drills: ~100 curves per drill, 1 attempt, heterogeneous paths | **Fits narrowly.** For the 40, Clark 2019 shows fast and slow athletes share τ [#15], so FPCA will probably rediscover the 2-parameter model (Ettema's warning [#24]). For skill drills, phase variation dominates and registration choices drive results [#88, #94]. Use as a **baseline** and diagnostic, not as the contribution | Baseline in C; check of B's 2-parameter adequacy |
| **Multivariate / bivariate FPCA** | Concurrent multi-channel curves | x, y, s per drill | Possible for path *shape* [#90, #95], with the same registration problems; low priority | Optional in C |
| **Hierarchical Bayesian models** | Grouped data, small groups, need for uncertainty | 5 positions × 21–122 players; uneven exposure (frames per player-season: 10th–90th percentile ~1.6k–68k) | **Strong fit.** Partial pooling is the principled answer to small per-position n and censored exposure, and gives calibrated intervals for downstream use [#118, #97, #98] | B (frontier), C (limits), A (location-scale) |
| **ICC** | ≥ 2 repeated measurements per subject | 40: 2 attempts (n ≈ 375); other drills: 2 attempts for 15–35% | **Fits for the 40 only**; partial elsewhere. Report the ICC form, CI and absolute error, never ICC alone [#70, #71, #77] | A (H-A1); measurement error for B and C |
| **Generalizability theory** | Crossed or nested facets (occasion, attempt, rater, side) | Facets: attempt (2), side (left/right variants for some drills). **Occasion facet absent** | **Weak fit.** A small G-study is possible, but the most important facet (day) is missing, so the dependability coefficient overstates true reliability. Mention it; don't lead with it [#83] | A (secondary) |
| **Dynamic time warping** | Sequences whose *timing* is nuisance | In speed and COD research, **timing is the outcome** | **Mostly unsuitable.** Warping removes the time differences we want to measure. Acceptable only for aligning phases (e.g. finding the break point) or as a shape-distance baseline [#107–#109]. Landmark registration (turn events) is more defensible [#88] | Baseline in C |
| **Time-series representation learning (self-supervised encoders)** | Large numbers of sequences; downstream labels | 315k player-plays (enough to pre-train) but **~500 athletes** for any athlete-level claim; no physical interpretability | **Not as a primary method.** Embeddings could overfit athlete-level outcomes, are hard to defend physically, and do not address the standards' "explainable discovery" requirement. Use as a *black-box upper-bound baseline* for predictive comparisons [#105, #106] | Optional baseline in B or C |
| **Mixed-effects models** | Repeated, unbalanced observations | Plays nested in players, games and teams; attempts nested in players | **Strong fit and required.** Repeated-measures designs otherwise discard data [#116]; standard in NFL tracking metrics [#101] | All |
| **Mixed-effects location-scale** | Many repetitions per person (≥ ~10) | Combine: no. Games: yes | **Fits only for in-game data** [#78–#81] | A (re-scoped) |
| **Measurement-error models / regression calibration** | Repeat measurements or known error variance | 40 duplicates; posterior SDs from hierarchical fits | **Strong fit and required.** Single-occasion combine predictors will otherwise attenuate every association [#113, #115] | All (outcome analyses) |
| **Stochastic frontier / quantile regression** | Outcome with an upper envelope | Acceleration at a given speed is bounded by capacity; most frames are sub-maximal | **Strong fit for B.** Frontier models give an explicit inefficiency term and uncertainty; quantile regression is the natural baseline [Aigner 1977; Koenker & Bassett 1978] | B (core), C (limits) |
| **Minimum-time speed profile on a path** | Path geometry plus acceleration limits | Paths from x, y; limits from B and C | **Fits C, and is the novel element.** Simple forward–backward or convex computation [Velenis & Tsiotras 2008; Lipp & Boyd 2014] | C (core) |

**Net recommendation on methods.** The defensible core is:
- penalised functional smoothing;
- hierarchical Bayesian frontier models;
- a physics-based minimum-time counterfactual;
- mixed-effects / measurement-error inference.

FPCA, DTW and representation learning serve as **baselines that the proposed methods must beat**, not as the contribution. G-theory and individual-level ICC are limited by the single-occasion, few-attempt design.

## 2. Comparison matrix

Scores: 1 (poor) to 5 (excellent). The **rationale is the important part**; totals are only a summary.

| Criterion | A — Consistency (as specified: combine attempts) | A′ — Re-scoped (reliability + in-game location-scale) | B — Speed/accel transfer (exposure-aware frontier) | C — Braking/COD (capacity-constrained minimum time) |
|---|---|---|---|---|
| **Novelty potential** | 3 — individual consistency as a trait is new in team-sport testing | 3 — the reliability part is incremental; the in-game consistency trait is new | 3 — in-situ A–S exists [#27–#33]; new are the NFL application, exposure-aware frontier and combine↔game link | **4** — no trajectory-based, athlete-specific COD counterfactual found; the vehicle-dynamics idea is new to sports *as far as we found* |
| **Technical depth** | 3 | 3 | 4 — hierarchical frontier with opportunity model and joint combine link | **5** — functional derivatives + frontier limits + path optimisation + uncertainty propagation |
| **Feasibility with available data** | **1** — 75% single attempts; individual variance not identifiable | 3 — reliability feasible for the 40; in-game action labels clean only for WR/TE routes | **5** — 418 tracked 40s, large game exposure | 3 — 10 Hz differentiation noise, curvature fragility, self-selected agility subset (~1/3); skill drills cover all |
| **Statistical power** | 1 | 2 — the H-A3 outcome test is per position (n ≈ 63–77) | 4 — the transfer test uses ~300+ players; incremental tests per position are weaker | 3 — combine-side reliability and validity well powered; game-outcome tests per position (n ≈ 63–75, TE 21) |
| **Potential football impact** | 2 | 3 | 4 — capacity and utilisation on one scale across scouting and pro play | **5** — COD and cut efficiency are central to WR/DB evaluation and coaching, and actionable |
| **Ability to demonstrate improvement over baselines** | 2 | 3 | **5** — clean ground-truth simulation vs explicit published heuristics, plus real-data reliability | 4 — simulation recovery vs COD deficit is clean; real-data superiority depends on noisy outcomes |
| **Publication potential** | 2 | 3 (sports-science methods) | 4 (sports-science / statistics venues: frontier method + NFL application) | 4–5 (strong if H-C2/H-C3 hold; the method is portable to all tracked sports) |
| **Total (/35)** | **14** | **20** | **29** | **28** |

### Critical notes (why these scores are not higher)

**A**
- The appealing story (consistency = skill) is supported by theory [#61–#64], but the **data cannot carry it at the combine**.
- Re-scoping to games makes it feasible but changes the question.
- Its most valuable output is infrastructure: reliability estimates and measurement-error correction that make B and C credible.

**B**
- The most feasible and the most *demonstrable* candidate.
- Its **discovery potential is the weakest**: "faster at the combine → faster in games" is expected [#35, #36].
- A genuine Eureka result would need H-B4 (utilisation predicts outcomes beyond capacity), which may well be null or explained by role.
- The algorithmic contribution (exposure-aware frontier) is real but builds on an existing econometric idea applied to an existing sports-science model.

**C**
- The highest ceiling: new method, plausible non-obvious finding ("how you turn, not how fast you are").
- The highest **measurement risk**:
  - (i) 10 Hz positions → second derivatives → braking and curvature;
  - (ii) unvalidated deceleration accuracy for NFL tracking [#54, #55];
  - (iii) the metric could collapse onto linear speed, as raw COD time does [#50]. H-C2 is designed to catch this early.
- C **depends on B** for athlete-specific acceleration limits.

**Not ranked higher for being complex.** Representation learning, DTW and FPCA-led proposals were considered and rejected as primary approaches:
- they are not interpretable;
- they are mismatched to athlete-level n;
- DTW destroys the timing signal;
- FPCA risks re-describing the 2-parameter sprint model [#24].

## 3. Ranking (for discussion; no hypothesis is finalised)

1. **B — exposure-aware frontier transfer model (29/35).** Highest feasibility and clearest demonstrable improvement over published baselines. Weakest discovery potential on its own.
2. **C — capacity-constrained minimum-time COD model (28/35).** Highest novelty and impact ceiling. Highest measurement risk. Requires B's capacity estimates.
3. **A′ — re-scoped consistency (20/35)**, then **A as specified (14/35)**. Not viable as a standalone combine study; valuable as the reliability / measurement-error layer.

**Observation for the decision (not a decision).**
- B and C are naturally *sequential*: B's frontier estimator provides the athlete limits that C's counterfactual needs.
- A's reliability analysis supplies the error model both require.
- A programme of **A-reliability → B → C** would satisfy all three CLAUDE.md standards:
  - technical contribution: the frontier and CCMT algorithms;
  - candidate discovery: H-B4 / H-C4;
  - algorithmic improvement over baselines: the simulation and reliability benchmarks.
- The cost is that the programme is larger, and the discovery hinges on hypotheses that may be null.

**Early go/no-go checks (decide before heavy investment):**
- (a) B's simulation (H-B1) must beat the baselines.
- (b) C's discriminant check (H-C2) on combine data alone must show execution cost is not just linear speed.
- Both are cheap and use no game-outcome data, which protects the confirmatory tests.
