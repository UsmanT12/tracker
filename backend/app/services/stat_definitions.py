from dataclasses import dataclass
from typing import Literal

ComparisonDirection = Literal["higher_better", "lower_better", "neutral"]


@dataclass(frozen=True)
class StatDefinition:
    key: str
    label: str
    short_label: str
    unit: Literal["count", "minutes", "percentage"]
    precision: int
    comparison_direction: ComparisonDirection
    field: str | None = None
    numerator: str | None = None
    denominator: str | None = None


STAT_DEFINITIONS = {
    item.key: item
    for item in (
        StatDefinition("pts", "Points", "PTS", "count", 1, "higher_better", field="pts"),
        StatDefinition("reb", "Rebounds", "REB", "count", 1, "higher_better", field="reb"),
        StatDefinition("ast", "Assists", "AST", "count", 1, "higher_better", field="ast"),
        StatDefinition(
            "fg3m", "Three-pointers made", "3PM", "count", 1, "higher_better", field="fg3m"
        ),
        StatDefinition("stl", "Steals", "STL", "count", 1, "higher_better", field="stl"),
        StatDefinition("blk", "Blocks", "BLK", "count", 1, "higher_better", field="blk"),
        StatDefinition("tov", "Turnovers", "TOV", "count", 1, "lower_better", field="tov"),
        StatDefinition(
            "minutes", "Minutes", "MIN", "minutes", 1, "neutral", field="minutes_seconds"
        ),
        StatDefinition(
            "fg_pct",
            "Field-goal percentage",
            "FG%",
            "percentage",
            1,
            "higher_better",
            numerator="fgm",
            denominator="fga",
        ),
        StatDefinition(
            "fg3_pct",
            "Three-point percentage",
            "3P%",
            "percentage",
            1,
            "higher_better",
            numerator="fg3m",
            denominator="fg3a",
        ),
        StatDefinition(
            "ft_pct",
            "Free-throw percentage",
            "FT%",
            "percentage",
            1,
            "higher_better",
            numerator="ftm",
            denominator="fta",
        ),
        StatDefinition(
            "plus_minus",
            "Plus/minus",
            "+/-",
            "count",
            1,
            "higher_better",
            field="plus_minus",
        ),
        StatDefinition("fga", "Field-goal attempts", "FGA", "count", 1, "neutral", field="fga"),
        StatDefinition(
            "fg3a", "Three-point attempts", "3PA", "count", 1, "neutral", field="fg3a"
        ),
        StatDefinition("fta", "Free-throw attempts", "FTA", "count", 1, "neutral", field="fta"),
    )
}


def get_stat_definition(key: str) -> StatDefinition:
    try:
        return STAT_DEFINITIONS[key]
    except KeyError as exc:
        valid = ", ".join(STAT_DEFINITIONS)
        raise ValueError(f"invalid stat {key!r}; choose one of: {valid}") from exc

