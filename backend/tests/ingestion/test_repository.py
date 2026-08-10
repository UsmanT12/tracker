from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.db.models import Game, Player, PlayerGameStat, Team
from app.db.repositories.ingestion import IngestionRepository
from app.ingestion.normalizer import normalize_name
from app.ingestion.parser import parse_box_score
from app.ingestion.schemas import IngestedTeam

FIXTURE = Path(__file__).parents[1] / "fixtures" / "completed_game.html"


def parsed_game():
    return parse_box_score(
        FIXTURE.read_text(),
        source_url="https://www.wnba.com/game/pho-vs-lva-20240514/boxscore",
        source_game_id="pho-vs-lva-20240514",
        season=2024,
    )


def test_import_is_idempotent_and_updates(session_factory) -> None:
    with session_factory.begin() as session:
        assert IngestionRepository(session).import_game(parsed_game()) == 3
    changed = parsed_game()
    changed.player_stats[0].pts = 22
    with session_factory.begin() as session:
        IngestionRepository(session).import_game(changed)

    with session_factory() as session:
        assert session.scalar(select(func.count(Game.id))) == 1
        assert session.scalar(select(func.count(Player.id))) == 3
        assert session.scalar(select(func.count(PlayerGameStat.id))) == 3
        copper = session.scalar(select(Player).where(Player.display_name == "Kahleah Copper"))
        stat = session.scalar(
            select(PlayerGameStat).where(PlayerGameStat.player_id == copper.id)
        )
        assert stat.pts == 22


def test_failed_game_transaction_writes_nothing(session_factory) -> None:
    invalid = parsed_game()
    invalid.source_game_id = "invalid-team-game"
    invalid.player_stats[0].team_name = "Unknown Team"

    with pytest.raises(ValueError), session_factory.begin() as session:
        IngestionRepository(session).import_game(invalid)

    with session_factory() as session:
        assert session.scalar(select(func.count(Game.id))) == 0
        assert session.scalar(select(func.count(PlayerGameStat.id))) == 0


def test_player_can_change_teams_without_changing_identity(session_factory) -> None:
    first = parsed_game()
    first.player_stats = [
        row for row in first.player_stats if row.display_name == "A'ja Wilson"
    ]
    second = first.model_copy(deep=True)
    second.source_game_id = "new-team-game"
    second.game_date += timedelta(days=7)
    second.home_team = IngestedTeam(name="New York Liberty")
    second.away_team = IngestedTeam(name="Phoenix Mercury")
    second.player_stats[0].team_name = "Phoenix Mercury"
    second.player_stats[0].opponent_name = "New York Liberty"
    second.player_stats[0].is_home = False

    with session_factory.begin() as session:
        IngestionRepository(session).import_game(first)
        IngestionRepository(session).import_game(second)

    with session_factory() as session:
        assert session.scalar(select(func.count(Player.id))) == 1
        assert session.scalar(select(func.count(PlayerGameStat.id))) == 2
        team_names = set(
            session.scalars(
                select(Team.name)
                .join(PlayerGameStat, PlayerGameStat.team_id == Team.id)
                .order_by(Team.name)
            )
        )
        assert team_names == {"Las Vegas Aces", "Phoenix Mercury"}


def test_source_player_match_refreshes_display_and_normalized_name(session_factory) -> None:
    malformed = parsed_game()
    malformed.player_stats = [malformed.player_stats[0]]
    malformed.player_stats[0].display_name = "Kahleah Copper K. Copper G"
    corrected = malformed.model_copy(deep=True)
    corrected.player_stats[0].display_name = "Kahleah Copper"

    with session_factory.begin() as session:
        IngestionRepository(session).import_game(malformed)
    with session_factory.begin() as session:
        IngestionRepository(session).import_game(corrected)

    with session_factory() as session:
        source_player_id = corrected.player_stats[0].source_player_id
        player = session.scalar(
            select(Player).where(Player.source_player_id == source_player_id)
        )
        assert player.display_name == "Kahleah Copper"
        assert player.normalized_name == normalize_name("Kahleah Copper")
