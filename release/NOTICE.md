# NOTICE: licensing and attribution

> **Status: PROPOSED, revision 2 (Phase 10.2). Pending:**
> 1. the project owner's approval;
> 2. confirmation of copyright ownership;
> 3. the competition host's answer to the licensing clarification (`release/FORUM_QUESTION_DRAFT.md`).
>
> Nothing here has been applied to the repository root or published. This is not legal advice.

**Project:** From Combine Speed to NFL Movement (NFL Big Data Bowl 2027 entry)

**Copyright:** 2026 Simhadri Praveena

This project contains four kinds of material. They are treated separately.

## 1. Original source code: Apache License 2.0

**Covers:**
- `src/nfl_bdb/**`;
- `scripts/*.py`;
- `research_notes/code_freeze.json` (SHA-256 manifest);
- the **code cells** of the project notebooks, including `notebooks/11_final_submission.ipynb`.

**Licence:** the **Apache License, Version 2.0** (see `LICENSE`), subject to confirmation of copyright ownership. It is OSI-approved and does not restrict commercial use. The project intends this to satisfy the competition's winner-licence provision for source code (rules §2.5.a.1).

**Not included:** third-party libraries (numpy, polars, scipy, matplotlib, statsmodels and others). They remain under their own licences.

## 2. Original written and visual expression: licence not yet chosen

**Covers:**
- the prose of the Kaggle Writeup and `paper/final_writeup.md`;
- the markdown and explanatory text of the notebooks;
- the design of the figures and tables (layout, captions, titles, visual encoding).

**Licence:** © the copyright holder. **No licence is granted yet.** The licence will be chosen after the host clarifies whether the winner-licence provision covers the written report (forum question 2).

**Until then:** these materials may be viewed on Kaggle under Kaggle's terms of service and the competition rules, and no further permission is implied.

## 3. Statistical results derived from the competition data: no licence asserted

**Covers:** the numerical results of the registered analyses, for example:
- point estimates and confidence intervals;
- p-values and decisions;
- sample sizes and reliabilities;
- the values plotted in the figures;
- the aggregate results embedded in the notebook and writeup.

**What the project does and doesn't claim:**
- These results were produced by the project's analysis of the competition data. They are aggregate statistics: they contain **no** raw records, player-level extracts or tracking frames.
- **The project does not claim** that these statistics are, or are not, adapted material of the competition data under CC BY-NC 4.0. It **does not grant any licence** to them beyond what the competition rules permit.
- They are published, if at all, only as part of the competition Writeup and Notebook, as the competition rules allow. Whether this is allowed is forum question 1.
- **Any reuse is subject to the competition rules,** including their non-commercial terms.

**Attribution** (required wherever the results appear):

> "Results derived from the NFL Big Data Bowl 2027 competition data (National Football League, via Kaggle), used under the competition rules."

This wording will be replaced by the host's recommended wording if one is given (forum questions 3 and 4).

## 4. NFL competition data: not included, not licensed here

- **Never distributed:** no competition file, copy, Parquet or CSV extract, player-level record or tracking frame is distributed with this project or saved in any notebook output.
- **Access:** only through the official Kaggle competition, for participants who have accepted its rules.
- **Governing terms:** the rules list Data Access and Use as **CC BY-NC 4.0**, permit non-commercial use only (§2.4.a), and prohibit redistribution to non-participants (§2.4.b).
- **Nothing in this project grants any right to the competition data.**

## Mixed-content notebook

The public notebook combines categories 1–3.

| part of the notebook | category |
|---|---|
| code cells | 1 (Apache-2.0) |
| markdown cells | 2 (licence not yet chosen) |
| embedded and printed results, and rendered figures | 3 (no licence asserted) |

Kaggle labels public notebooks with its standard open-source notice. To avoid that notice being read as covering categories 2 and 3, the published notebook should carry a short cell repeating this table. Its exact wording waits for the host's answer to forum question 3.
