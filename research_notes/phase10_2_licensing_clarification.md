# Phase 10.2: competition licensing clarification

**Status:** drafts for owner review.
- Nothing posted; no private contact with the host.
- Nothing made public; nothing submitted.
- No scientific result and no notebook source changed.

## 1. Forum question (draft, not posted)

`release/FORUM_QUESTION_DRAFT.md`, about 230 words, for the public Discussion forum of the competition. It quotes only the official rules:
- rule 7 "Data Access and Use: CC BY-NC 4.0";
- §2.4.a non-commercial use;
- §2.4.b no redistribution to non-participants;
- §2.5.a.1 winner licence.

It asks the host's four questions:
1. May aggregate statistical findings be published in public Writeups and Notebooks without raw data or player-level extracts?
2. Does the winner-licence requirement cover the written report and aggregate results, or only software and model code?
3. How should derived results and figures be marked inside notebooks that also contain Apache-2.0 code?
4. Is there a recommended attribution or licensing statement?

## 2. Revised licensing language (`release/NOTICE.md`, revision 2)

**Changes from Phase 10.1 (revision 1):**

| category | revision 1 | revision 2 |
|---|---|---|
| original source code (+ notebook **code cells**) | Apache-2.0 | **unchanged:** Apache-2.0, subject to confirmation of copyright ownership |
| original written and visual expression (writeup prose, notebook markdown, figure and table design) | writeup: "owner to decide; suggested CC BY-NC 4.0" | **separated out as its own category; no licence chosen.** © holder, no licence granted until the winner-licence question (Q2) is answered |
| statistical results derived from the data (estimates, CIs, sample sizes, plotted values) | asserted **CC BY-NC 4.0** | **no licence asserted**, and no claim either way about whether they are CC BY-NC adapted material. Published only as the rules allow, with any reuse subject to the rules. Interim attribution string, to be replaced by the host's wording if given (Q3/Q4) |
| competition data | not included; rules govern | **unchanged** |
| mixed-content notebook | NOTICE cell proposed (embedded results CC BY-NC) | NOTICE cell proposed as a **mapping table** (code cells → Apache-2.0; markdown → category 2; results and figures → category 3), with wording pending Q3 |

**Also revised:** `release/DATASET_README.md` (aggregate results: no licence asserted; not in the dataset).

**Unchanged:** `release/LICENSE-Apache-2.0.txt`.

**Superseded:** the CC BY-NC claim for aggregate results in `phase10_1_release_licensing_audit.md` §1.3 is replaced by this revision.

## 3. Items to refresh before any publication

1. **Private Kaggle release dataset** `from-combine-speed-to-nfl-movement-code` still contains **revision 1** of `NOTICE.md` and `README.md`. Before it is made public, create a new dataset version from `scripts/build_kaggle_code_bundle.py --release`, which copies the revised files.
2. **Notebook licence cell.** After the host answers, add the agreed cell to the notebook. This changes the notebook source and needs one more validation run of the private release notebook.
3. **Copyright holder** placeholder in `NOTICE.md`.
4. **Writeup licence:** chosen only after Q2 is answered.

## 4. Constraints respected

- No forum post.
- No private contact with the host.
- No visibility change on Kaggle.
- No submission.
- No change to results, figures, writeup or notebook source.
