# Phase 21: final reviewer corrections and submission audit

**Scope:** presentation only.
- No model was fitted, no association was computed, no analysis was rerun, and no phase was reopened.
- The pre-registration, registered results, experiment outputs, `paper/registered_results.json` and the 12 frozen files are unchanged.
- Nothing was published, created on Kaggle or submitted.

## 1. Corrections made (by reviewer item)

| # | reviewer item | correction | source check |
|---|---|---|---|
| 2 | H2 conclusion too strong | Removed "The data rule out a large added separation signal…" and "The interval rules out a gain larger than about 2 inches". New text: no additional predictive value detected; **moderate effects remain possible**; the upper limit +2.3 in is about half the between-player SD (0.13 yd ≈ 4.6 in; 0.063 / 0.1288 = 0.49); the data do not establish that the added effect is zero. Main paragraph and Fig. 5 both use inches: −0.7 in, 95% CI −3.6 to +2.3 in. The yd values (β_P −0.020 [−0.101, 0.063]) moved to the appendix. "Negligible" is not used. | `registered_results.json` h2: `beta_P_in_per_sd`, `beta_P_ci95_in`, `beta_P_ci95_yd`, `between_player_sd_yd` |
| 3 | Fig. 6 reliability over-precise | The text leads with all-route separation: 0.81 (95% CI 0.64–0.89) → 0.61 (0.28–0.78). Short-route 0.22 is described as "also low but very uncertain (95% CI −0.66 to 0.60)" and no longer as a precise drop. The populations are explained: 63 WR with ≥ 100 routes (outcome-only, no tracked-40 requirement) vs 57 in the registered analyses (which also require a valid tracked 40). The split-half vs player-only (0.44) distinction is kept. | `outcome_reliability_wr` rows (`split_half_sb`, `sb_lo`, `sb_hi`, `players_eligible`); preregistration §4 |
| 4 | Evaluator table | Tracked peak row reads verbatim: "Tracked peak speed is a repeatable measurement, but its incremental value beyond the official 40 for game outcomes remains unresolved". The WR game-speed row names *tracked Combine peak speed*, gives ρ 0.58 deep / 0.49 short, and says "not compared with the official 40". The separation row is explicit: the official 40 alone and 40 + tracked peak both failed to beat the position average; adding tracked peak lowered held-out R² by 0.024; "not proof that neither can predict separation". "alongside the 40" removed. | h2 `cv_frozen` (r2_m1 −0.020, r2_m2 −0.044, dr2 −0.024) |
| 5 | Deep/short slopes | Added: raw slopes 0.110 (deep) and 0.113 (short) yd/s per 0.25 yd/s, so the higher deep correlation does not show a stronger per-unit link; the model estimates **less between-player variation on deep routes than on short routes**. The reviewer's reversed suggestion was **not** adopted. | `h1_wr_confirmatory_results.md` §3 (slopes) and §5 (Σ_b deep 0.0353 < short 0.0600) |
| 6 | Figures 2 / 5 / 6 / 7 | Fig. 2: panel B position labels; panel titles state their n (A: athletes with two tracked 40 attempts; B: athletes with tracked peak and official 40); layout widened so labels do not collide. Fig. 5: "Short routes (descriptive comparison)". Fig. 6: caption gives the short-route interval and both populations (computed from the registered file, not hard-coded). Fig. 7: short title "Defensive-line speed, weight and role travel together"; full headline kept in the caption and in the §7 heading. No plotted value or interval changed. | figure source diff: text and layout only |
| 7 | Terminology | "REG" → "regular season" (writeup and Figs. 1, 3, 6, 7). ρ defined at first use. β_P replaced by a plain sentence in the main text. "H1-DL(b)" replaced by "This secondary test… after a Holm correction for testing several secondary comparisons". "Wald" → "model-based 95% interval" (Figs. 4, 7). ICC(3,1) / Spearman–Brown / REML replaced by plain descriptions in the captions (Figs. 2, 4, 5, 6). "H1-WR" → "Primary test". "H5(b)" replaced by its meaning in the appendix ("whether the WR deep–short gap exceeds the OL pass-block–run gap"). The appendix keeps β_P in yd for formal traceability. | preregistration §8 (H5(b) definition) |
| 8 | Contribution | "We make no novelty claim" replaced with the factual statement: "This study combines a pre-registered analysis of how Combine peak speed relates to NFL game movement with a systematic reliability assessment of additional Combine tracking measurements. It shows which measurements are repeatable and where their relationship with game movement and football performance remains uncertain." The drill screening is described as "screened for reliability only", not as a pre-registered experiment. | — |
| 9 | Other wording | Eligibility now reads: "Eligible receivers were drafted much higher than ineligible receivers but were only about 0.02 seconds faster on the official 40". Verified direction: eligible mean draft round 3.8 vs 5.4, undrafted 12% vs 46%, 40 time 4.465 vs 4.485 s. "Full texts not read" removed from the references; the two DOI-verified entries are kept. | `h1_wr_robustness_results.md` R14 |
| 10 | Word count and cover | Counts are in §2. The cover is now **purely typographic** (title, subtitle, four layer names; no chart, schematic or number). The README says to upload it to the cover/media slot only, never into the body. | `scripts/build_cover_image.py` |

