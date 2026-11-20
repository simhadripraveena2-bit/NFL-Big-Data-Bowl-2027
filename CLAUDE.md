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
- **Research hypothesis: NOT finalised — awaiting approval.**
- Phase 2: **not started — awaiting approval.** No preprocessing, no feature engineering, no models trained.

## Data facts that must not be forgotten (verified in Phases 1–1.5)

- `a` is an **unsigned** acceleration magnitude (combine and game). Derive signed / braking acceleration from `s`.
- Combine `dis` is **not** per-frame displacement (≈0.46×). Derive distance from `x, y`. Game `dis` is fine.
- `dir` follows NGS: 0° = +y, clockwise. `o` exists only in game data.
- Game tracking contains **only the 510 cohort players**: no ball, no other players.
- WR/TE game rows contain **only route-running dropbacks**. OL/DL/DB rows include run plays.
- Exclude faulty game 2025101205 (plays 1289, 1314) and spikes with `s` > 12.5 yd/s.
- Harmonise drill-name synonyms across years before pooling.
- Same-drill repetitions are scarce: 75% of (player, drill) pairs have one attempt; only the 40 has two attempts for most players (90%).
- Unit of inference is the **player** (n ≈ 500; 63–77 per position with ≥100 REG plays). Split by player, never by frame or play.

## Literature rules (Phase 1.5)

- Cite only papers whose DOI has been verified. State whether the abstract or full text was read. Never attribute findings to metadata-only references.
- Before any novelty claim, read the full texts of the closest prior work: Morin 2021, Miguens 2024, Clark 2019, Silva 2026, Nimphius 2016, Chu 2020, Hedeker 2008.
