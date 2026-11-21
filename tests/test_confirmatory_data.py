import sys
from pathlib import Path

import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nfl_bdb.data import confirmatory_data as cd  # noqa: E402


def _pred():
    att = pl.DataFrame({"nfl_id": [1, 1, 2, 2, 3, 4], "attempt": [1, 2, 1, 2, 1, 1],
                        "vpeak": [10.0, 10.4, 9.0, 12.9, 9.5, 11.0], "r2": [0.99, 0.97, 0.99, 0.99, 0.90, 0.99]})
    cr = pl.DataFrame({"nfl_id": [1, 2, 3, 4], "combine_position": ["WR"] * 4, "draft_year": [2023] * 4,
                       "forty": [4.4, 4.6, 4.5, None]})
    return cd.predictor_table(att, cr)


def test_predictor_validity_rule_and_max():
    p = _pred().sort("nfl_id")
    assert p["x_peak"].to_list()[:2] == [10.4, 9.0]        # player 2: 12.9 yd/s attempt is a spike -> invalid
    assert p["x_peak"][2] is None and not p["valid_tracked_40"][2]   # R^2 0.90 -> no valid attempt
    assert p["n_valid_attempts"].to_list()[:2] == [2, 1]


def test_join_is_many_to_one_and_never_multiplies_rows():
    p = _pred()
    plays = pl.DataFrame({"game_id": [1, 1, 2], "play_id": [1, 2, 1], "nfl_id": [1, 1, 2]})
    j = cd.join_predictors(plays, p)
    assert j.height == plays.height and cd.key_duplicates(j) == 0
    with pytest.raises(Exception):
        cd.join_predictors(plays, pl.concat([p, p.filter(pl.col("nfl_id") == 1)]))   # duplicated predictor row
