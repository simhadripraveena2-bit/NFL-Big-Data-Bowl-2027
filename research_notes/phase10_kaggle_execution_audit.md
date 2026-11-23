# Phase 10: Kaggle execution and reproducibility audit

**Scope:**
- Deploy the frozen submission notebook to Kaggle and validate it at runtime.
- No registered analysis, result, preregistration or scientific interpretation was changed.
- **Not published, and no competition entry submitted.**

## 1. Frozen state and inputs

**Source.** The bundle and notebook were built from commit `b23342b` (final writeup wording). The Kaggle-portability fixes are listed in §5.

**Private Kaggle dataset** `nfl-bdb-2027-pipeline-code` (code bundle only, 33 files + metadata):
- contents: `src/nfl_bdb/**`; the four frozen scripts (`run_real_capacity`, `run_phase3_screening`, `run_confirmatory_join`, `run_forty_reliability`); `research_notes/code_freeze.json`; `paper/registered_results.json` (aggregates; 0 player-ID-like tokens);
- excluded: no competition files, no player-level extracts, no experiment outputs, no credentials;
- the builder verified **12/12 frozen files present, all SHA-256 digests match**.

**Competition data.** The official `nfl-big-data-bowl-2027` competition data was attached as a `competition_sources` input. **No separate copy of the competition files was created.**

**Kernel settings:** private, internet **disabled**, no GPU or TPU. Inputs are the competition data and the private code dataset only.

**Actual Kaggle mount paths** (resolved by the notebook's discovery code; no local paths, no GitHub, no internet):

| input | path |
|---|---|
| competition data | `/kaggle/input/competitions/nfl-big-data-bowl-2027/nfl-big-data-bowl-2027` |
| code | `/kaggle/input/datasets/<owner>/nfl-bdb-2027-pipeline-code` |

## 2. Kaggle runs

| version | outcome | note |
|---|---|---|
| 1 | completed | ⚠ the scratch directory was under `/kaggle/working`, so Kaggle saved **Parquet copies of the competition files as notebook outputs** (private). Fixed in v2 (§5). See §6 |
| 2 | completed | scratch directory in `/tmp` and deleted at the end; outputs contain only the run log |
| **3 (final)** | **COMPLETE** | v2 + figure manifest + peak-memory print. Kernel run took about 107 s wall-clock from push to completion (about 75 s of notebook execution) |

**Final run (v3), clean session with no saved outputs (the pushed notebook had 0 outputs):**

| check | result |
|---|---|
| environment | Kaggle CPU; Python 3.13.18, polars 1.35.2, matplotlib 3.10.0 |
| cell errors / tracebacks | **0** |
| frozen-file verification | "all 12 frozen files present; all SHA-256 digests verified" |
| data validation | 510 unique prospects; REG 249,269 / PRE 51,759 / POST 13,169; 0 duplicate keys; faulty-game rows 7; > 12.5 yd/s frames {2023: 4, 2024: 3, 2025: 80} (same as local) |
| Combine feature definitions | valid tracked 40 per position DB 102, DL 93, OL 95, TE 34, WR 94 (418); x_peak sums equal the registered values |
| play exclusions | 249,269 → 240,412 → 240,405; 910 without tracking features (= registered) |
| registered sample sizes | **all reproduced:** H1-WR 57 / 19,960 (deep 9,961, short 9,999); H1-TE 17 / 4,170; H1-DB 52 / 16,643; H1-DL 53 / 34,154; H1-OL 53 / 64,285; H2-WR 57 / 19,967 (deep 9,935) |
| registered results vs writeup | H1-WR Δ 0.090 [−0.089, 0.400] INCONCLUSIVE; H2 β_P −0.020 [−0.101, 0.063] INCONCLUSIVE; H1-DL(b) 0.816 [0.160, 1.538], Holm p 0.032 SUPPORTED; H1-DB, H5(b) inconclusive; H1-DL(a) falsified by the 90 % rule; ΔR²_CV −0.024 (LB −0.036); reliability 0.44; pooled DL ρ 0.549 → −0.267. **All identical to the writeup** (`check_writeup_numbers.py` 43/43) |
| figures | **7 rendered** (manifest asserted in the notebook; 1–2 axes each, 1,045–1,188 px wide at notebook dpi) |
| model refits | **none.** No code cell references a confirmatory runner, a REML fit or bootstrap, or the predictor join |
| data exposure | stdout contains 0 player-ID-like tokens and only aggregate tables. The scratch directory was removed; "data-like files in /kaggle/working: none" |
| runtime | about 75 s of notebook execution (validation 14 s, Combine features 20 s, game pipeline 15 s) |
| memory | peak RSS 8.44 GB (Kaggle CPU sessions provide about 30 GB) |
| warnings | stderr holds only Kaggle-image tooling messages (`SyntaxWarning` in mistune/nbconvert, the debugger "frozen modules" notice, nbconvert progress); none come from project code |

**Limitation of this audit:**
- The Kaggle API returns the run log, but not the executed `.ipynb` / HTML.
- Figure rendering is therefore verified by the in-notebook manifest and assertion, not by downloading the images.
- The rendered notebook can be viewed in the private kernel's web page.

## 3. Local reproduction of the same notebook

The same notebook was executed in a simulated Kaggle layout (`<tmp>/kaggle/input/...`, no repository paths):
- 0 errors; 7 images;
- empty working folder;
- peak RSS 4.86 GB.

## 4. Network setting changed

`www.kaggleusercontent.com` was added to the environment's allowlist, so the kernel outputs and log could be downloaded for this audit.

## 5. Files changed (Kaggle portability and safety only)

| commit | file | change |
|---|---|---|
| `e0281e3` | `scripts/build_notebook_11.py` | data/code discovery searches `/kaggle/input` up to 4 levels deep. Needed: the real mounts are `competitions/<slug>/<slug>` and `datasets/<owner>/<slug>`. The code root must hold the freeze manifest |
| `e0281e3` | `scripts/build_kaggle_code_bundle.py` | dataset title shortened to Kaggle's 6–50 character limit |
| `e0281e3` | `notebooks/11_final_submission.ipynb` | rebuilt from the builder (outputs cleared) |
| this commit | `scripts/build_notebook_11.py`, `notebooks/11_final_submission.ipynb` | scratch directory under `/tmp`, never `/kaggle/working`, with assertions; final clean-up cell deletes it and asserts no data-like files in `/kaggle/working`; figure manifest with a count assertion; peak-memory print |
| this commit | `research_notes/phase10_kaggle_execution_audit.md`, `CLAUDE.md` | this audit and the status line |

**Unchanged:** research code, registered results, figures, writeup, preregistration and frozen files (`tests/test_code_freeze.py` passes).

## 6. Open items for the owner (not done here)

1. **Kernel version 1 holds Parquet copies of competition data in its saved outputs.** The kernel is private, so nothing has been exposed. Before making the notebook public, either:
   - delete kernel version 1 (or the whole kernel), and re-push the final notebook as a new kernel; or
   - keep the kernel private and publish a fresh kernel.
   
   Public kernels expose their version history.
2. **The private code dataset** must be made public, or shared, for a public notebook to run for others. It holds only code and aggregates.
3. **Publication and submission** (writeup, public notebook, competition entry) await the separate final review.
