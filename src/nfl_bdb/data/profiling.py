"""Structural profiling and kinematic-consistency checks used in Phase 1 (exploration).

These are *validation* utilities (does a column mean what we think it means?), not
research features.
"""
from __future__ import annotations

import numpy as np
import polars as pl


def profile(lf: pl.LazyFrame) -> tuple[int, pl.DataFrame]:
    """Per-column dtype, null count/percent and n_unique."""
    sch = lf.collect_schema()
    n = lf.select(pl.len()).collect().item()
    nulls = lf.select([pl.col(c).null_count() for c in sch]).collect().row(0)
    uniq = lf.select([pl.col(c).n_unique() for c in sch]).collect().row(0)
    df = pl.DataFrame({
        "column": list(sch.keys()), "dtype": [str(t) for t in sch.values()],
        "nulls": list(nulls), "null_pct": [round(100 * v / n, 2) for v in nulls], "n_unique": list(uniq),
    })
    return n, df


def key_report(lf: pl.LazyFrame, keys: list[str]) -> dict:
    n = lf.select(pl.len()).collect().item()
    u = lf.select(keys).unique().select(pl.len()).collect().item()
    return {"key": ", ".join(keys), "rows": n, "unique": u, "duplicates": n - u, "is_key": n == u}


def add_kinematics(df: pl.DataFrame, group: str | list[str], dt: float = 0.1) -> pl.DataFrame:
    """Finite-difference kinematics from x, y, s, dir (NGS convention: dir 0 = +y, clockwise).

    Adds: step (yd moved since previous frame), vx, vy (yd/s, from s & dir),
    a_tan (signed tangential accel = ds/dt, central difference), a_vec (|dv/dt|).
    """
    df = df.sort([*([group] if isinstance(group, str) else group), "time"])
    over = group
    df = df.with_columns(
        (pl.col("s") * pl.col("dir").radians().sin()).alias("vx"),
        (pl.col("s") * pl.col("dir").radians().cos()).alias("vy"),
        ((pl.col("x").diff() ** 2 + pl.col("y").diff() ** 2).sqrt()).over(over).alias("step"),
        (pl.col("x").diff().over(over)).alias("dx"),
        (pl.col("y").diff().over(over)).alias("dy"),
    )
    return df.with_columns(
        ((pl.col("s").shift(-1) - pl.col("s").shift(1)).over(over) / (2 * dt)).alias("a_tan"),
        ((((pl.col("vx").shift(-1) - pl.col("vx").shift(1)) ** 2
           + (pl.col("vy").shift(-1) - pl.col("vy").shift(1)) ** 2).sqrt()).over(over) / (2 * dt)).alias("a_vec"),
    )


def semantics_checks(k: pl.DataFrame, min_step: float = 0.05) -> pl.DataFrame:
    """Compare provided s/dis/dir/a against values derived from x, y (one row per check)."""
    d = k.drop_nulls(["dx", "a_tan", "a_vec"]).filter(pl.col("step") > min_step)
    dirv = d["dir"].to_numpy()
    ang_ngs = np.degrees(np.arctan2(d["dx"].to_numpy(), d["dy"].to_numpy())) % 360
    ang_math = np.degrees(np.arctan2(d["dy"].to_numpy(), d["dx"].to_numpy())) % 360
    circ = lambda a, b: float(np.median(np.abs((a - b + 180) % 360 - 180)))
    m = d.filter(pl.col("s") > 1)
    rows = [
        ("s vs 10*step (yd/s)", float(np.corrcoef(d["s"], d["step"] * 10)[0, 1]), float((d["s"] / (d["step"] * 10)).median())),
        ("dis vs step (yd)", float(np.corrcoef(d["dis"], d["step"])[0, 1]), float((d["dis"] / d["step"]).median())),
        ("a vs |vector accel|", float(np.corrcoef(m["a"], m["a_vec"])[0, 1]), float((m["a"] / m["a_vec"]).median())),
        ("a vs |ds/dt| (tangential)", float(np.corrcoef(m["a"], m["a_tan"].abs())[0, 1]), float((m["a"] / m["a_tan"].abs()).median())),
    ]
    out = pl.DataFrame(rows, schema=["check", "pearson_r", "median_ratio"], orient="row")
    return out.vstack(pl.DataFrame({"check": ["dir vs atan2(dx,dy) NGS [median |deg|]", "dir vs atan2(dy,dx) math [median |deg|]"],
                                    "pearson_r": [None, None], "median_ratio": [circ(dirv, ang_ngs), circ(dirv, ang_math)]},
                                   schema={"check": pl.Utf8, "pearson_r": pl.Float64, "median_ratio": pl.Float64}))
