"""Real game-tracking sequences and kinematic estimators (Phase 2 feasibility).

A *sequence* is one player on one play. Exclusions (Phase 1 / CLAUDE.md):
  * plays 1289 and 1314 of game 2025101205 (tracking fault);
  * any sequence containing a frame with provided speed s > 12.5 yd/s (physically implausible spike).
Only REG and POST games are used by default (PRE optional for sensitivity).

Kinematic estimators (all per sequence; units yd, s):
  pos_sgW  : Savitzky–Golay (window W, quadratic) derivatives of provided x, y
             -> speed, tangential acceleration a_t = (v . a)/|v|, normal acceleration a_n = |v x a|/|v|
  s_diff   : central difference of the provided speed s (vendor-smoothed)
  s_sgW    : Savitzky–Golay first derivative of provided s
  dir_rate : normal acceleration from the provided heading: a_n = s * |d dir / dt| (dir in radians)
The provided ``a`` is an unsigned magnitude of the full acceleration vector (Phase 1), so it mixes
braking with turning; it is kept only for comparison.
"""
from __future__ import annotations

import numpy as np
import polars as pl
from scipy.ndimage import convolve1d
from scipy.signal import savgol_coeffs

from nfl_bdb.data.io import load

FAULTY = [(2025101205, 1289), (2025101205, 1314)]
S_MAX_PLAUSIBLE = 12.5


COLS = ["game_id", "play_id", "nfl_id", "time", "x", "y", "s", "a", "dir", "event"]


def load_game_sequences(seasons=(2023, 2024, 2025), season_types=("REG", "POST"), cols=COLS):
    """Load game frames (selected columns), apply exclusions, add integer ``seq`` (player-play) id.
    Returns (frames DataFrame sorted by seq/time, exclusion report dict)."""
    games = load("games").filter(pl.col("season_type").is_in(list(season_types))).select("game_id", "season", "season_type")
    frames = []
    for y in seasons:
        frames.append(load(f"game_tracking_{y}").select(cols).join(games, on="game_id").collect())
    df = pl.concat(frames)
    n0 = df.select("nfl_id", "game_id", "play_id").n_unique()
    faulty = pl.DataFrame({"game_id": [g for g, _ in FAULTY], "play_id": [p for _, p in FAULTY]})
    df = df.join(faulty, on=["game_id", "play_id"], how="anti")
    n1 = df.select("nfl_id", "game_id", "play_id").n_unique()
    bad = df.filter(pl.col("s") > S_MAX_PLAUSIBLE).select("nfl_id", "game_id", "play_id").unique()
    df = df.join(bad, on=["nfl_id", "game_id", "play_id"], how="anti").sort("nfl_id", "game_id", "play_id", "time")
    key = df.select(((pl.col("nfl_id").diff() != 0) | (pl.col("game_id").diff() != 0) | (pl.col("play_id").diff() != 0)).fill_null(True).alias("new"))
    df = df.with_columns(key["new"].cast(pl.Int64).cum_sum().alias("seq"))
    rep = dict(sequences_loaded=n0, removed_faulty_game=n0 - n1, removed_speed_spike=bad.height, sequences_kept=int(df["seq"].max()))
    return df, rep


def _edge_mask(seq: np.ndarray, h: int) -> np.ndarray:
    n = len(seq); bad = np.zeros(n, bool); idx = np.arange(n)
    for k in range(-h, h + 1):
        bad |= seq[np.clip(idx + k, 0, n - 1)] != seq
    return bad


def sg_kinematics(x, y, seq, window=7, poly=2, fs=10.0):
    """Vectorised SG kinematics on concatenated sequences; frames within window//2 of a sequence
    edge are NaN. Returns dict(speed, a_t, a_n, curvature)."""
    dt = 1.0 / fs
    c1 = savgol_coeffs(window, poly, deriv=1, delta=dt, use="conv")
    c2 = savgol_coeffs(window, poly, deriv=2, delta=dt, use="conv")
    vx = convolve1d(x, c1, mode="nearest"); vy = convolve1d(y, c1, mode="nearest")
    ax = convolve1d(x, c2, mode="nearest"); ay = convolve1d(y, c2, mode="nearest")
    sp = np.hypot(vx, vy); safe = np.maximum(sp, 1e-6)
    at = (vx * ax + vy * ay) / safe
    an = np.abs(vx * ay - vy * ax) / safe
    bad = _edge_mask(seq, window // 2)
    out = dict(speed=sp, a_t=at, a_n=an, curvature=an / np.maximum(sp, 0.5) ** 2)
    for v in out.values():
        v[bad] = np.nan
    return out


def speed_derivatives(s, seq, fs=10.0, window=7, poly=2):
    """Central difference and SG derivative of the provided speed."""
    dt = 1.0 / fs
    d = np.full(len(s), np.nan)
    d[1:-1] = (s[2:] - s[:-2]) / (2 * dt)
    d[_edge_mask(seq, 1)] = np.nan
    c1 = savgol_coeffs(window, poly, deriv=1, delta=dt, use="conv")
    g = convolve1d(s, c1, mode="nearest"); g[_edge_mask(seq, window // 2)] = np.nan
    return d, g


def heading_lateral(s, dir_deg, seq, fs=10.0):
    """Normal acceleration from the provided heading: s * |d dir/dt| (central difference, wrapped)."""
    dt = 1.0 / fs
    th = np.radians(dir_deg)
    dth = np.full(len(s), np.nan)
    diff = (th[2:] - th[:-2] + np.pi) % (2 * np.pi) - np.pi
    dth[1:-1] = diff / (2 * dt)
    dth[_edge_mask(seq, 1)] = np.nan
    return s * np.abs(dth)


def split_half_by_game(df: pl.DataFrame) -> pl.DataFrame:
    """Assign each (player, game) to half 0/1 by alternating the player's games in date order."""
    g = (df.select("nfl_id", "game_id").unique().sort("nfl_id", "game_id")
         .with_columns((pl.int_range(pl.len()).over("nfl_id") % 2).alias("half")))
    return df.join(g, on=["nfl_id", "game_id"])


def spearman_brown(r):
    r = np.asarray(r, float)
    return 2 * r / (1 + r)
