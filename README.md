# NFL Big Data Bowl 2027 — Research Project

Research codebase for the [NFL Big Data Bowl 2027](https://www.kaggle.com/competitions/nfl-big-data-bowl-2027)
Kaggle competition (Featured, deadline 2027-01-06).

Our goal is a PhD-level contribution that meets three standards — an advanced technical
contribution, a genuinely novel discovery, and a potentially new algorithm that improves on
existing approaches. See [`CLAUDE.md`](CLAUDE.md) for the full research charter.

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
| 2. Real-data feasibility / feature engineering | ⏸ Awaiting approval |
| 3. Modelling & novel algorithm | — |
| 4. Write-up & submission | — |

## Security

- Raw data, derived data, model artifacts and credentials are excluded by `.gitignore`.
- Credentials are read from the environment only and never written to the repo.
