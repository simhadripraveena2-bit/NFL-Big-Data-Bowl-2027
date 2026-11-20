"""Shared matplotlib style (reference data-viz palette, light mode)."""
from __future__ import annotations

import matplotlib as mpl

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
TEXT, TEXT2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1", "#fcfcfb"
# Fixed position -> colour mapping (colour follows the entity, never its rank)
POSITION_ORDER = ["WR", "TE", "OL", "DL", "DB"]
POSITION_COLOR = dict(zip(POSITION_ORDER, SERIES))


def apply() -> None:
    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": MUTED, "axes.labelcolor": TEXT2, "xtick.color": TEXT2, "ytick.color": TEXT2,
        "text.color": TEXT, "axes.titlecolor": TEXT, "axes.titlesize": 11, "axes.titleweight": "bold",
        "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
        "legend.frameon": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
        "lines.linewidth": 1.6, "axes.prop_cycle": mpl.cycler(color=SERIES), "figure.dpi": 110,
        "font.family": "DejaVu Sans",
    })
