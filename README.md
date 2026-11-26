# NFL Big Data Bowl 2027 — Research Project

Research codebase for the [NFL Big Data Bowl 2027](https://www.kaggle.com/competitions/nfl-big-data-bowl-2027)
Kaggle competition (Featured, deadline 2027-01-06).

Our goal is a rigorous, reproducible, PhD-level analysis of how NFL Combine athletic measures relate to regular-season movement and performance. The confirmatory study is complete. A final literature audit found no defensible new algorithmic contribution from the available data; see [`research_notes/phase8c_novelty_audit.md`](research_notes/phase8c_novelty_audit.md). Any additional estimator benchmark is a separate empirical study and requires its own preregistration.

## Data

Competition data is **not** in this repository (Kaggle rules). To fetch it:

1. Accept the competition rules on Kaggle.
2. Provide credentials via environment variables — `KAGGLE_API_TOKEN` (or
   `KAGGLE_USERNAME` + `KAGGLE_KEY`).
3. Run:

```bash
./scripts/download_data.sh
```

This downloads and extracts into `data/raw/nfl-big-data-bowl-2027/`:

| File | Size |
|---|---|
| `combine_results.csv` | 41 KB |
| `combine_tracking.csv` | 84 MB |
| `game_tracking_2023.csv` | 335 MB |
| `game_tracking_2024.csv` | 718 MB |
| `game_tracking_2025.csv` | 1.02 GB |
| `games.csv` | 43 KB |
| `player_career_successes.csv` | 14 KB |
| `player_play.csv` | 147 MB |
| `players.csv` | 47 KB |

Total ≈ 2.3 GB extracted (489 MB zipped).

The first notebook run caches the CSVs as Parquet in `data/interim/` (≈0.46 GB, git-ignored) via `nfl_bdb.data.io.build_parquet_cache()`.

## Repository layout

```
configs/            experiment configuration files
data/
  raw/              original competition files (git-ignored)
  interim/          cleaned / Parquet-converted data (git-ignored)
  processed/        model-ready features (git-ignored)
  external/         third-party data (git-ignored)
docs/               research notes, literature review
experiments/        experiment logs and outputs (git-ignored)
notebooks/          exploratory and narrative notebooks
paper/              write-up / submission drafts
research_notes/     written findings (dataset inventory, player matching, research opportunities)
reports/figures/    generated figures (git-ignored)
scripts/            CLI entry points (e.g. download_data.sh)
src/nfl_bdb/        package: data, features, models, evaluation, visualization
tests/              unit tests
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

## Project phases

| Phase | Status |
|---|---|
| 0. Setup, data access, download | ✅ Done |
| 1. Exploratory data analysis | ✅ Done — `notebooks/01_dataset_exploration.ipynb`, `research_notes/` |
| 1.5 Literature review & research gaps | ✅ Done — `research_notes/` |
| 1.6 Feasibility simulations (B + C) | ✅ Done — notebooks 02–03, `research_notes/*feasibility*.md` |
| 2. Real-data feasibility validation | ✅ Done — notebooks 04–05, `research_notes/` |
| 3. Outcome-blind hypothesis screening | ✅ Done — `research_notes/phase3_hypothesis_screening.md` |
| 3.5 Pre-registration & power | ✅ Done — `research_notes/preregistration.md` (frozen v1.0 + deviations log §15), notebook 06 |
| 4. Synthetic validation of the confirmatory pipeline | ✅ Done — `research_notes/synthetic_validation.md`, notebook 07 |
| 4.5 Pre-join decisions, single combine × outcome join, pre-model audit | ✅ Done — D1–D4 in §15, `join_validation_report.md`, `pre_model_audit.md` |
| 5a. H1-WR (sole primary confirmatory test) | ✅ Done — **inconclusive**; notebook 08 |
| 5b. H1-WR registered robustness + negative control | ✅ Done — conclusion stable |
| 5c. H2 (secondary, estimation-focused after D4) | ✅ Done — no incremental information detected; notebook 09 |
| 5d. Secondary Holm family (H1-DB, H1-DL a/b, H5b), H5(a)/(c), H1-global, TE descriptives | ✅ Done — notebook 10, `research_notes/secondary_family_results.md` |
| 8. Literature novelty audit | ✅ Done — no new algorithm justified; see `research_notes/phase8c_novelty_audit.md` |
| 9–10. Submission build, Kaggle execution, release | ✅ Built, public code + notebook released; **not submitted** — `research_notes/phase9b_submission_audit.md`, `phase10_3_publication_audit.md` |
| 11–17. Combine measurement-development branch (three-cone, shuttle, continuous-time estimator, skill drills, WR route launch, WR outcome power) | ⛔ **Closed** — no measurement approved for outcome validation; see [`research_notes/phase18_research_closeout.md`](research_notes/phase18_research_closeout.md) |
| 18. Branch closure and evidence audit | ✅ Done — [`research_notes/phase18_research_closeout.md`](research_notes/phase18_research_closeout.md) |
| 19. Feasibility: tracked peak beyond the official 40 for WR game speed (simulation only) | ⛔ **NO-GO** — [`research_notes/phase19_game_speed_incremental_feasibility.md`](research_notes/phase19_game_speed_incremental_feasibility.md) |

## Research summary (current)

The consolidated final summary, with claims, non-claims, limitations and opportunities, is in [`research_notes/research_findings_summary.md`](research_notes/research_findings_summary.md). The post-study measurement-development branch (Phases 11–17) and its closure, candidate decision matrix and evidence audit are in [`research_notes/phase18_research_closeout.md`](research_notes/phase18_research_closeout.md).

**Title:** *Task-Conditioned Translation of Athletic Capacity: Connecting NFL Combine Sensor Tracking to Regular-Season Football Performance.*

**H1-WR (sole primary, pre-registered; `research_notes/h1_wr_confirmatory_results.md`).**
- **Hypothesis:** combine tracked peak speed is more strongly associated with in-game speed on deep routes than on short routes (Δ = ρ_deep − ρ_short > 0).
- **Sample and method:** 57 WRs and 19,960 REG route plays; REML mixed model with a full REML player-cluster bootstrap (B = 2,000).
- **Result: Δ̂ = 0.090** (ρ_deep 0.576, ρ_short 0.486), **95 % CI [−0.089, 0.400]**, p = 0.21. The 2025 season-forward sign agrees.
- **Decision: INCONCLUSIVE.** Not supported (the CI includes 0) and not falsified (the 90 % upper bound 0.33 > SESOI 0.15).
- **Interpretation:** combine peak speed translates into game speed on short routes about as strongly as on deep routes. The raw slopes are about 0.11 yd/s per 0.25 yd/s in both contexts.

**H1-WR robustness** (`h1_wr_robustness_results.md`, `h1_wr_negative_controls.md`, `h1_wr_bootstrap_diagnostics.md`):
- Every registered full-sample variant gives Δ̂ 0.073–0.119, with a CI including 0.
- Leave-one-team-out: 0.035–0.125.
- The permutation negative control is centred at 0.
- The Wald check gives 95 % CI [−0.114, 0.294].
- The BCa interval's downward shift is traced to a known property of the registered bootstrap; the percentile interval stays primary.

**H2** (secondary, estimation-focused; `h2_estimation_results.md`):
- Tracked peak speed adds **no detectable information** about deep-route separation beyond the official 40: β_P = −0.020 yd per SD, 95 % CI [−0.101, 0.063].
- No model (not even the 40 alone) predicts held-out players' deep separation better than the position mean.
- The registered criteria pattern is "inconclusive", because the true-scale partial correlation is not estimable: between-player SD of deep separation is only 0.13 yd.

**Secondary family** (Holm, m = 4; `secondary_family_results.md`):

| hypothesis | estimate | 95 % CI | Holm-adjusted p | decision |
|---|---|---|---|---|
| H1-DL(b) | 0.82 | [0.16, 1.54] | 0.032 | **supported** |
| H1-DB | 0.14 | [−0.61, 1.05] | 1.00 | inconclusive |
| H5(b) | 0.01 | [−0.57, 0.63] | 1.00 | inconclusive |
| H1-DL(a) | 0.04 | [−0.23, 0.15] | 1.00 | falsified (registered equivalence-type rule) |

- **H1-DL(b)**
  - **Registered statistical result:** supported after Holm adjustment (p = 0.032).
  - **Interpretation:** the pooled DL association between combine speed and game speed (ρ 0.55) is substantially sensitive to adjustment for EDGE/interior role and body weight.
  - **Descriptive audit** (`dl_role_weight_interpretation.md`):
    - role alone (−0.05) and weight alone (−0.08) each remove most of the pooled association;
    - within EDGE (0.05) and within interior (0.01) linemen it is near zero.
  - **Not claimed:**
    - that the joint role-and-weight model uniquely identifies the mechanism;
    - that the adjusted negative value (−0.27 ± 0.45) has a causal or substantive meaning.
  - Collinearity is substantial but not extreme: speed–weight r −0.80, VIF 2.9. The earlier wording "weakly identified" has been corrected.
  - This concerns game *movement*, not performance.
- **H1-DL(a):** a pass-rush-vs-run difference of ≥ 0.15 is not supported.
- **Estimation only:** H5(a), the OL negative control (Δ_OL 0.08 [−0.46, 0.64]), H5(c) and the demand meta-regression are uninformative.

| 6. Additional empirical estimator benchmark (optional; separate preregistration required) | Not approved |
| 7. Write-up & submission | Next — consolidate the completed confirmatory study |

## Security

- Raw data, derived data, model artifacts and credentials are excluded by `.gitignore`.
- Credentials are read from the environment only and never written to the repo.
