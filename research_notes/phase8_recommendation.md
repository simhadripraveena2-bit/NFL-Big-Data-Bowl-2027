# Phase 8 recommendation

**Status:** recommendation only. **No implementation, training or modelling has been started.** The completed empirical study and its preregistration are unchanged.

## 1. Evidence base, and its main limitation

- The literature review (`related_work_full_text_review.md`) could **not** read any paper in full in this session. The full-text hosts were unreachable from the session's page fetcher, even after the project lead approved adding them to the environment.
- Evidence is therefore **abstract-level** (Phase 1.5) or **search-level** (Phase 8).
- Consequences:
  - The ranking below is provisional.
  - **No novelty claim is made.**
  - The recommendation is conditional on a full-text check of the named closest works.

## 2. Scoring (1 = weak, 5 = strong)

| criterion | G1 exposure-aware capacity | G2 acceleration / braking / turning capacity | G3 capacity vs deployment | G4 crossed bootstrap |
|---|---|---|---|---|
| technical novelty (provisional) | 3 | 3 | 3 | 2 |
| scientific significance | 4 | 4 | 4 | 3 |
| feasibility | 4 | 2 | 2 | 5 |
| data availability (ability to *validate*) | **5** | 2 | 1 | 4 |
| strength of available baselines (higher = clearer benchmark) | 4 | 3 | 2 | 4 |
| potential for measurable improvement | 4 | 3 | 2 | 3 |
| **total (/30)** | **24** | 17 | 14 | 21 |

**Notes on the scores:**
- **Novelty for G1 is scored only 3**, because two 2025–2026 works are close: an NFL quantile A–S effort report, and a quantile motion-feasibility model. Neither could be read.
- **G4 scores high on feasibility, but low on novelty**, because the pigeonhole and Owen–Eckles bootstraps exist.
- **G3 is scientifically important but weakly identifiable** with these data.

## 3. Recommended direction: G1

**Exposure-aware estimation of latent athlete speed capacity from sub-maximal, context-dependent game tracking, validated against combine tracking.**

**Why G1:**
1. **It targets a problem our own study exposed.**
   - Observed game maxima depend on exposure and role (Phase 2).
   - Match peak speed is known to sit below test maxima, and to depend on situation (literature, search level).
   - Yet "game top speed" is used as an athlete trait in applied models (e.g. player-specific top speeds in pitch control).
2. **The competition data has an unusual asset: an external near-capacity measurement for the same athletes.**
   - Combine tracked 40 peak speed, within-position reliability 0.94–0.99.
   - It allows held-out, exposure-stratified validation that most tracking studies cannot do.
3. **Clear, strong baselines exist:** observed max, top-k mean, high quantile, in-situ A–S S0, per-athlete quantile curves, stochastic frontier, and hierarchical mean models. Improvement can be measured on identical splits.
4. **It reuses validated infrastructure:** the single join, real-design simulation skeletons, player-grouped cross-validation and season-forward splits.

**What success would mean (to be pre-specified before any model is fitted):**
- **(a) Exposure invariance.** Estimates for the same player change less across subsampled exposure levels than the baselines' do.
- **(b) External validity.** Higher within-position rank agreement with combine peak speed, and calibrated interval coverage, on held-out players.
- **(c) Unseen athletes.** Calibrated predictions for players with few plays.
- **(d) Simulation recovery.** Of known capacities under realistic opportunity distributions.

**Known risks, stated in advance:**
- **Construct gap.** Combine straight-line peak speed is not identical to game capacity (equipment, flying vs standing start, context). Validation therefore targets ranking, calibration and exposure invariance, not levels.
- **Prior work.** The closest works may already model exposure. If so, the direction must be narrowed or dropped. **The full-text check comes first.**
- **Selection.** Players with more opportunities differ systematically, which ties into G3. The design must separate exposure (a count) from selection (who gets it).

## 4. Proposed next steps (only after approval)

1. **Restore full-text access.** Start a new session on the updated environment (arxiv.org, PubMed Central, Europe PMC and Springer are now allowed), or supply the PDFs.
2. **Full-text review**, recording all Task 1 fields, of:
   - Gutiérrez-Pérez & Agudo 2026;
   - Shteynberg et al. 2025;
   - Nguyen & Yurko 2026 and 2025;
   - Morin 2021 and Miguens 2024;
   - SFA (Aigner 1977, plus panel and hierarchical SFA);
   - order-α / extreme-value frontier work (Daouia et al.);
   - Brefeld 2019 and Narizuka 2023.
   Then update the evidence levels and **re-score G1–G4**.
3. **Only if G1 survives:** write a methods pre-registration covering:
   - the estimand;
   - the baselines;
   - the exposure-subsampling protocol;
   - the held-out and season-forward splits;
   - the metrics and significance tests;
   - the simulation design;
   - the algorithm in pseudocode, with its complexity.
4. **No modelling before that pre-registration is approved.**

## 5. Explicitly not claimed

- That G1 (or any candidate) is novel.
- That combine peak speed *is* game capacity.
- That any of the four candidates has been, or can be, validated before the steps above.
