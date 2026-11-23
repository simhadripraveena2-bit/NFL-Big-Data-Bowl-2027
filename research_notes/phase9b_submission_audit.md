# Phase 9B: final submission quality audit

**Scope.** Prepare the Big Data Bowl 2027 entry from the existing registered results (Path A).
- No statistical test was run, no model fitted, and no new Combine-to-outcome association computed or inspected.
- The frozen code, the preregistration and all registered outputs are unchanged.
- The Kaggle entry was **not** submitted.

## 1. Deliverables

| deliverable | path | built by |
|---|---|---|
| writeup | `paper/final_writeup.md` | hand-written from registered results |
| figure plan | `paper/figure_plan.md` | — |
| figures (7) | `paper/figures/fig1…fig7*.png` | `scripts/build_submission_figures.py` → `src/nfl_bdb/visualization/submission_figures.py` |
| registered results (aggregates, provenance-tagged) | `paper/registered_results.json` | `scripts/build_registered_results.py` (reads run outputs only) |
| public notebook | `notebooks/11_final_submission.ipynb` (executed copy) | `scripts/build_notebook_11.py` |
| Kaggle code bundle (not uploaded; git-ignored) | `build/kaggle_code_bundle/` | `scripts/build_kaggle_code_bundle.py` |
| number check | — | `scripts/check_writeup_numbers.py` |

**New code:** four scripts and one visualization module. None of them is a frozen file. `tests/test_code_freeze.py` passes (all 12 frozen files unchanged).

## 2. Every reported number checked against its source

`scripts/check_writeup_numbers.py` formats **38 claims** from `paper/registered_results.json` and requires each to appear verbatim in the writeup.
- **Result: 38/38 OK** (exit 0).
- `registered_results.json` itself is extracted programmatically from the registered run files: H1-WR `20261121T223645Z`, H2 `20261122T012339Z`, secondary `20261122T015315Z`, join `20261121T135032Z`, 40 reliability `20261121T134306Z`, Phase 3 screening `20261121T010253Z`.

**Numbers in the writeup that are not in the JSON, traced by hand:**

| writeup claim | value | source note |
|---|---|---|
| raw slopes ≈ 0.11 yd/s per 0.25 yd/s | 0.11 | `research_findings_summary.md` §4 (RFS) |
| robustness variants Δ 0.07–0.12 | 0.073–0.119 | RFS §4; `h1_wr_robustness_results.md` |
| ≈ 0.3 detectable with 57 WRs | MDE 0.27–0.33 | `power_analysis.md` |
| play-to-play SD 1.73 yd | 1.73 | RFS §8 |
| 60 % of bootstrap fits at zero player variance | 60 % | RFS §5 |
| man vs zone median separation differs by 1.6 yd | 1.55 vs 3.15 | `game_outcome_inventory.md` §5 |
| EDGE ≈ 258 lb / 10.6 yd/s; interior ≈ 304 lb / 9.7 yd/s | 257.6 / 10.57; 304.2 / 9.71 | `dl_role_weight_diagnostics.json` (role means) |
| Phase 4 null size ≤ 0.0125; power 0.45 at Δ 0.2, 0.94 at 0.35 | same | `synthetic_validation.md`; CLAUDE.md Phase 4 |
| matched 332, valid tracked 40 = 418 | same | join validation (checked by script) |
| DL pass-rush advantage ≥ 0.15 not supported | 90 % upper 0.124 | `secondary_family_results.md` |

All agree. **Rounding convention:** two decimals in prose, three for the mandatory registered statements; inches = yards × 36.

## 3. Statistical conclusions against the registered decisions

| analysis | registered decision | writeup wording | consistent |
|---|---|---|---|
| H1-WR | INCONCLUSIVE, Δ 0.090 [−0.089, 0.400] | "H1-WR: INCONCLUSIVE. Δ = … 0.090, 95% CI [−0.089, 0.400]"; "not supported … not ruled out" | ✅ |
| H2 | INCONCLUSIVE, β_P −0.020 [−0.101, 0.063]; secondary, estimation-focused (D4, pre-association) | mandatory sentence verbatim. Also: the demotion and its timing are stated; "no incremental predictive value was detected"; "does not show that speed has no effect"; true-scale partial not estimable (reliability 0.44) | ✅ |
| H1-DL(b) | SUPPORTED after Holm (p 0.032) | "supported after Holm adjustment (p = 0.032)"; "substantially sensitive to role and weight adjustment"; "not a causal statement" | ✅ |
| H1-DL(a) | FALSIFIED by the 90 %-upper < 0.15 rule | "a pass-rush advantage of 0.15 or more is not supported" (the RFS-approved wording; not a claim of zero) | ✅ |
| H1-DB, H5(b) | INCONCLUSIVE | "weak and imprecise"; inconclusive in Fig 4 | ✅ |
| H5(a), H5(c), H1-global | uninformative (estimation) | OL "uninformative" (Fig 4); H5(c) and H1-global not featured | ✅ |
| TE | descriptive | "descriptive only" | ✅ |

**Wording rules applied:**
- No causal language.
- No novelty claim (the closing sentence of §8 says so explicitly).
- "Inconclusive" and "not detected" are never turned into "no effect".
- Capacity, movement, performance and deployment are named as separate layers: Fig 1, the §1 definitions, and the "Layer" column of the §8 table.

## 4. Competition limits and pass/fail requirements

