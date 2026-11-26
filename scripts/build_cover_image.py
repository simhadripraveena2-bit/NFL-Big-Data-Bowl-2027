"""Build paper/kaggle_writeup/cover_image.png (1600 x 900): title, subtitle and the rendered Figure 1.

Presentation only: no data is read except the already-rendered Figure 1 image; no new results.
Usage: python scripts/build_cover_image.py   (run scripts/build_submission_figures.py first)
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TITLE = "What Combine Tracking Can and Cannot Tell Us About NFL Game Movement"
SUBTITLE = "A reliability-first study of athletic capacity, game-speed translation and receiver separation"


def main():
    fig = plt.figure(figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor("white")
    fig.text(0.04, 0.93, TITLE, fontsize=27, fontweight="bold", color="#222222", va="top")
    fig.text(0.04, 0.85, SUBTITLE, fontsize=17, color="#444444", va="top")
    fig.text(0.04, 0.80, "NFL Big Data Bowl 2027 · Combine and regular-season tracking, 2023–2025", fontsize=13, color="#666666", va="top")
    ax = fig.add_axes([0.12, 0.02, 0.76, 0.74]); ax.set_axis_off()
    ax.imshow(mpimg.imread(ROOT / "paper" / "figures" / "fig1_framework.png"))
    out = ROOT / "paper" / "kaggle_writeup" / "cover_image.png"
    fig.savefig(out, dpi=100); plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    main()
