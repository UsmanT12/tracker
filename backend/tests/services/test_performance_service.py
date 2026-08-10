from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from app.services.performance_service import PerformanceInput, calculate_performance
from app.services.stat_definitions import get_stat_definition


def game(index: int, *, played: bool = True, **stats: int) -> PerformanceInput:
    defaults = {
        "pts": 0,
        "tov": 0,
        "fgm": 0,
        "fga": 0,
        "fg3m": 0,
        "fg3a": 0,
        "ftm": 0,
        "fta": 0,
    }
    defaults.update(stats)
    return PerformanceInput(
        game_id=str(index),
        date=date(2024, 5, 1) + timedelta(days=index),
        team="LVA",
        opponent="PHO",
        is_home=True,
        played=played,
        minutes_seconds=1800 if played else 0,
        result=None,
        stats=SimpleNamespace(**defaults),
    )


def test_counting_average_deltas_and_dnp() -> None:
    result = calculate_performance(
        [game(1, pts=10), game(2, pts=20), game(3, played=False)],
        get_stat_definition("pts"),
    )
    assert result["summary"]["games_played"] == 2
    assert result["summary"]["average"] == 15
    assert result["games"][0]["delta"] == -5
    assert result["games"][2]["comparison_bucket"] == "dnp"


def test_weighted_percentage_and_zero_attempts() -> None:
    result = calculate_performance(
        [game(1, fgm=1, fga=2), game(2, fgm=9, fga=18), game(3, fgm=0, fga=0)],
        get_stat_definition("fg_pct"),
    )
    assert result["summary"]["average"] == pytest.approx(50)
    assert result["summary"]["valid_samples"] == 2
    assert result["games"][2]["value"] is None
    assert result["games"][2]["comparison_bucket"] == "unavailable"


def test_lower_is_better_inverts_semantic_bucket() -> None:
    result = calculate_performance(
        [game(index, tov=value) for index, value in enumerate([1, 2, 2, 3, 7], start=1)],
        get_stat_definition("tov"),
    )
    assert result["games"][-1]["delta"] > 0
    assert result["games"][-1]["comparison_bucket"] == "strong_below"
    assert "above average" in result["games"][-1]["comparison_label"]

