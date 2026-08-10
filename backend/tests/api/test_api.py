import uuid
from pathlib import Path

from sqlalchemy import select

from app.db.models import Player
from app.db.repositories.ingestion import IngestionRepository
from app.ingestion.parser import parse_box_score

FIXTURE = Path(__file__).parents[1] / "fixtures" / "completed_game.html"


def seed(session_factory) -> uuid.UUID:
    parsed = parse_box_score(
        FIXTURE.read_text(),
        source_url="https://www.wnba.com/game/pho-vs-lva-20240514/boxscore",
        source_game_id="pho-vs-lva-20240514",
        season=2024,
    )
    with session_factory.begin() as session:
        IngestionRepository(session).import_game(parsed)
    with session_factory() as session:
        return session.scalar(
            select(Player.id).where(Player.display_name == "A'ja Wilson")
        )


def test_catalog_seasons_and_performance(client, session_factory) -> None:
    player_id = seed(session_factory)

    seasons = client.get("/api/v1/seasons")
    assert seasons.status_code == 200
    assert seasons.json() == {"seasons": [2024], "default_season": 2024}

    catalog = client.get("/api/v1/players", params={"season": 2024, "search": "wilson"})
    assert catalog.status_code == 200
    assert catalog.json()["total"] == 1

    response = client.get(
        f"/api/v1/players/{player_id}/performance",
        params={"season": 2024, "stat": "pts"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["average"] == 25
    assert payload["games"][0]["comparison_label"] == "near average"


def test_invalid_stat_and_unknown_player(client, session_factory) -> None:
    player_id = seed(session_factory)
    invalid = client.get(
        f"/api/v1/players/{player_id}/performance",
        params={"season": 2024, "stat": "made_up"},
    )
    assert invalid.status_code == 422

    missing = client.get(
        f"/api/v1/players/{uuid.uuid4()}/performance",
        params={"season": 2024, "stat": "pts"},
    )
    assert missing.status_code == 404

