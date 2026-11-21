# CLAUDE.md — NFL Big Data Bowl 2027 Research Project

Guidance for Claude (and any collaborator) working in this repository.

## Research objectives

1. Produce a PhD-level, publication-quality analysis for the **NFL Big Data Bowl 2027**
   Kaggle competition (`nfl-big-data-bowl-2027`, deadline 2027-01-06 23:59 UTC).
2. Use player-tracking data (2023–2025 game tracking, NFL Combine tracking), play-level and
   player-level tables to answer a question that matters to football decision-makers.
3. Deliver a rigorous, reproducible pipeline: raw data → validated features → models →
   uncertainty-quantified results → paper/notebook submission.
4. Every claim must be supported by evidence that survives held-out validation and
   reasonable robustness checks.

## The three research standards (non-negotiable)

Every proposed direction, experiment and final result is judged against all three.

### 1. Advanced technical contribution
- Methods must go beyond off-the-shelf summary statistics or default model fits:
  e.g. spatio-temporal / graph / sequence models, causal inference, Bayesian hierarchical
  modelling, physics-informed or kinematic constraints, proper uncertainty quantification.
- Rigor: leakage-free splits (by game/week/season, never random frames), baselines,
  ablations, calibration, confidence intervals, and stated assumptions.
- Reproducible: seeded, configuration-driven, runnable from scripts.

### 2. A genuinely novel "Eureka-style" discovery
- Aim for an insight that is *surprising yet obviously true in hindsight* — something that
  changes how a coach, scout or analyst would think, not a re-confirmation of known facts.
- Before claiming novelty, check prior Big Data Bowl winners/finalists and the public
  sports-analytics literature; document what is known and how our finding differs.
- A discovery must be stated as a falsifiable hypothesis, tested out-of-sample, and stress
  tested against confounders (game state, personnel, opponent, season, tracking noise).

### 3. A potentially new algorithm that improves on existing approaches
- Propose a method (metric, model, or estimation procedure) with a clear statement of what
  it improves on: accuracy, calibration, interpretability, data efficiency, or compute.
- Benchmark head-to-head against the strongest reasonable existing approach on identical
  splits, with statistical significance of the improvement.
- Write the algorithm down precisely (pseudocode + complexity) so it can stand on its own.

## Working rules

- **Data never leaves the machine via git.** Raw/derived competition data, model
  artifacts and credentials are git-ignored. Never `git add -f` anything under `data/`.
- **Credentials:** read Kaggle credentials only from the environment
  (`KAGGLE_API_TOKEN`, or `KAGGLE_KEY` holding a `KGAT_` token). Never print, log or commit them.
- **Phase gating:** do not start a new phase (EDA → features → modelling → write-up)
  without explicit approval from the project lead.
- Put reusable code in `src/nfl_bdb/`; notebooks are for exploration and narrative only.
- Read large tracking CSVs with chunked/columnar tools (polars / pyarrow); convert to
  Parquet under `data/interim/` rather than repeatedly parsing CSV.
- Log every experiment (config, seed, split, metrics) under `experiments/`.

## Current status

- Phase 0 (setup): complete.
- Phase 1 (dataset exploration): complete. See `notebooks/01_dataset_exploration.ipynb` and `research_notes/`.
- Phase 1.5 (literature review and research-gap identification): complete. See:
  - `research_notes/literature_review.md` (123 verified papers: 106 abstracts read, 2 summary-only, 15 metadata-only; no full texts);
  - `research_notes/research_gap_analysis.md`;
  - `research_notes/research_proposals.md` (3 candidate proposals);
  - `research_notes/methodology_comparison.md` (method fit + ranked comparison matrix).
  - Current ranking, for discussion only: B (exposure-aware A–S frontier, 29/35) > C (capacity-constrained minimum-time COD, 28/35) > A′ (re-scoped consistency, 20/35) > A as specified (14/35, not identifiable from combine data).
- Phase 1.6 (feasibility simulations for the approved B + C programme, "Athletic Capacity and Movement Efficiency"): complete. See:
  - `research_notes/candidate_b_feasibility.md` (Experiment 1);
  - `research_notes/candidate_c_feasibility.md` (Experiment 2);
  - `research_notes/feasibility_comparison.md` (comparison + recommendation);
  - notebooks 02/03; `scripts/run_capacity_simulation.py`, `scripts/run_cod_simulation.py`; figures `reports/figures/sim_*.png`.
  - Headline (simulation only):
    - B: measurement and preprocessing dominate. SIMEX halves the S0 bias, but A0 is best from plain binning, and pooling hurts calibration.
    - C: the CCMT execution cost beats the COD deficit only with precise athlete limits (≤ 5% A0/S0, ≤ 10% D/C).