| requirement (official pages, read via the Kaggle CLI in Phase 9A) | status |
|---|---|
| ≤ 2,000 words | **1,817 words**, counting the whole file: body, tables, appendix, references and image alt text. The body alone is about 1,550 |
| < 10 tables + figures | **9** (7 figures + 2 tables) |
| Pass/fail 1: explicit Combine-tracking → REG *performance* link | §1 names H2 as the explicit Combine-to-performance analysis; §6 reports it with the mandatory wording; Fig 5 |
| Pass/fail 2: readable markdown, embedded visuals, attached public notebook | markdown with 7 embedded figures. Notebook ready but **not yet published** (owner step, §6) |
| writeup uses player tracking data | yes: Combine tracking (predictor) and game tracking (movement, separation) |
| code mostly in an appendix or linked notebook | yes: the writeup holds no code; methods are in the appendix and notebook |

## 5. Figure accessibility

| check | result |
|---|---|
| colour-blind-safe palette | Okabe–Ito; colour is never the sole cue (direct labels, marker shape, row position) |
| text contrast (WCAG 2.1, ≥ 4.5:1) | annotation text dark (15.9:1), grey (5.3:1) or blue (5.2:1). Lower-contrast hues (green 3.4, vermillion 3.9, purple 3.1, sky 2.3, orange 2.3) are used only for marks, never for small text |
| graphic contrast (≥ 3:1) | low-contrast fills (sky, orange) have a dark outline |
| units and labels | every axis has units (yd/s, inches, %, lb, correlation, R²) |
| uncertainty | shown wherever an interval exists. Point-only panels (Fig 2B, Fig 3) say so and give n |
| misleading axes | correlation axes span −1 to 1 with a zero line; bars start at 0; the one clipped interval (short-route separation, −0.66) is marked with an arrow |
| alt text | all 7 figures (133 words in total) |
| text size | ≥ 8.5 pt at 200 dpi |

Each figure was reviewed visually after rendering, and overlapping labels and footnotes were fixed.

## 6. Public notebook: reproducibility and safety

**Execution.** Executed end to end with `jupyter nbconvert --execute` against the real competition CSVs, using a scratch work directory outside the repository.
- 0 errors; 7 figures; 37–104 s locally (4 CPUs, 15 GB).
- The executed copy is committed. It contains aggregate outputs only.

**Verified inside the notebook by assertions:**

| check | result |
|---|---|
| frozen-code manifest | all 12 files unchanged |
| data validation | 510 unique prospects; REG 249,269 / PRE 51,759 / POST 13,169 player-play rows; 0 duplicate keys; faulty-game rows and > 12.5 yd/s spikes counted |
| Combine feature definitions | `forty_fits` + `predictor_table` (frozen) reproduce the registered predictor table exactly: valid tracked 40 per position (DB 102, DL 93, OL 95, TE 34, WR 94; total 418) and x_peak sums to 1e-6 |
| game features and exclusions | `run_phase3_screening.features` + `outcome_table` (frozen) reproduce the registered exclusion log (249,269 → 240,412 → 240,405; 910 rows without tracking features) |
| registered samples | `h1_eligible` / `h2_eligible` (frozen) reproduce every registered player and play count: WR 57/19,960; TE 17/4,170; DB 52/16,643; DL 53/34,154; OL 53/64,285; H2 57/19,967 (deep 9,935) |

**One-run restrictions respected:**
- The notebook never calls `run_h1_wr_confirmatory.py`, `run_h2_estimation.py`, `run_secondary.py` or `run_confirmatory_join.py`, and never writes to `data/interim` or `experiments/`. There is an assertion on the work path.
- Eligibility uses only the *validity flag* of the tracked 40. Combine values are never joined to plays.
- Registered results are embedded read-only, with run IDs, commits and seeds.
- §9 of the notebook documents the reproduction route: a new run ID labelled *reproduction*, with approval, never replacing the registered result.

**No credentials, no redistribution:**
- The notebook reads no environment secrets. A scan for `KAGGLE_KEY` / `KGAT` / `kaggle.json` finds nothing in any deliverable.
- On Kaggle it reads the attached competition dataset and writes only to `/kaggle/working`.
- Nothing derived at player or play level is committed. `registered_results.json` holds aggregates only.

**Kaggle execution requirements (not testable from this session):**
- Two attachments: the competition data, and the code bundle (`build/kaggle_code_bundle/`, 33 files, 257 KiB: `src/nfl_bdb`, two frozen feature scripts, the freeze manifest and the registered results; no data).
- The notebook locates both automatically (`/kaggle/input/...`).
- Requirements: polars ≥ 1.0 (asserted, with a pip hint), scipy, matplotlib. No internet and no GPU needed.
- Expected run time on a Kaggle CPU session: a few minutes. Peak memory locally was well under 15 GB (the pipeline processes one season at a time).
- **Not yet verified on Kaggle itself.** That needs the owner to upload the bundle (`kaggle datasets create`) and push the notebook. Both are outward-facing and were not done.

## 7. Consistency between notebook and writeup

- **Figures:** the notebook's figures come from the same module and the same embedded JSON as `paper/figures/`, so they are identical.
- **Decisions:** the notebook's decision table (§7) shows the same estimates, CIs, labels and Holm p-values as the writeup. Its wording cell repeats the mandatory statements.
- **Samples:** the sample sizes printed by the notebook equal the §2 table in the writeup.

## 8. Remaining owner actions before submission (not done here)

1. **Kaggle username:** replace `<KAGGLE_USERNAME>` in `build/kaggle_code_bundle/*-metadata.json`.
2. **Publish:** upload the code bundle as a dataset, push the notebook, run it once on Kaggle, then make it public.
3. **Writeup assets:** upload the 7 PNGs to the Kaggle writeup, and replace the relative image paths.
4. **Link:** add the public notebook link to the writeup appendix.
5. **Licence:** choose the open-source licence for the code (rules §5 require an OSI licence if the entry wins; the template uses Apache-2.0).
6. **Final read-through, then submit** before 2027-01-06 23:59 UTC.