**Also changed:**
- To fit the word budget, the shuffled-label control, the measurement-error check and the "simulated null ≤ 0.0125" sentence were cut. They remain in the source reports.
- Alt texts were shortened.

## 2. Final counts (Kaggle body = `writeup_body.md`)

| method | words |
|---|---|
| raw whitespace tokens, including table pipes, bullets and alt text (most conservative) | **1,893** |
| project checker (hyphenated words split; image paths removed) | 1,842 (1,854 with the title line) |
| alphanumeric tokens only | 1,776 |

On the previous version the reviewer's count (1,954) fell between our checker count (1,890) and raw count (1,965). The raw count is therefore the safe upper estimate. **Visuals:** 7 figures + 2 tables = 9; the cover is not in the body.

## 3. Verification

| check | result |
|---|---|
| `scripts/check_writeup_numbers.py` | **70 / 70 OK** |
| checker: mandatory registered wording | primary test, deep separation (inches) and appendix yd values, DL Holm sentence |
| checker: new reviewer checks | half-SD ratio guarded to 0.45–0.55; "moderate effects remain possible"; "not … zero"; slopes and variance direction, also verified in the source note; reliability CIs and populations; ρ definition; contribution; eligibility, verified against R14; table rows; Fig. 2 labels; Fig. 5 label; Fig. 6 caption; Fig. 7 title |
| checker: forbidden phrases | "rule out a large", "rules out a gain", "negligible", "We make no novelty claim", "full texts not read", "alongside the 40", "H5(b)", "H1-DL(b)", " REG ", "Wald", "ICC(3,1)", "Spearman–Brown", "less spread in short", "negative control", "distinct athletic capacity", "equally predictive" |
| manual source comparison | every number in the writeup traced to `registered_results.json`, `h1_wr_confirmatory_results.md`, `h1_wr_robustness_results.md`, `power_analysis.md`, `forty_test_retest.md`, `game_outcome_inventory.md` or `phase18_research_closeout.md` |
| full test suite | 113 passed |
| `tests/test_code_freeze.py` and direct SHA-256 | pass; 12 / 12 |
| registered files | `git diff` empty for `registered_results.json`, `preregistration.md` and `code_freeze.json`; experiment outputs untouched |

## 4. Unresolved owner actions

1. Create the Kaggle Writeup **draft** in the web UI:
   - paste `writeup_body.md`;
   - upload the 7 figures into the body and the cover to the cover/media slot only;
   - **read the editor's word counter** (stop if > 1,950);
   - select Open Track;
   - save as a draft without submitting.
2. Republish the public notebook / code dataset if you want their figure titles and captions to match. Plotted values are identical.
3. Approve a final NOTICE / licence; the published header still says PROPOSED.
4. Post or drop the drafted forum licensing question.
5. Make the final submission decision before 2027-01-06 23:59 UTC.
