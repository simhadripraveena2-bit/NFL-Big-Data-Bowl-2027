# Phase 10.1: public-release preparation and licensing audit

**Status:** staged privately. **Nothing was published or made public.** Kaggle visibility is unchanged, and the competition entry was not submitted.

**Validated private run preserved.** `simhadripraveena03/combine-speed-to-nfl-movement` (versions 1–3) was left untouched: private, history kept, version 3 unmodified. It stands as the private execution record.

## 1. Licensing audit

### 1.1 What the repository holds today

- **No licence or ownership files:** no `LICENSE`, `NOTICE`, `COPYING`, `AUTHORS` or `CITATION` file; no licence or ownership statement in `README.md`.
- **Commit authorship:** "Praveena Simhadri" (2 commits) and "Claude" (34 commits, authored on the owner's behalf in this project). Copyright ownership must be **confirmed by the owner**; it is left as a placeholder below.
- **Builder licence field:** the Phase 9B code-bundle builder declared `apache-2.0` for a dataset that also contained `paper/registered_results.json` (competition-derived aggregates). That mixes licence categories. It is corrected in the release candidate (§2).

### 1.2 What the official competition rules say

Read from the rules page via the Kaggle CLI (Phase 9A copy):

| rule | text (abridged) | consequence |
|---|---|---|
| §1.7 Data Access and Use | **CC BY-NC 4.0** | competition data and its adaptations: non-commercial, with attribution |
| §2.4.a Data Access and Use | "non-commercial purposes only, including for participating in the Competition and on Kaggle.com forums, and for academic research and education" | no commercial use of the data |
| §2.4.b Data Security | "not … publish, redistribute or otherwise provide or make available the Competition Data to any party not participating in the Competition" | **never** ship competition files or extracts |
| §1.6 / §2.5.a.1 Winner License | winning submission and source code under an **OSI-approved licence that does not limit commercial use** | the code must carry a permissive OSI licence. Apache-2.0 qualifies, and so would MIT |
| §2.5.a.3 | no open-source licence needs to be granted for input data with an incompatible licence | the competition data and its derivatives stay outside the code licence |

### 1.3 Proposed licence and attribution structure (for owner approval)

| category | covers | proposed treatment |
|---|---|---|
| **1. Original project source code** | `src/nfl_bdb/**`, `scripts/*.py`, `research_notes/code_freeze.json` | **Apache License 2.0.** Canonical text, SHA-256 `c71d239d…0ab4`. Copyright line: `Copyright 2026 <COPYRIGHT HOLDER: owner to confirm>`. Meets the Winner License requirement; matches the Kaggle dataset licence field |
| **2. Notebook source code** | `notebooks/11_final_submission.ipynb` (code cells and prose) | **Apache License 2.0** for the code. Public Kaggle notebooks are shown under Kaggle's standard Apache-2.0 notice; verify in the UI at publication. **Caveat:** the notebook *embeds* the registered aggregate results (category 3). The release version should therefore carry a short NOTICE cell stating that the embedded results are CC BY-NC 4.0. That changes the notebook source, so it needs owner approval and one more validation run. Not done here, because this phase uses the exact `44ae25e` source |
| **3. Registered aggregate results** | estimates, CIs, sample sizes, reliabilities, figures; `paper/registered_results.json`; the results embedded in the notebook and writeup | **Not Apache-2.0.** Derived from CC BY-NC 4.0 data, so shared **for non-commercial purposes under CC BY-NC 4.0**. Attribution: *"Derived from the NFL Big Data Bowl 2027 competition data (National Football League, via Kaggle), used under the competition rules (CC BY-NC 4.0)."* Apache-2.0 would allow commercial reuse, which CC BY-NC 4.0 §3(a)(4) forbids an adapter's licence to enable. The release code dataset therefore **excludes** `registered_results.json`. It is unused at runtime anyway, because the notebook embeds the results |
| **4. NFL competition data** | all competition CSVs and any extract or copy | **Not included and not licensed by the project.** Accessed only through Kaggle's competition input by participants who have accepted the rules. Governed by rules §2.4 (CC BY-NC 4.0; no redistribution to non-participants) |
| **5. Writeup prose** | Kaggle Writeup text / `paper/final_writeup.md` | owner decision. Suggested CC BY-NC 4.0, consistent with category 3 |

**Draft files** (labelled *PROPOSED*; not applied to the repository root):
- `release/LICENSE-Apache-2.0.txt`: canonical Apache-2.0 text, hash-checked by the builder;
- `release/NOTICE.md`: the per-category licensing and attribution above;
- `release/DATASET_README.md`: the dataset description.

**Recommendation.** If the GitHub repository is (or becomes) public, add a root `LICENSE` (Apache-2.0) and `NOTICE.md` with the same structure. The repository's aggregate results (`paper/`, `research_notes/`, figures) fall under category 3.

*Not legal advice. Treating aggregate statistics as material derived from the data is the conservative reading.*

## 2. Clean public-release candidate (staged privately)

| item | value |
|---|---|
| **proposed notebook** | `https://www.kaggle.com/code/simhadripraveena03/from-combine-speed-to-nfl-movement`. A new slug with a single version, so no version history holds data |
| visibility | **private** (`is_private: true`); internet off; no GPU |
| notebook source | **exact** `notebooks/11_final_submission.ipynb` from commit **`44ae25e`** (byte-identical; pushed with 0 saved outputs) |
| **proposed code dataset** | `https://www.kaggle.com/datasets/simhadripraveena03/from-combine-speed-to-nfl-movement-code`: **private**; Kaggle licence field `apache-2.0` (read back from Kaggle) |
| code-dataset contents | `src/nfl_bdb/**` (27 files); `scripts/run_real_capacity.py`, `run_phase3_screening.py`, `run_confirmatory_join.py`, `run_forty_reliability.py`; `research_notes/code_freeze.json`; `LICENSE` (Apache-2.0); `NOTICE.md`; `README.md`. **36 files, no `paper/`, no results file.** Built by `python scripts/build_kaggle_code_bundle.py --release`, which asserts the canonical licence hash, 12/12 frozen files and no derived-results files |
| competition input | official `nfl-big-data-bowl-2027` competition data via `competition_sources`; no copy made |
| excluded | competition files, Parquet/CSV extracts, player-level records, experiment outputs, credentials. The builder checks forbidden extensions and directories |

## 3. Verification run of the candidate (Kaggle, version 1, clean session)

| check | result |
|---|---|
| status | **COMPLETE.** About 128 s from push to finish (about 90 s of notebook execution) |
| mounts discovered | data `/kaggle/input/competitions/nfl-big-data-bowl-2027/nfl-big-data-bowl-2027`; code `/kaggle/input/datasets/<owner>/from-combine-speed-to-nfl-movement-code` |
| cell errors / tracebacks | **0** |
| frozen files | "all 12 frozen files present; all SHA-256 digests verified" |
| Combine features | 418 valid tracked 40s; per-position counts and x_peak sums equal the registered values |
| sample sizes | all reproduced: H1-WR 57 / 19,960; TE 17 / 4,170; DB 52 / 16,643; DL 53 / 34,154; OL 53 / 64,285; H2-WR 57 / 19,967 |
| registered results | H1-WR Δ 0.090 [−0.089, 0.400] INCONCLUSIVE; H2 β_P −0.020 [−0.101, 0.063] INCONCLUSIVE; H1-DL(b) 0.816 [0.160, 1.538], Holm p 0.032; ΔR²_CV −0.024 (LB −0.036); reliability 0.44; DL pooled 0.549 → −0.267 |
| match with the validated private run (v3) | every count and result identical. The only differences are the printing order of keys inside three per-context count dictionaries (polars `group_by` does not guarantee row order); the values are identical |
| figures | **7 rendered** (in-notebook assertion) |
| clean-up | "scratch directory removed: True"; "data-like files in /kaggle/working: none". **Saved outputs = the run log only** (no data files) |
| data exposure | 0 player-ID-like tokens in the outputs; aggregate tables only |
| memory | peak RSS 8.36 GB |
| model refits | none (no confirmatory runner, REML fit, bootstrap or join in any code cell) |

## 4. Can another eligible participant run it?

**Yes, once both inputs are visible to them. Requirements:**
1. **They are a competition participant.** They have joined NFL Big Data Bowl 2027 and accepted its rules, so Kaggle mounts the competition data for them. Non-participants cannot access the data, as rules §2.4.b requires.
2. **The code dataset must be public**, or shared with them. It is private now, per this phase's constraints. Making it public is the only remaining step for others. It contains code only, so publishing it does not distribute competition data.
3. **Nothing else is needed:** no internet, no GitHub access, no credentials, no local paths. The notebook finds both inputs under `/kaggle/input/` at any depth up to 4. It runs on a standard CPU session, well within the 30 GB memory limit.

**Not tested here:** an actual run under a second Kaggle account, which needs a second account and public or shared inputs.

## 5. Owner decisions required before publication

1. **Licensing:** approve the structure in §1.3, and fill in the copyright holder.
2. **NOTICE cell:** approve adding a short licensing cell to the notebook, stating that embedded results are CC BY-NC 4.0. If approved, it needs one validation re-run as version 2 of the new notebook.
3. **Visibility:** when ready, make public:
   - the code dataset `from-combine-speed-to-nfl-movement-code`;
   - the notebook `from-combine-speed-to-nfl-movement`.
   Keep `combine-speed-to-nfl-movement`, the execution record whose version 1 outputs hold data copies, private permanently.
4. **Writeup prose:** choose its licence; then publish the writeup and submit the entry (separate review).

## 6. Files changed in this phase

**Added:**
- `release/LICENSE-Apache-2.0.txt`, `release/NOTICE.md`, `release/DATASET_README.md` (proposals);
- this note.

**Modified:**
- `scripts/build_kaggle_code_bundle.py`: new `--release` mode (code only, plus licence files, hash-checked). The default mode is unchanged;
- `CLAUDE.md`: status line.

**Unchanged:** the research code, registered results, figures, writeup and notebook source (`44ae25e`).
