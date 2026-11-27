# Kaggle refresh manifest: public notebook and code dataset (prepared, NOT uploaded)

**Prepared from repository commit:** `9270f58` plus the notebook-text update committed with this manifest. **Nothing has been uploaded or published.** Licensing language is unchanged and still PROPOSED (see §4).

## 1. Code dataset `simhadripraveena03/from-combine-speed-to-nfl-movement-code` (minimal refresh, new version of the existing public dataset)

Staging folder (git-ignored): `build/kaggle_release_minimal/`. Built from the downloaded public version 2; only the figure module is replaced. Structure, file names, title, description and licence metadata are unchanged.

| file | bytes | sha256 (first 16) | vs public v2 | frozen | source |
|---|---|---|---|---|---|
| `LICENSE` | 11,357 | `c71d239df91726fc` | unchanged |  | release/LICENSE-Apache-2.0.txt |
| `NOTICE.md` | 4,417 | `4a97faadedba9ca8` | unchanged |  | release/NOTICE.md |
| `README.md` | 1,412 | `04c54a92899a757f` | unchanged |  | release/DATASET_README.md |
| `research_notes/code_freeze.json` | 1,501 | `adeedd4296236421` | unchanged |  | repo HEAD |
| `scripts/run_confirmatory_join.py` | 10,436 | `acc7581bf6d52998` | unchanged | yes | repo HEAD |
| `scripts/run_forty_reliability.py` | 6,250 | `49cf4ca619b3be78` | unchanged | yes | repo HEAD |
| `scripts/run_phase3_screening.py` | 33,434 | `525ab946332cf2c5` | unchanged | yes | repo HEAD |
| `scripts/run_real_capacity.py` | 6,311 | `810c6d238002eebe` | unchanged | yes | repo HEAD |
| `src/nfl_bdb/__init__.py` | 0 | `e3b0c44298fc1c14` | unchanged |  | repo HEAD |
| `src/nfl_bdb/data/__init__.py` | 0 | `e3b0c44298fc1c14` | unchanged |  | repo HEAD |
| `src/nfl_bdb/data/confirmatory_data.py` | 9,210 | `cbc77a7fc42272f1` | unchanged | yes | repo HEAD |
| `src/nfl_bdb/data/game_kinematics.py` | 5,150 | `2b7a4a3b3f9331f5` | unchanged | yes | repo HEAD |
| `src/nfl_bdb/data/io.py` | 2,462 | `11b4c60a4fc24175` | unchanged | yes | repo HEAD |
| `src/nfl_bdb/data/play_table.py` | 5,483 | `9755b6b48b2464a4` | unchanged | yes | repo HEAD |
| `src/nfl_bdb/data/profiling.py` | 3,796 | `61e02f2edbb06c12` | unchanged |  | repo HEAD |
| `src/nfl_bdb/evaluation/__init__.py` | 0 | `e3b0c44298fc1c14` | unchanged |  | repo HEAD |
| `src/nfl_bdb/features/__init__.py` | 0 | `e3b0c44298fc1c14` | unchanged |  | repo HEAD |
| `src/nfl_bdb/features/change_direction_cost.py` | 22,729 | `774519c72401240f` | unchanged |  | repo HEAD |
| `src/nfl_bdb/features/demand.py` | 3,184 | `f10e70c0a1a07c28` | unchanged | yes | repo HEAD |
| `src/nfl_bdb/features/forty_reliability.py` | 3,867 | `cdeee09243a861bf` | unchanged | yes | repo HEAD |
| `src/nfl_bdb/models/__init__.py` | 0 | `e3b0c44298fc1c14` | unchanged |  | repo HEAD |
| `src/nfl_bdb/models/capacity_estimator.py` | 27,326 | `1a258149f3c832e3` | unchanged |  | repo HEAD |
| `src/nfl_bdb/models/confirmatory.py` | 18,186 | `2b7d06cdaaaecbe5` | unchanged | yes | repo HEAD |
| `src/nfl_bdb/models/h1_extensions.py` | 18,161 | `fb5a3841f3140a8f` | unchanged |  | repo HEAD |
| `src/nfl_bdb/models/h2_extensions.py` | 11,960 | `1096e46e83a32556` | unchanged |  | repo HEAD |
| `src/nfl_bdb/models/power.py` | 8,995 | `99186571b14e8ee8` | unchanged |  | repo HEAD |
| `src/nfl_bdb/models/reml.py` | 5,497 | `7decc6d0d81dce96` | unchanged | yes | repo HEAD |
| `src/nfl_bdb/models/secondary.py` | 7,295 | `cd8d576757e0a592` | unchanged |  | repo HEAD |
| `src/nfl_bdb/models/validation_summary.py` | 5,010 | `ed21d96c4e73f9ac` | unchanged |  | repo HEAD |
| `src/nfl_bdb/simulation/__init__.py` | 92 | `607370ee6c7da968` | unchanged |  | repo HEAD |
| `src/nfl_bdb/simulation/confirmatory_sim.py` | 5,867 | `dda5fd45b9fc1709` | unchanged |  | repo HEAD |
| `src/nfl_bdb/simulation/movement.py` | 10,630 | `fe87d606a69eeda5` | unchanged |  | repo HEAD |
| `src/nfl_bdb/visualization/__init__.py` | 0 | `e3b0c44298fc1c14` | unchanged |  | repo HEAD |
| `src/nfl_bdb/visualization/style.py` | 1,355 | `1fa9406f502e229c` | unchanged |  | repo HEAD |
| `src/nfl_bdb/visualization/submission_figures.py` | 22,186 | `7a6e2fe7bba6c0e2` | **changed** |  | repo HEAD |

