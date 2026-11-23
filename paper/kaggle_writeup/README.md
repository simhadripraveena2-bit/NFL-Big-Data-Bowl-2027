# Kaggle Writeup package: create as a DRAFT, do not submit

Kaggle's API and CLI (kaggle 2.2.5 / kagglesdk 0.1.38) **cannot create or edit Writeups**: the Writeups service exposes only a link resolver. The draft must therefore be created in the Kaggle web interface by the account owner.

## Form fields

| field | value |
|---|---|
| Competition | NFL Big Data Bowl 2027 → **Writeups** → New Writeup |
| Title | `From Combine Speed to NFL Movement: What Tracking Reveals About Receiver Separation` |
| Subtitle | `Connecting NFL Combine sensor tracking to regular-season movement and receiver separation, 2023–2025.` |
| Track | **Open Track** only. Do **not** select University Track or Grand Prize |
| Body | contents of `writeup_body.md`. This is `paper/final_writeup.md` without its `#` title line, which goes in the Title field |
| Project Files | public notebook **https://www.kaggle.com/code/simhadripraveena03/from-combine-speed-to-nfl-movement** |
| Media Gallery / cover (if requested) | `cover_image.png` (1600 × 900). Figure 1 plus the title and subtitle; no new results |

## Figures

In the body, replace each `figures/<file>.png` link with the uploaded image. The alt text in the body doubles as the caption.

| order | file | section |
|---|---|---|
| 1 | `paper/figures/fig1_framework.png` | §1 |
| 2 | `paper/figures/fig2_tracking_vs_forty.png` | §3 |
| 3 | `paper/figures/fig3_speed_demand.png` | §4 |
| 4 | `paper/figures/fig4_translation.png` | §5 |
| 5 | `paper/figures/fig5_h2_separation.png` | §6 |
| 6 | `paper/figures/fig6_reliability.png` | §6 (end) |
| 7 | `paper/figures/fig7_dl_role_weight.png` | §7 |

**Tables:**
- the §2 sample-size table (de-indented in Phase 10.3 so it renders as a table);
- the §8 guidance table.

**Total:** 9 visuals.

## Checks before saving the draft

1. All 7 images display; both tables render as tables.
2. The Figure 5 alt text contains balanced square brackets (`[−3.6, +2.3]`). If the editor breaks the image there, replace those brackets with parentheses **in the alt text only**.
3. Word count stays under 2,000: the body is 1,870 words by the project counter (`scripts/check_writeup_numbers.py` counts 1,882 including the title line).
4. Open Track is selected.
5. Click **Save** (draft). **Do not click Submit.**
