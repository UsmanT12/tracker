import statistics
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.services.stat_definitions import StatDefinition


@dataclass(frozen=True)
class PerformanceInput:
    game_id: str
    date: date
    team: str
    opponent: str
    is_home: bool | None
    played: bool
    minutes_seconds: int
    result: str | None
    stats: Any


def _value(game: PerformanceInput, definition: StatDefinition) -> float | None:
    if not game.played:
        return None
    if definition.unit == "percentage":
        numerator = getattr(game.stats, str(definition.numerator))
        denominator = getattr(game.stats, str(definition.denominator))
        return numerator / denominator * 100 if denominator else None
    raw = getattr(game.stats, str(definition.field))
    if raw is None:
        return None
    return raw / 60 if definition.unit == "minutes" else float(raw)


def _average(
    games: list[PerformanceInput], definition: StatDefinition, values: list[float]
) -> float | None:
    if not values:
        return None
    if definition.unit == "percentage":
        numerator = sum(
            getattr(game.stats, str(definition.numerator)) for game in games if game.played
        )
        denominator = sum(
            getattr(game.stats, str(definition.denominator)) for game in games if game.played
        )
        return numerator / denominator * 100 if denominator else None
    return statistics.fmean(values)


def _raw_bucket(delta: float, z_score: float | None, sample_count: int) -> str:
    if z_score is None or sample_count < 5:
        if abs(delta) < 1e-9:
            return "near_average"
        return "above" if delta > 0 else "below"
    if z_score <= -1:
        return "strong_below"
    if z_score < -0.25:
        return "below"
    if z_score < 0.25:
        return "near_average"
    if z_score < 1:
        return "above"
    return "strong_above"


def _semantic_bucket(bucket: str, definition: StatDefinition) -> str:
    if definition.comparison_direction != "lower_better":
        return bucket
    return {
        "strong_below": "strong_above",
        "below": "above",
        "near_average": "near_average",
        "above": "below",
        "strong_above": "strong_below",
    }[bucket]


def _label(delta: float, precision: int, near_average: bool) -> str:
    if near_average:
        return "near average"
    direction = "above" if delta > 0 else "below"
    return f"{abs(delta):.{precision}f} {direction} average"


def calculate_performance(
    games: list[PerformanceInput], definition: StatDefinition
) -> dict[str, Any]:
    game_values = [_value(game, definition) for game in games]
    valid_values = [value for value in game_values if value is not None]
    average = _average(games, definition, valid_values)
    standard_deviation = (
        statistics.pstdev(valid_values) if len(valid_values) >= 2 else 0.0
    )

    game_results: list[dict[str, Any]] = []
    for game, value in zip(games, game_values, strict=True):
        if not game.played:
            game_results.append(
                {
                    "game_id": game.game_id,
                    "date": game.date,
                    "team": game.team,
                    "opponent": game.opponent,
                    "is_home": game.is_home,
                    "played": False,
                    "minutes": 0.0,
                    "result": game.result,
                    "value": None,
                    "average": average,
                    "delta": None,
                    "z_score": None,
                    "comparison_bucket": "dnp",
                    "comparison_label": "DNP",
                }
            )
            continue

        delta = value - average if value is not None and average is not None else None
        z_score = (
            delta / standard_deviation
            if delta is not None and standard_deviation > 0 and len(valid_values) >= 5
            else None
        )
        raw_bucket = (
            _raw_bucket(delta, z_score, len(valid_values))
            if delta is not None
            else "near_average"
        )
        game_results.append(
            {
                "game_id": game.game_id,
                "date": game.date,
                "team": game.team,
                "opponent": game.opponent,
                "is_home": game.is_home,
                "played": True,
                "minutes": game.minutes_seconds / 60,
                "result": game.result,
                "value": value,
                "average": average,
                "delta": delta,
                "z_score": max(-2.0, min(2.0, z_score)) if z_score is not None else None,
                "comparison_bucket": (
                    _semantic_bucket(raw_bucket, definition) if delta is not None else "unavailable"
                ),
                "comparison_label": (
                    _label(delta, definition.precision, raw_bucket == "near_average")
                    if delta is not None
                    else "metric unavailable"
                ),
            }
        )

    total = sum(valid_values) if definition.unit != "percentage" and valid_values else None
    return {
        "summary": {
            "games_played": sum(game.played for game in games),
            "valid_samples": len(valid_values),
            "average": average,
            "standard_deviation": standard_deviation if valid_values else None,
            "total": total,
            "high": max(valid_values) if valid_values else None,
            "low": min(valid_values) if valid_values else None,
        },
        "games": game_results,
    }

