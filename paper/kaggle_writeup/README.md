# Kaggle Writeup package: create as a DRAFT, do not submit

Kaggle's API and CLI (kaggle 2.2.5 / kagglesdk 0.1.38) **cannot create or edit Writeups**: the Writeups service exposes only a link resolver. The draft must therefore be created in the Kaggle web interface by the account owner.

## Form fields

| field | value |
|---|---|
| Competition | NFL Big Data Bowl 2027 → **Writeups** → New Writeup |
| Title | `What Combine Tracking Can and Cannot Tell Us About NFL Game Movement` |
| Subtitle | `A reliability-first study of athletic capacity, game-speed translation and receiver separation.` |
| Track | **Open Track** only. Do **not** select University Track or Grand Prize |
| Body | contents of `writeup_body.md`. This is `paper/final_writeup.md` without its `#` title line, which goes in the Title field |
| Project Files | public notebook **https://www.kaggle.com/code/simhadripraveena03/from-combine-speed-to-nfl-movement** |
| Media Gallery / cover (optional) | `cover_image.png` (1600 × 900; `scripts/build_cover_image.py`). Purely typographic (title, subtitle, four layer names): no chart, schematic or number. Upload it **only** to the media gallery / cover slot, **never into the body**, so it cannot count as an eighth figure |

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
2. No alt text contains square brackets (the Figure 5 interval is written as "95% CI −3.6 to +2.3"), so the image links should not break.
3. Word count stays under 2,000. Body counts (Phase 21): **1,893** raw whitespace tokens including table pipes, bullets and alt text (most conservative); 1,842 by the project checker (`scripts/check_writeup_numbers.py`, 1,854 with the title line); 1,776 alphanumeric words. On the previous version the reviewer's count (1,954) fell between our checker count (1,890) and our raw count (1,965), so the raw count is the safe upper estimate; margin ~107 words. **Check the Kaggle editor's own word counter after pasting**; if it reports > 1,950, stop and report rather than trimming ad hoc.
4. The body contains exactly 7 images and 2 tables (9 visuals); the cover is not in the body.
5. Open Track is selected.
6. Click **Save** (draft). **Do not click Submit.**
