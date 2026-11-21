# Phase 3, Tasks 4–5: Hypothesis Screening and Research Design

*Inputs:*
- `game_outcome_inventory.md`, `temporal_matching_report.md`, `position_specific_metrics.md`;
- Phase 2 notes;
- run `experiments/phase3_screening/20261121T010253Z`.

**Screening status: outcome-blind.**
- No combine × game-performance association has been computed.
- `player_career_successes` was not used.
- The hypotheses below were fixed using only:
  - data availability;
  - outcome reliability;
  - predictor structure;
  - speed-demand descriptives;
  - Phase 2 speed-transfer results. These involve speed *expression*, not performance.
- The tests below can therefore be **confirmatory** if they are pre-registered before linkage (§5).

## 1. Literature position (for novelty statements)
**Peer-reviewed (from `literature_review.md`, DOIs verified):**
- Combine stopwatch tests relate weakly and inconsistently to draft status or career statistics. Examples:
  - Kuzmits & Adams 2008;
  - Vincent et al. 2019;
  - Cook et al. 2020 (≈ 2.6% of next-season variance);
  - Doyle et al. 2026.
- None of these uses tracking-derived combine measures, tracking-derived game outcomes, opportunity adjustment, or within-position context moderation.
- STRAIN (Nguyen, Yurko & Matthews 2023) is a tracking pass-rush metric. It does not link to the combine.

