"""I/O helpers: locate raw competition files and cache them as Parquet in data/interim/.

Raw CSVs are never modified. Parquet copies are a lossless, typed cache only.
"""
from __future__ import annotations

from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "raw" / "nfl-big-data-bowl-2027"
INTERIM = ROOT / "data" / "interim"

FILES = [
    "combine_results", "combine_tracking", "game_tracking_2023", "game_tracking_2024",
    "game_tracking_2025", "games", "player_career_successes", "player_play", "players",
]

# Explicit dtypes for the large files (avoid inference errors / int overflow).
_TRACKING_SCHEMA = {
    "game_id": pl.Int64, "play_id": pl.Int64, "nfl_id": pl.Int64, "time": pl.Utf8,
    "x": pl.Float64, "y": pl.Float64, "s": pl.Float64, "a": pl.Float64, "dis": pl.Float64,
    "o": pl.Float64, "dir": pl.Float64, "event": pl.Utf8,
}
_COMBINE_TRACKING_SCHEMA = {
    "draft_year": pl.Int64, "event_id": pl.Utf8, "nfl_id": pl.Int64, "entity_type": pl.Utf8,
    "time": pl.Utf8, "drill_type": pl.Utf8, "drill_name": pl.Utf8, "attempt": pl.Int64,
    "x": pl.Float64, "y": pl.Float64, "s": pl.Float64, "a": pl.Float64, "dis": pl.Float64,
    "dir": pl.Float64,
}


def raw_path(name: str) -> Path:
    return RAW / f"{name}.csv"


def scan_raw(name: str) -> pl.LazyFrame:
    kw: dict = dict(null_values=["NA"], infer_schema_length=100_000)
    if name.startswith("game_tracking"):
        kw["schema_overrides"] = _TRACKING_SCHEMA
    elif name == "combine_tracking":
        kw["schema_overrides"] = _COMBINE_TRACKING_SCHEMA
    return pl.scan_csv(raw_path(name), **kw)


def parquet_path(name: str) -> Path:
    return INTERIM / f"{name}.parquet"


def build_parquet_cache(overwrite: bool = False) -> None:
    INTERIM.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        out = parquet_path(name)
        if out.exists() and not overwrite:
            continue
        lf = scan_raw(name)
        if "time" in lf.collect_schema().names():
            lf = lf.with_columns(pl.col("time").str.to_datetime("%Y-%m-%dT%H:%M:%S%.f", strict=True))
        lf.sink_parquet(out, compression="zstd")


def load(name: str, lazy: bool = True) -> pl.LazyFrame | pl.DataFrame:
    """Load from Parquet cache (built on demand)."""
    if not parquet_path(name).exists():
        build_parquet_cache()
    lf = pl.scan_parquet(parquet_path(name))
    return lf if lazy else lf.collect()
