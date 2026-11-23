# From Combine Speed to NFL Movement: pipeline code

> **Status: PROPOSED.** This dataset description is pending approval by the project owner.

This dataset holds the code used by the notebook *From Combine Speed to NFL Movement* (NFL Big Data Bowl 2027).

## Contents

| Path | What it is |
|---|---|
| `src/nfl_bdb/` | the pipeline package |
| `scripts/` | the four frozen pipeline scripts |
| `research_notes/code_freeze.json` | SHA-256 manifest of the 12 frozen files |
| `LICENSE` | Apache License 2.0 |
| `NOTICE.md` | licensing by content category |

**This dataset contains no competition data.**

## How to use it

Attach this dataset to a Kaggle notebook, together with the official **NFL Big Data Bowl 2027** competition data. The competition data is available to participants who have accepted the competition rules.

The notebook:
- reads the competition files from `/kaggle/input/`;
- verifies the 12 frozen files against the manifest;
- reproduces the registered sample sizes.

## Licence

- **Code:** Apache-2.0.
- **Competition data:** not included; governed by the competition rules (CC BY-NC 4.0, non-commercial, no redistribution).
- **Aggregate results** (embedded in the notebook and writeup): CC BY-NC 4.0, with attribution to the NFL Big Data Bowl 2027 competition data.

See `NOTICE.md`.