**Targeted searches this phase (grey literature only, no DOIs; cited as context, never as evidence):**
- [PFF](https://pff.com/news/40-yard-dash-vs-football-production-do-faster-receivers-deliver-more) argues that WR success depends on how speed is deployed, not 40 time alone.
- [FiveThirtyEight](https://fivethirtyeight.com/features/the-nfl-has-a-new-way-to-measure-the-explosiveness-of-pass-rushers) reports NGS get-off correlating with pass-rush win rate (r ≈ −0.51) and being stable year to year.
- No source found links combine tracking to NGS separation, get-off or pressure.
- The NGS [pressure probability](https://www.nfl.com/news/next-gen-stats-introduction-to-pressure-probability) page defines the OL metric we use.

**Novelty therefore remains *unverified*.** Before any claim we must:
- read the full texts required by CLAUDE.md;
- search past Big Data Bowl finalist notebooks on separation, get-off and combine.

## 2. Candidate hypotheses

### H1: Speed-demand moderation of capacity translation (mechanism; all positions)
- **Statement.** The game expression of combine top speed depends on how often the *task* demands near-maximal speed, not on the position label. Formally: within position, the slope of game speed expression on combine peak speed increases with the context's speed demand D(c).
- **Falsifiable predictions (directional, pre-specified):**
  - (a) WR: slope on deep routes > slope on short routes (D = 0.17 vs 0.01).
  - (b) DB: slope in man > in deep zone > in underneath zone (D = 0.07 / 0.03 / 0.02).
  - (c) DL: the pooled DL slope (Phase 2 ρ 0.73) **shrinks materially within alignment** (EDGE vs INTERIOR) **and after adjusting for weight**. Reason: in DL, peak speed and weight correlate at −0.80, so the high "transfer" is partly role/body-type sorting.
- **Motivation.** This explains Phase 2's puzzle: DL 0.73 vs DB 0.13, despite DBs being faster and playing in open space.
- **Novelty.** Not seen in the peer-reviewed set; game-demand descriptions exist, but not as a moderator of combine transfer. Unverified (see §1).
- **Variables:**
  - combine: tracked 40 peak speed (r = 0.987);
  - game: play max speed (before the throw for WR);
  - context: route depth, coverage role, alignment;
  - D(c) from `speed_demand.parquet`.
- **Eligible players:** WR 57, DB 56 (35 with ≥ 100 man snaps), DL 53, OL 53. TE descriptive only.
- **Measurement validity:** outcome reliability 0.68–0.95 (expression metrics); predictor 0.987.
- **Statistical feasibility:** good.
  - The design is *within-player*: each player contributes plays in several contexts. The context × capacity interaction is therefore identified from within-player contrasts, with thousands of plays.
  - Its between-player precision is still bounded by n ≈ 55. Power will be simulated before confirmation.
- **Baselines:** (i) one slope per position (Phase 2); (ii) the official 40 in place of tracked peak speed.
- **Football implication:** say where combine speed will and will not show up for a player, given his projected role. Example: a DB projected as a zone safety should not be drafted for his 40.
- **Major confounders:**
  - Routes and coverage are *assigned* by coaches, possibly because of speed. Addressed with a player random slope, and by treating deployment as a separate outcome (H4).
  - Ceiling/censoring: short-route speed is capped by the route.
  - Exposure: Phase 2 ratio effect.

### H2: WR top speed buys separation on deep routes only (performance; WR)
- **Statement.** Among WRs, tracked combine peak speed predicts context-adjusted separation at pass forward on deep routes. It does not do so on short routes. The deep-route association persists after conditioning on the official 40 time.
- **Predictions:** β_deep > 0; β_deep − β_short > 0; ΔR² over the 40-only model > 0 in player-grouped CV.
- **Motivation.** H1(a) is the mechanism; separation is the payoff, a validated tracking quantity reproduced exactly from coordinates. WR peak speed carries 34% unique variance beyond the 40.
- **Novelty.** Not found in the peer-reviewed or grey literature searched. Unverified.
- **Eligible players:** 57 WRs (≥ 100 routes); 41 with ≥ 100 deep routes.
- **Measurement validity:**
  - Adjusted separation reliability: 0.61 (all), 0.61 (deep), but **0.22 for short routes**. The short-route arm is essentially a test against noise, which is a weakness.
  - Season-to-season ρ is only 0.28–0.47.
- **Statistical feasibility: marginal.**
  - Between-player MDE |ρ| = 0.36 (α 0.05, 80% power), or 0.43 with Holm-adjusted α.
  - Attenuation √(0.99 × 0.61) = 0.78, so a true ρ ≥ 0.46 is needed.
  - The play-level mixed model is more efficient than player means, but the effective n is the player.
- **Baselines:**
  - official 40;
  - 10-yd split;
  - draft-round-free position mean;
  - raw (unadjusted) separation, to show deployment confounding.
- **Football implication:** a direct, weekly-usable statement: which receivers' speed creates separation, and on which routes. It sharpens WR evaluation beyond the 40.
- **Major confounders:**
  - QB and offence quality → team-season random effect.
  - Coverage shell and man/zone.
  - Time to throw (sensitivity only; it is partly a consequence).
  - Route mix assigned for speed (deployment).
  - Selection into playing time.
  - Separation exists only on thrown passes (selection on QB decisions).

### H3: Combine burst → game get-off → pressure (performance chain; DL)
- **Statement.** Combine early acceleration (official 10-yd split) predicts game get-off within alignment, and get-off mediates part of any association with pressure per rush.
- **Predictions:** 10-yd split → get-off (positive slope on time); get-off → pressure (negative); the indirect effect ≠ 0.
- **Novelty:**
  - Get-off → pressure is partly known (grey).
  - Combine → get-off was not found.
  - The chain design is new to our knowledge. Unverified.
- **Eligible players:** 53 DL (≥ 100 rushes); 37 with ≥ 200.
- **Measurement validity:**
  - Get-off: 0.90 (adj), validated by tracking (ρ −0.90).
  - Pressure: **0.50** (adj).
  - Predictor: an official electronic split, single trial, reliability unknown.
  - Tracked combine A0 is unreliable (Phase 2) and is not used.
- **Statistical feasibility:**
  - First link (split → get-off): good, given rel 0.90 and MDE 0.38.
  - Second link (→ pressure): weak, with an attenuation ceiling of 0.70.
- **Critical limitation:** in DL, the 40, the 10-yd split, peak speed and weight are one dimension (|ρ| 0.80–0.97).
  - **No incremental value beyond the 40 can be identified.**
  - Speed effects cannot be separated from body type except within alignment.
  - The combine-*tracking* contribution is minimal here, which fits the competition poorly.
- **Baselines:** 40 time; weight; alignment.
- **Football implication:** an edge vs interior burst profile; this is moderate value.
- **Major confounders:** alignment, weight, blitz/stunt design (not labelled), opponent OL, time to throw.

### H4: Speed buys deployment (DB; deployment as outcome; exploratory)
- **Statement.** Faster DBs (combine) are deployed more in man coverage and with tighter cushion. Their game speed expression appears in man, not in zone (overlaps H1b).
- **Status: exploratory.**
  - No DB coverage *performance* outcome exists.
  - Cushion is a deployment metric (reliability 0.97, but dominated by alignment).
  - The man-snap share has not yet been reliability-screened.
- **Eligible players:** 56 (35 with ≥ 100 man snaps).
- **Football implication:** a revealed-preference reading of how coaches use speed. Interesting, but not performance.

### H5: OL speed → pass-protection quality (OL)
- **Statement.** OL combine speed (peak speed / 10-yd split) predicts lower peak pressure probability allowed, adjusted for alignment and number of rushers.
- **Measurement validity:**
  - Outcome reliability 0.69 (adj), but season-to-season ρ only 0.32.
  - Phase 2 OL speed transfer is weak (0.38).
  - Speed demand in OL tasks is ~1% of plays.
- **Theory:** H1 predicts **no** association (low demand). H5 is therefore a *negative-control-style* test of H1, not a discovery target.
- **Eligible players:** 53. MDE 0.38.

## 3. Screening matrix
Scores are 1–5; higher is better.

| Criterion | H1 | H2 | H3 | H4 | H5 |
|---|---|---|---|---|---|
| Uses combine *tracking* (competition requirement) | 5 | 5 | 2 | 4 | 3 |
| Answers "why does it vary across positions?" | **5** | 3 | 2 | 3 | 3 (as negative control) |
| Outcome validity / reliability | 5 | 3 | 3 | 2 | 3 |
| Statistical power (n, attenuation) | 4 | 2 | 3 | 2 | 3 |
| Incremental value beyond 40 testable | 4 (WR/DB) | 4 | 1 | 4 | 2 |
| Novelty (provisional) | 4 | 4 | 3 | 3 | 2 |
| Football usefulness | 4 | 5 | 3 | 3 | 2 |
| **Total (/35)** | **31** | **26** | **17** | **21** | **18** |

## 4. Research design (Task 5)
### 4.1 Models (no deep learning, by design)
Unit: player i, play j, context c(j), team-season t(j). All continuous predictors are standardised within position.

**M1 (H1): expression model, linear mixed model.**
- `vmax_ij = α_pos + β_pos(c) · peak_i + γ' context_ij + θ · log(exposure) + u_i + u_i,c + v_t + ε_ij`
  - The slope β_pos(c) = β0_pos + β1 · D(c) is a **demand-varying coefficient**: the methodological contribution.
  - Random effects: player intercept, player-by-context slope, team-season.
  - Confirmatory parameter: **β1 > 0**, plus the per-position contrasts (a)–(c).
- Nonlinearity: natural cubic spline (3 df) in `peak`, as a sensitivity analysis.
- **Ceiling handling:**
  - play max speed is bounded by route length;
  - sensitivity uses a censored/quantile (0.9) version, and the per-player top-5 within context.

**M2 (H2): separation model (WR).**
- `sep_ij = α + β_d · peak_i · deep_ij + β_s · peak_i · short_ij + δ · forty_i + γ' context_ij + u_i + v_t + ε_ij`
- Confirmatory parameters: β_d > 0, and β_d − β_s > 0.
- Incremental value: an LR test of `peak` given `forty`, plus **player-grouped 10-fold CV** of player-level adjusted separation (ΔR², ΔRMSE, bootstrap CI).

**M3 (H3): two-equation mediation (DL), within alignment.**
- `getoff_ij ~ split_i + weight_i + alignment + context + u_i + v_t`
- `pressure_ij ~ logit(getoff_i, split_i, weight_i, context, ttt) + u_i + v_t`
- Indirect effect with a cluster bootstrap.

### 4.2 Uncertainty, multiplicity, validation
- **CIs:** cluster (player) bootstrap, 2,000 reps, alongside model-based CIs.
- **Multiplicity:** Holm across the primary family {H1-β1, H2-β_d, H2-(β_d − β_s)}. Everything else is secondary or exploratory and labelled as such.
- **Measurement error:**
  - The predictor reliability of 0.987 makes the correction negligible; it is reported anyway.
  - Outcome unreliability is handled by the mixed model; disattenuated correlations are reported as secondary.
- **Validation:**
  - (i) player-grouped CV;
  - (ii) **season-forward:** fit 2023–24, predict 2025 player means;
  - (iii) new-player check on the 2025 draft class (small; descriptive).
- **Robustness:**
  - opportunity thresholds 50/100/200;
  - with and without time-to-throw;
  - REG only vs REG+POST (POST as robustness only);
  - inverse-probability-of-eligibility weights;
  - leave-one-team-out.
- **Negative controls:**
  - H5 (OL, low demand) should show ≈ 0;
  - the WR short-route arm;
  - permuted context labels.

### 4.3 Exploratory vs confirmatory
- **Confirmatory:** the three pre-registered primary parameters above. Directions, model, covariates, thresholds and exclusions are frozen in a committed pre-registration file *before* any combine × game outcome join is run.
- **Exploratory, labelled as such:**
  - H3 (DL chain), H4 (DB deployment), TE descriptives;
  - any new contexts or outcomes discovered while modelling;
  - DB coverage from cohort–cohort matchups (≈ 4.8k selected plays).
- Any exploratory finding must replicate on the 2025 season hold-out before it is reported as a result.

### 4.4 What the claims can and cannot be
- **Associational only.** Assignment of routes and coverage depends on speed (deployment), and selection into playing time is non-random. Statements will read "is associated with … conditional on …".
- Results will **not** be called causal "effects of speed".

## 5. Recommendation
**Recommended direction:** *"Speed only matters where the game asks for it." A demand-moderated model of how combine top speed translates into NFL play.* This is H1 as the backbone, with H2 as the performance payoff. H5 serves as a negative control; H3 and H4 are secondary or exploratory.

**Why:**
1. **It answers the central question directly.**
   - It explains *why* translation varies across positions through a measurable, position-independent quantity, task speed demand D(c), rather than describing five different correlations.
   - It also makes a pointed, falsifiable prediction: the "high DL transfer" is mostly body-type and role sorting.
2. **It rests on measurements that survived validation.**
   - Tracked combine peak speed: r = 0.987.
   - Game speed expression: reliability 0.68–0.95.
   - Separation: reproduced exactly from tracking.
   - It avoids every Phase 2 failure: A0, braking/lateral "capacities", CCMT.
3. **It uses combine *tracking* where tracking adds information.** Peak speed carries a third unique variance beyond the official 40 in WR and DB, the two positions where demand varies most.
4. **It is statistically feasible where it is primary.**
   - The within-player context contrast (H1) is well powered.
   - **H2 is honestly marginal:** it can detect only a true ρ ≳ 0.45. A null H2 would itself be informative, given H1.
5. **It has a methodological contribution to benchmark:**
   - The varying-coefficient (demand-moderated) mixed model.
   - Baselines: one-slope-per-position and 40-only. The comparison metric is player-grouped and season-forward predictive accuracy.

**Main risks:**
- deployment endogeneity (fast players are sent deep);
- ceiling effects on short routes;
- WR n ≈ 57;
- TE unusable.

**Not recommended as primary:**
- H3: its predictors are collinear with weight, there is no tracking contribution, and the outcome reliability is 0.50.
- H4: there is no DB performance outcome.

**Next step, if approved:**
- (1) Write and commit the pre-registration (models, directions, thresholds, exclusions).
- (2) Simulate power for M1/M2 at the observed n and reliabilities.
- (3) Only then join combine to game outcomes and run the confirmatory tests.

**Full performance modelling has not started and awaits approval.**
