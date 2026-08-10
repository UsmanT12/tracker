import pytest

from app.ingestion.sources.selenium_wnba import (
    box_score_url,
    schedule_status_is_final,
    schedule_url,
    source_game_id,
)


def test_schedule_and_box_score_urls() -> None:
    assert schedule_url(2025) == "https://www.wnba.com/schedule?season=2025&month=all"
    assert (
        box_score_url("https://www.wnba.com/game/1022400016/SEA-vs-NYL")
        == "https://www.wnba.com/game/1022400016/SEA-vs-NYL/box-score"
    )
    assert (
        box_score_url("https://www.wnba.com/game/1022400016/SEA-vs-NYL/boxscore")
        == "https://www.wnba.com/game/1022400016/SEA-vs-NYL/box-score"
    )
    assert (
        box_score_url("https://www.wnba.com/game/1022400016/SEA-vs-NYL/box-score")
        == "https://www.wnba.com/game/1022400016/SEA-vs-NYL/box-score"
    )


def test_source_game_id() -> None:
    assert source_game_id("https://www.wnba.com/game/1022400016/SEA-vs-NYL/boxscore") == (
        "1022400016"
    )
    with pytest.raises(ValueError):
        source_game_id("https://www.wnba.com/")


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("FINAL", True),
        ("Regular Season\nFINAL\nIndiana Fever", True),
        ("FINAL/OT", True),
        ("FINAL/2OT", True),
        ("7:00 PM PDT", False),
        ("LIVE", False),
        ("WNBA FINALS", False),
        ("POSTPONED", False),
    ],
)
def test_schedule_status_is_final(status: str, expected: bool) -> None:
    assert schedule_status_is_final(status) is expected
