"""Render the writeup figures from paper/registered_results.json into paper/figures/ (Phase 9B).

Draws registered numbers only (see src/nfl_bdb/visualization/submission_figures.py).
Usage: python scripts/build_submission_figures.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nfl_bdb.visualization import submission_figures as sf  # noqa: E402


def main():
    R = json.loads((ROOT / "paper" / "registered_results.json").read_text())
    out = ROOT / "paper" / "figures"; out.mkdir(parents=True, exist_ok=True)
    sf.apply_style()
    for name, fn in sf.FIGURES.items():
        fig = fn(R)
        fig.savefig(out / f"{name}.png", bbox_inches="tight", dpi=200)
        plt.close(fig)
        print("wrote", out / f"{name}.png")


if __name__ == "__main__":
    main()
