# Phase 20: final submission revision and quality audit

**Scope:** presentation only.
- No model was fitted. No Combine × outcome association was computed. H1, H2 and the secondary analyses were not rerun.
- No frozen file, pre-registration text, registered result, experiment output or `paper/registered_results.json` was changed.
- Nothing was published, created on Kaggle or submitted.

## 1. Narrative change

| | before | after |
|---|---|---|
| Title | From Combine Speed to NFL Movement: What Tracking Reveals About Receiver Separation | **What Combine Tracking Can and Cannot Tell Us About NFL Game Movement** |
| Subtitle | Connecting NFL Combine sensor tracking to regular-season movement and receiver separation, 2023–2025 | **A reliability-first study of athletic capacity, game-speed translation and receiver separation** |
| Story order | framework → tracking vs 40 → demand → H1 → H2 → DL → guidance | framework → **which measurements are reliable** → demand → H1 (with **why inconclusive**) → H2 + separation context → DL role/weight → **what can and cannot be trusted** |

## 2. Section-by-section changes (`paper/final_writeup.md`)

| section | change | source of every number |
|---|---|---|
| §1 | Shortened. Separation introduced as a performance outcome. One-sentence roadmap of the six-step story. | — |
| §2 Eligibility | **New.** Players need ≥ 100 qualifying REG opportunities (routes, coverage snaps, pass rushes or pass blocks). This excludes rarely used players and selects on playing time and draft position: strongly on draft capital, weakly on speed (≈ 0.02 s on the 40). Explicitly **no claim about draft busts or career success**. | preregistration §4 table; `h1_wr_robustness_results.md` R14 |
| §2 Separation source | **New.** `separation_at_pass_forward` is the competition-supplied NGS field from `player_play` and was **not** rebuilt from the cohort-only tracking. It exists for every route on a thrown pass (targeted or not) and is absent for sacks and scrambles. The tracked cohort-defender match is described as a consistency check on a subset, **not** validation of every defender assignment. | `game_outcome_inventory.md` (rows 47, 69–76) |
| §2 Safeguards | Compressed. Phase numbers, run IDs and commit hashes removed. | — |
| §3 (was "What does tracking add beyond the 40?") | Retitled as a reliability section. "Not the same thing as the 40" replaced by "the 40 explains most, not all": the unexplained third mixes real differences with measurement error in both measures; the 40's reliability is not identifiable; **no separate-capacity claim**. "5% unique" → "5% not explained by the 40". Added: tracked 0–10 yd time barely repeatable (WR 0.20). Added a one-bullet summary of the drill-measure screening, as reliability evidence only and never outcome-linked: shuttle 0.21, three-cone 0.34, DL bend L/R 0.14–0.31, WR route start 0.69 (relative only); none validated. | `forty_test_retest.md`; `phase18_research_closeout.md` §3.2 |
| §4 | Wording tightened; descriptive caveat kept verbatim. | registered results (speed demand) |
| §5 H1 | **New power paragraph:** 80% power only for Δ 0.27–0.33 (central ≈ 0.30); power ≈ 0.44 at Δ 0.20; inconclusive ≠ equivalence. Mandatory H1 wording and numbers unchanged. | `power_analysis.md` §1 and the central-scenario table |
| §6 H2 | Demotion sentence moved here. Content unchanged. The "60% of bootstrap fits at zero" detail dropped for length (still in `h2_estimation_results.md`). Separation-context paragraph merged. | registered results (H2, outcome reliability) |
| §7 DL | Heading now "The pooled **defensive-line** speed association is substantially sensitive to role and body-weight adjustment". States that the **supported contrast is the change** between pooled and adjusted estimates; that the jointly adjusted −0.27 is imprecise (Wald interval spans zero) and **not evidence that speed hurts linemen**. Numbers 0.55 / −0.05 / −0.08 / −0.27 / 0.05 / 0.01 / 0.82 [0.16, 1.54] / Holm p 0.032 unchanged. | registered results (`dl_b`, contrasts); `dl_role_weight_interpretation.md` |
| §8 | Guidance table and limitations merged into one **"can and cannot trust"** table (still one table). Limitations shortened. The game-speed follow-up (Phase 19) is mentioned once, as a feasibility decision: never fitted to real data, supports no conclusion either way. | `phase19_game_speed_incremental_feasibility.md` |
| Appendix | Run IDs, seeds and commits removed. Reproducibility and literature (two DOI-verified, abstract-only references) kept. | — |

**Claims removed or softened:**
- "for receivers and defensive backs it is not the same thing as the 40" (could imply a distinct capacity);
- "Record tracked peak speed … don't treat them as interchangeable" (softened to "alongside the 40; not as a separate capacity");
- the Figure 6 title "how he is used, not who he is" (overstated);
- the Figure 4 title grouping DL with WR (the DL association is role- and weight-sensitive).