Upload metadata `dataset-metadata.json` (not a content file): id `simhadripraveena03/from-combine-speed-to-nfl-movement-code`, title "From Combine Speed to NFL Movement: code", licence `apache-2.0`, description unchanged.

**Summary:** 35 content files; 1 changed (`src/nfl_bdb/visualization/submission_figures.py`: final figure titles, captions, labels and layout; imports unchanged; no plotted value changed); 0 added; 0 removed. 12/12 frozen files present with registered SHA-256.

**Deliberately not included:** the 13 Phase 11–19 modules that the full `--release` builder would add (`evaluation/repeatability.py`, `features/{exit_accel_candidates,launch,phase15_measures,shuttle_accel,skill_drills,turn_reacc_audit,turn_recovery}.py`, `simulation/{arc_synth,game_speed_incremental,outcome_power,shuttle_synth,start_synth}.py`). The public notebook does not import them.

## 2. Public notebook `simhadripraveena03/from-combine-speed-to-nfl-movement` (new version)

Staging folder (git-ignored): `build/kaggle_notebook_release/`.

| file | bytes | sha256 (first 16) | note |
|---|---|---|---|
| `from-combine-speed-to-nfl-movement.ipynb` | 64,597 | `97eba8ad10a16ef1` | byte-identical to `notebooks/11_final_submission.ipynb`; no stored outputs |
| `kernel-metadata.json` | 692 | `8b1e0249729f634a` | same as the public version: public, internet off, no GPU, same docker image, sources = competition `nfl-big-data-bowl-2027` + the code dataset; Kaggle title unchanged ("From Combine Speed to NFL Movement") |

**Source changes vs public version 3:** 5 of 25 cells, all markdown (cells 0, 12, 14, 16, 19); every code cell is identical.

| cell | change |
|---|---|
| 0 | title → "What Combine Tracking Can and Cannot Tell Us About NFL Game Movement" |
| 12 | separation provenance aligned with the writeup: competition-supplied NGS field, not rebuilt; thrown passes incl. untargeted, not sacks/scrambles; cohort-defender match is a consistency check on a subset (replaces "the inventory showed it equals the tracked nearest-defender distance") |
| 14 | "his own … his 5 fastest" → "their own … the player's 5 fastest" |
| 16 | "noise-free" → "underlying" game-speed level (already in the repository) |
| 19 | H2: adds the 95% CI −3.6 to +2.3 in per SD (−0.101 to 0.063 yd), about half the between-player SD (0.13 yd): moderate effects remain possible; added effect not shown to be zero (numbers formatted from `registered_results.json` at build time) |

**Rendered output change:** the 7 figures are drawn by the dataset's `submission_figures.py`, so after both refreshes they show the final titles and captions (identical to `paper/figures/`).

## 3. Validation (local, against the staged files; no Kaggle run)

| check | result |
|---|---|
| figures from the staged `submission_figures.py` + `paper/registered_results.json` vs `paper/figures/*.png` | **7/7 byte-identical** |
| full local execution of the staged notebook with the staged dataset as code root (`NFL_BDB_CODE`) and the local competition files | **0 errors**; 12/12 frozen hashes verified from the dataset; predictor table 418 valid (per-position counts and x_peak sums equal registered); all six registered sample sizes reproduced; 7 figures rendered (final titles confirmed visually); scratch removed; nothing written to the simulated `/kaggle/working`; 97 s; peak 4.9 GB |
| embedded results in the notebook vs `paper/registered_results.json` | identical |
| notebook narrative vs `paper/kaggle_writeup/writeup_body.md` | consistent after the cell 0 / 12 / 14 / 19 updates (title, separation provenance, neutral wording, H2 qualification); technical notation (REML, Wald, H-labels) kept in the notebook's methods/results cells by design |
| secrets / local paths / data copies in both staging folders | none (no tokens, emails or local paths; no CSV / Parquet / NumPy / pickle files; Python byte-code caches created by the local checks were deleted) |
| repository tests | 113 passed; `tests/test_code_freeze.py` passed; 12/12 frozen hashes in repo and in the staged dataset |
| writeup checker | 72/72; writeup and Kaggle body synchronized |

## 4. Remaining blockers (owner)

1. **Licensing text not final** (unchanged here by instruction): the staged `NOTICE.md` and `README.md` still carry "Status: PROPOSED, revision 2" and "Nothing here has been … published", which is inaccurate for an already-public dataset. Copyright "subject to confirmation"; no licence chosen for written/visual material; no licence asserted for aggregate results; forum question unposted; the NOTICE-recommended licence-table cell is not in the notebook. Decide whether to publish this refresh with the current PROPOSED text or after a licensing decision.
2. **Upload** (owner, manual): new dataset version from `build/kaggle_release_minimal/` first, then the notebook version from `build/kaggle_notebook_release/`; confirm the Kaggle run passes (0 errors, 12/12 hashes, sample sizes, 7 figures, run log only) and that `/kaggle/working` holds no data files.
3. **Kaggle display title** of the notebook is still "From Combine Speed to NFL Movement" (changing it may affect the slug); the cell 0 heading carries the final title. Owner choice.
4. Writeup draft creation in the web editor, word-counter check, and final submission decision (see `paper/kaggle_writeup/README.md`).
