# Phase 10.3: publication of the clean Kaggle assets and Writeup preparation

**Source:**
- owner commit `e721bee` (copyright holder confirmed in `release/NOTICE.md`);
- the notebook source is byte-identical to `44ae25e`.

**No research result, figure, statistical wording or notebook source was changed.**

## 1. Code dataset refreshed (version 2), then published

| check | result |
|---|---|
| build | `python scripts/build_kaggle_code_bundle.py --release`: "12/12 frozen files present, all SHA-256 digests match" |
| contents | 35 files: `src/nfl_bdb/**` (27), 4 frozen scripts, `research_notes/code_freeze.json`, `LICENSE` (canonical Apache-2.0), `NOTICE.md`, `README.md` |
| NOTICE / README | byte-identical to `release/NOTICE.md` (copyright "2026 Simhadri Praveena") and `release/DATASET_README.md` |
| excluded | 0 CSV / Parquet / npy / npz / zip files, no `registered_results.json`, no credentials, 0 player-ID-like tokens, no experiment outputs |
| upload | new version of the existing private dataset (`kaggle datasets version`; visibility unchanged at upload) |
| read-back | remote file list equals the local bundle. The downloaded NOTICE, README, LICENSE and manifest are byte-identical. **12/12 frozen hashes verified on the downloaded copy.** Metadata: title "From Combine Speed to NFL Movement: code", licence `apache-2.0` |
| publish | `kaggle datasets metadata --update`, with title, description and licence preserved and `isPrivate: false` |
| public check | `https://www.kaggle.com/datasets/simhadripraveena03/from-combine-speed-to-nfl-movement-code`: **HTTP 200 without login** |

## 2. Clean notebook validated, then published

| version | visibility | result |
|---|---|---|
| 1 (Phase 10.1) | private | passed; saved outputs = run log only |
| 2 (this phase) | private | **all 28 audit checks passed** against the refreshed dataset. 0 errors; 12/12 hashes; predictor table 418; exclusions 240,405; all six sample sizes; H1-WR, H2, H1-DB, H1-DL(a), H1-DL(b), H5(b) results and the H2 / DL(b) detail lines identical to the registered values; 7 figures; scratch removed; no data-like files in `/kaggle/working`; peak 8.37 GB; 65 s execution |
| 3 (public) | **public** | same source, pushed with `is_private: false`. **All 28 checks passed again;** peak 8.31 GB; 90 s execution; saved outputs = run log only |

**Settings:** internet disabled, no GPU; inputs are the official competition data plus the release code dataset.

**Public check:** `https://www.kaggle.com/code/simhadripraveena03/from-combine-speed-to-nfl-movement` returns **HTTP 200 without login**.

**History:** all three versions ran the same validated source with scratch data in `/tmp`, and each saved only its run log. **The notebook history holds no competition-data copies.**

**Unchanged and still private** (HTTP 404 without login): the old notebook `combine-speed-to-nfl-movement`, whose version 1 outputs hold data copies, and the old dataset `nfl-bdb-2027-pipeline-code`.

## 3. Kaggle Writeup: NOT created (blocked)

**Why it is blocked:**
- The Kaggle CLI and SDK cannot create or edit Writeups.
- This cloud session has no browser signed in to the owner's Kaggle account.
- No owner computer is connected (`list_computer_folders`: none).

**Prepared instead:** a paste-ready package in `paper/kaggle_writeup/`:
- `README.md`: form values, figure upload order and pre-save checks;
- `writeup_body.md`;
- `cover_image.png`.

**Package checks:**
- **Title and subtitle:** exactly as specified.
- **Track:** Open Track only.
- **Project Files:** the public notebook URL.
- **Length:** 1,882 words (project counter, including the title line; body alone 1,870).
- **Visuals:** 9 (7 figures + 2 tables).
- **Results:** `scripts/check_writeup_numbers.py` passes **43/43**.
- **Rendering:** the body was converted with mistune and loaded in headless Chromium. All 7 images load, and both tables render (6 and 7 rows).
- **Formatting fix (no wording change):** the §2 sample-size table was indented under a list item and did not render as a table. It is now de-indented in `paper/final_writeup.md` (7 lines; same words and numbers).

## 4. Unresolved items

1. **Create the Writeup draft in the Kaggle UI** (owner), following `paper/kaggle_writeup/README.md`. Save as draft; do not submit.
2. **The published NOTICE still carries the "PROPOSED, revision 2 … nothing has been published" header,** plus "subject to confirmation of copyright ownership". It was uploaded unchanged, as instructed ("use the latest `release/NOTICE.md`"). Now that the dataset is public, the header is inaccurate. The owner should approve an updated NOTICE (final status, copyright confirmed), followed by a new dataset version. Code is unaffected.
3. **Writeup appendix** names the notebook `11_final_submission` (the file name); the public notebook's title is "From Combine Speed to NFL Movement". This is linked through Project Files. Optional wording edit; owner's choice.
4. **Mixed-content licence cell** in the notebook (NOTICE category mapping) is still pending, as in Phase 10.2. Adding it would change the notebook source and require a re-validation run.