**No new significance claims** were introduced. The only "supported" result remains H1-DL(b), with its registered meaning.

## 3. Figure review (all seven inspected visually)

| fig | issue found | change (text only; plotted values unchanged) |
|---|---|---|
| 1 | Separation box did not say where the value comes from | Box reads "supplied NGS nearest-defender distance; thrown passes" |
| 2 | Title "not the same as the 40" implied a distinct construct | Title: "Tracked top speed is highly repeatable; for WR and DB the 40 explains about two-thirds of it". Panel B: "Variance the official 40 does not explain". Caption: the remainder includes measurement error; not evidence of a separate capacity |
| 3 | Axis label used "his" | "their own top game speed" |
| 4 | Title put DL alongside WR as "shows up in game speed" | Title: "Combine top speed tracks WR game speed; DB and OL links are weak; for DL see Figure 7". WR note adds "80% power needs Δ ≈ 0.3" |
| 5 | Provenance of separation not stated | Caption adds "Separation = competition-supplied NGS value (player_play), not recomputed" |
| 6 | Title overstated ("how he is used, not who he is"); caption did not explain why split-half 0.61 > H2 0.44 | Title: "Much of a receiver's raw separation reflects route and coverage context". Caption: split halves share team-seasons, so they include team effects; the H2 model separates them (0.44) |
| 7 | Heading wording; caption did not flag imprecision | Title uses "defensive-line"; caption: jointly adjusted value imprecise, not evidence that speed hurts linemen |

**For every figure:**
- every axis has units;
- intervals are shown wherever one exists;
- point estimates are labelled separately from registered decisions.

No figure was added. The visual count stays at **7 figures + 2 tables = 9** (limit < 10). Figures are still drawn only from `paper/registered_results.json` (`scripts/build_submission_figures.py`).

**Cover image.** Rebuilt with the new title and subtitle by the new presentation-only `scripts/build_cover_image.py` (1600 × 900, Figure 1 plus text).

## 4. Synchronisation

- `paper/kaggle_writeup/writeup_body.md` = `final_writeup.md` minus the title line.
- `paper/kaggle_writeup/README.md`:
  - new title and subtitle;
  - word counts updated;
  - Figure 5 alt text no longer contains square brackets, so the old bracket warning was replaced;
  - cover-builder reference added.
- `paper/figure_plan.md`: titles updated, plus a revision note.

## 5. Checks

| check | result |
|---|---|
| `scripts/check_writeup_numbers.py` | **55 / 55 OK**. Updated: section-7 headline, "not explained by the 40" phrase. New checks: title; H1 MDE 0.27–0.33, central 0.30 and power 0.44, each also verified as present in `power_analysis.md`; separation provenance, coverage and scope sentences; eligibility; no bust claim; no separate-capacity claim; DL supported-contrast and imprecision sentences; follow-up never fitted. Forbidden phrases (e.g. "not the same thing as the 40", "distinct athletic capacity", "equally predictive", "significantly", "Phase 19", "commit") are absent |
| words | writeup 1,902 incl. title and alt text; **Kaggle body 1,890** (limit 2,000) |
| visuals | 7 figures + 2 tables = 9 |
| numbers not covered by the checker | verified by hand against the source: DB ρ 0.09–0.29 and OL 0.03–0.11 (`rho_by_context`); DL/OL ≤ 2.5% near-top share; DL joint Wald interval [−0.71, 0.18]; tracked 0–10 WR 0.199; drill reliabilities (closeout matrix); man/zone 1.55 / 3.15 yd; robustness Δ 0.073–0.119; slopes 0.110 / 0.113 yd/s; R14 ≈ 0.02 s |
| full test suite | 113 passed |
| `tests/test_code_freeze.py` | pass (12 / 12 frozen hashes) |
| registered files | `git diff` empty for `registered_results.json`, `preregistration.md` and `code_freeze.json`; experiment outputs untouched |

## 6. Unresolved owner actions

1. **Create the Kaggle Writeup draft in the web UI.** The API cannot do it. Paste `writeup_body.md`, upload the 7 figures and the cover, select Open Track, and **save as a draft; do not submit** until you decide.
2. **Public notebook and code dataset** still render the *previous* figure titles. Plotted values are identical. Either republish them so the titles match, or accept the mismatch: the writeup uses `paper/figures/`.
3. **NOTICE / licence:** the published NOTICE header still says PROPOSED. Approve a final version (Phase 10.2–10.3 items).
4. **Forum licensing question** (`release/FORUM_QUESTION_DRAFT.md`) is still unposted. Post it or drop it.
5. **Final submission decision** before 2027-01-06 23:59 UTC.