- Phase 2 (real-data feasibility validation): complete. See:
  - `research_notes/real_data_capacity_transfer.md`;
  - `research_notes/braking_estimation_validation.md`;
  - `research_notes/lateral_constraint_validation.md`;
  - `research_notes/combine_execution_cost.md`;
  - notebooks 04/05; scripts `run_real_capacity.py`, `run_real_movement.py`, `run_real_combine_execution.py`.
  - Headline:
    - Speed capacity: rankings transfer partially within position (peak ↔ game max ρ 0.13 DB to 0.73 DL); game levels are far lower than combine levels.
    - Game A0: not measurable (implausible values grow with exposure).
    - D99 braking and C99 lateral envelopes: robust, but they are demonstrated, context-dependent envelopes, not capacities.
    - CCMT execution cost: not yet valid on real combine data (timing validity, non-identifiable limits, weak reliability; shuttle unusable).
- Phase 3 (performance-linkage discovery, outcome-blind screening): complete. See:
  - `research_notes/game_outcome_inventory.md`, `position_specific_metrics.md`, `temporal_matching_report.md`, `phase3_hypothesis_screening.md`;
  - `scripts/run_phase3_screening.py` (stages `features`, `analyse`).
  - Recommended (awaiting approval): H1 demand-moderated speed translation + H2 WR deep-route separation; H5 (OL) as negative control; H3 (DL) and H4 (DB) exploratory.
  - No combine x game-performance association has been computed yet. Pre-register before the first join.
- Phase 3.5 (pre-registration + power): complete. See:
  - `research_notes/preregistration.md` (frozen protocol v1.0), `statistical_model_specification.md`, `power_analysis.md`, `notebooks/06_power_analysis.ipynb`;
  - `scripts/run_power_analysis.py`, `src/nfl_bdb/models/power.py`, `src/nfl_bdb/data/play_table.py` (frozen contexts/covariates).
  - Approved title: "Task-Conditioned Translation of Athletic Capacity". Primary = fixed sequence H1-WR (deep vs short) -> H2 (WR deep separation, peak | 40). H1-DB demoted to secondary (power). H5 = OL comparison (secondary).
  - Power: H1-WR MDE delta-rho ~0.30; H2 MDE partial r ~0.6 (power ~0.3 at 0.3); players, not plays, limit power.
- **Research hypothesis: pre-registered (v1.0). Any change after the first combine x outcome join goes in the protocol's deviations log.**
- Phase 4 (synthetic validation of the confirmatory pipeline): complete. See:
  - `research_notes/synthetic_validation.md`, `demand_measure_validation.md`, `selection_bias_analysis.md`, `notebooks/07_synthetic_pipeline_validation.ipynb`;
  - `src/nfl_bdb/models/{reml,confirmatory,validation_summary}.py`, `src/nfl_bdb/simulation/confirmatory_sim.py`, `src/nfl_bdb/features/demand.py`;
  - `scripts/run_synthetic_validation.py` + `scripts/phase4_stages.py` (run id 20261121T023847Z), `scripts/build_notebook_07.py`.
  - Headline: the registered full REML bootstrap is valid but conservative for H1-WR (null size <= 0.0125; power 0.45 at delta 0.2, 0.94 at 0.35). The registered fallback (moment bootstrap) is liberal for WR (0.045) and invalid for DB (0.225). H2 is estimation-only (full support <= 0.035). Fixed-sequence FWER <= 0.02.
  - Proposed deviations awaiting approval (NOT implemented): D1 retire the fallback; D2 (optional) fix the crossed-design bootstrap; D3 combine-only 40 test-retest + EIV tipping point.
- Pre-join (approved): D1 retire fallback (approved), D2 (rejected), D3 40 test-retest (done: `forty_test_retest.md`; within-WR R_x 0.94, not 0.987) logged in preregistration §15. Code frozen at `955d94d` (`research_notes/code_freeze.json` + `tests/test_code_freeze.py`).
- **The single combine x outcome join has been performed** (run 20261121T135032Z, `scripts/run_confirmatory_join.py`, outputs in `data/interim/confirmatory_join/`). See `research_notes/join_validation_report.md`: all registered sample sizes reproduced, 0 duplicates, raw unchanged.
- D4 approved (Option A): H2 demoted to secondary, estimation-focused (logged in §15). Hierarchy: H1-WR sole primary; H2 secondary estimation; Holm secondary family {H1-DB, H1-DL(a), H1-DL(b), H5(b)} unchanged; H5(a)/(c), H1-global estimation; TE descriptive.
- Pre-model audit passed (`research_notes/pre_model_audit.md`, `scripts/run_pre_model_audit.py`): frozen code unchanged, single join unchanged, rules re-verified, sample sizes = registered.
- **H1-WR confirmatory analysis done (run 20261121T223645Z, commit 8674e80, seed 4004, B = 2000): INCONCLUSIVE.** Delta = 0.090 (rho deep 0.576 / short 0.486), 95% CI [-0.089, 0.400], SE 0.122, p = 0.211; 2025 season-forward same sign (0.219); not falsified (90% upper 0.333 > 0.15). Equal raw slopes (~0.11 yd/s per 0.25 yd/s). See `research_notes/h1_wr_confirmatory_results.md`, notebook 08. The runner refuses a second run.
- Secondary analyses (H2, Holm family, H5, TE) and the H1-WR robustness grid: **not run — awaiting review.**
- Confirmatory H1 must use `confirmatory.h1_registered_test` (full REML bootstrap, B = 2000). Never `h1_procedure`.

