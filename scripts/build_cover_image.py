"""Build paper/kaggle_writeup/cover_image.png (1600 x 900): a purely typographic cover.

Presentation only. It deliberately contains no chart, no schematic and no number, so it cannot be mistaken
for (or counted as) one of the seven content figures. Optional media-gallery asset.
Usage: python scripts/build_cover_image.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TITLE = "What Combine Tracking Can and Cannot\nTell Us About NFL Game Movement"
SUBTITLE = "A reliability-first study of athletic capacity, game-speed translation and receiver separation"
CHIPS = [("CAPACITY", "#0072B2"), ("MOVEMENT", "#E69F00"), ("PERFORMANCE", "#009E73"), ("DEPLOYMENT", "#CC79A7")]


def main():
    fig = plt.figure(figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor("#14213D")
    fig.text(0.06, 0.80, TITLE, fontsize=44, fontweight="bold", color="white", va="top", linespacing=1.15)
    fig.text(0.06, 0.47, SUBTITLE, fontsize=20, color="#E5E5E5", va="top")
    ax = fig.add_axes([0.06, 0.18, 0.88, 0.14]); ax.set_axis_off(); ax.set_xlim(0, 4); ax.set_ylim(0, 1)
    for i, (lab, col) in enumerate(CHIPS):
        ax.add_patch(FancyBboxPatch((i + 0.04, 0.15), 0.86, 0.7, boxstyle="round,pad=0.02,rounding_size=0.12", fc=col, ec="none"))
        ax.text(i + 0.47, 0.5, lab, ha="center", va="center", fontsize=19, fontweight="bold", color="white")
    fig.text(0.06, 0.08, "NFL Big Data Bowl 2027  ·  Combine and regular-season tracking, 2023–2025", fontsize=15, color="#BBBBBB")
    out = ROOT / "paper" / "kaggle_writeup" / "cover_image.png"
    fig.savefig(out, dpi=100, facecolor=fig.get_facecolor()); plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    main()
