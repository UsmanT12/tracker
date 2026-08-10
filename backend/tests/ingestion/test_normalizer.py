from datetime import date

from app.ingestion.normalizer import (
    is_dnp,
    normalize_name,
    parse_game_date,
    parse_made_attempted,
    parse_minutes,
    safe_int,
)


def test_normalization_and_parsing() -> None:
    assert normalize_name("  A’ja   Wilson ") == "a ja wilson"
    assert parse_game_date("Tuesday, May 14, 2024") == date(2024, 5, 14)
    assert parse_minutes("34:30") == 2070
    assert parse_minutes("00:34:30") == 2070
    assert parse_made_attempted("10-18") == (10, 18)
    assert parse_made_attempted("3 / 7") == (3, 7)
    assert safe_int("—") == 0
    assert safe_int("+12") == 12


def test_dnp_detection() -> None:
    assert is_dnp({"MIN": "DNP - Coach's Decision"})[0] is True
    assert is_dnp({"MIN": "00:00"})[0] is True
    assert is_dnp({"MIN": "14:02"}) == (False, None)