## Data facts that must not be forgotten (verified in Phases 1–1.5)

- `a` is an **unsigned** acceleration magnitude (combine and game). Derive signed / braking acceleration from `s`.
- Combine `dis` is **not** per-frame displacement (≈0.46×). Derive distance from `x, y`. Game `dis` is fine.
- `dir` follows NGS: 0° = +y, clockwise. `o` exists only in game data.
- Game tracking contains **only the 510 cohort players**: no ball, no other players.
- WR/TE game rows contain **only route-running dropbacks**. OL/DL/DB rows include run plays.
- Exclude faulty game 2025101205 (plays 1289, 1314) and spikes with `s` > 12.5 yd/s.
- Harmonise drill-name synonyms across years before pooling.
- Same-drill repetitions are scarce: 75% of (player, drill) pairs have one attempt; only the 40 has two attempts for most players (90%).
- Game-derived braking (D99) and lateral (C99) values are *demonstrated envelopes*. Never use them as capacity limits: they make combine drills "impossible" (negative execution cost).
- Use a_t (from positions or speed) for braking, never the provided `a`. In sharp turns, 22–33% of |a|² is turning.
- Game A0 by binning is implausible (> 15 yd/s²) for 22% of high-exposure players. Use robust peak-speed measures for game speed capacity.
- Real combine drill timing from tracking: 3-cone r = 0.65 with official time; shuttle r = 0.40 and not repeatable.
- Within-position reliability must be reported; pooled reliabilities are inflated by position differences.
- Outcomes are **REG season only** (competition wording). PRE/POST rows exist in player_play: exclude PRE; POST only as robustness.
- Defender pressure has no flag: pressure generated = `time_to_pressure` non-null. Run play = `pass_result == ""`. `NO_ASSIGNMENT` = rusher (not a coverage snap). DL `blitzing` behaves as a rushing flag.
- `separation_at_pass_forward` exists for all routes on thrown passes (not sacks or scrambles) and is reproduced exactly from tracking. There is no DB coverage-performance outcome.
- Context adjustment removes much apparent player signal (WR short-route separation reliability 0.75 -> 0.22). Always report adjusted reliability.
- In DL, forty / 10-yd split / peak speed / weight are one dimension (|rho| 0.80-0.97): no incremental-over-40 test is possible.
- Pre-registration firewall: never join combine predictors to game outcomes before the confirmatory phase is approved. Verify the confirmatory pipeline on simulated data with planted effects first.
- Route depth (frozen): deep = GO/POST/CORNER/WHEEL; short = HITCH/SLANT/OUT/FLAT/SCREEN/ANGLE; IN/CROSS excluded as ambiguous.
- Unit of inference is the **player** (n ≈ 500; 63–77 per position with ≥100 REG plays). Split by player, never by frame or play.

## Phase 4 rules

- The REML player-cluster bootstrap shares team-season columns between duplicated players. This inflates s2_team, shrinks Sigma_b and over-disperses rho* (size <= 0.0125 vs 0.025). Do not "fix" it silently: it is registered.
- Never use the moment fallback (pooled residualisation) for decisions. Common covariate effects across contexts flip the DB man/zone correlation (-0.33 vs registered +0.36) and bias DB delta by +0.28.
- Report H1 under selection against the selected-population target: selection on deep-route level inflates the target delta by ~0.04.
- A play-level CV split is optimistic by ~0.02 in delta-R2, which equals the H2 threshold. Always fold by player.

## Simulation rules (Phase 1.6)

- Development seeds (101–103) are for design only. Evaluation uses disjoint seeds. Never tune on evaluation output.
- Every estimator in a comparison uses identical preprocessing. Smoothing window, sampling rate and noise are sensitivity factors.
- Simulated improvements are never reported as real-world validity.
- Base tracking noise is 0.01 yd: it matches real game Δ²x and Δ²s statistics.
- When building polars frames from lists of dicts, pass `infer_schema_length=None`. Columns missing from early rows are silently dropped otherwise (this bug cost one rerun).

## Memory rule (Phase 2)

- Loading all game seasons with many derived columns exceeds 15 GB. Process per season, write float32 frame tables to `data/interim/`, aggregate lazily, and run heavy pipelines one at a time.

## Literature rules (Phase 1.5)

- Cite only papers whose DOI has been verified. State whether the abstract or full text was read. Never attribute findings to metadata-only references.
- Before any novelty claim, read the full texts of the closest prior work: Morin 2021, Miguens 2024, Clark 2019, Silva 2026, Nimphius 2016, Chu 2020, Hedeker 2008.
