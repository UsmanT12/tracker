import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.db.models import Game, Player, PlayerGameStat, Team
from app.services.performance_service import PerformanceInput, calculate_performance
from app.services.stat_definitions import get_stat_definition


class PlayerNotFoundError(LookupError):
    pass


class PlayerSeasonNotFoundError(LookupError):
    pass


class PlayerService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def performance(self, player_id: uuid.UUID, season: int, stat_key: str) -> dict:
        definition = get_stat_definition(stat_key)
        player = self.session.get(Player, player_id)
        if player is None:
            raise PlayerNotFoundError(str(player_id))

        team = aliased(Team)
        opponent = aliased(Team)
        rows = self.session.execute(
            select(PlayerGameStat, Game, team, opponent)
            .join(Game, Game.id == PlayerGameStat.game_id)
            .join(team, team.id == PlayerGameStat.team_id)
            .join(opponent, opponent.id == PlayerGameStat.opponent_team_id)
            .where(PlayerGameStat.player_id == player_id, Game.season == season)
            .order_by(Game.game_date)
        ).all()
        if not rows:
            raise PlayerSeasonNotFoundError(f"{player.display_name} has no games in {season}")

        inputs: list[PerformanceInput] = []
        for stats, game, player_team, opponent_team in rows:
            result = None
            if game.home_score is not None and game.away_score is not None:
                team_score = game.home_score if stats.is_home else game.away_score
                opponent_score = game.away_score if stats.is_home else game.home_score
                outcome = "W" if team_score > opponent_score else "L"
                result = f"{outcome} {team_score}-{opponent_score}"
            inputs.append(
                PerformanceInput(
                    game_id=str(game.id),
                    date=game.game_date,
                    team=player_team.abbreviation or player_team.name,
                    opponent=opponent_team.abbreviation or opponent_team.name,
                    is_home=stats.is_home,
                    played=stats.played,
                    minutes_seconds=stats.minutes_seconds,
                    result=result,
                    stats=stats,
                )
            )

        calculated = calculate_performance(inputs, definition)
        latest_team = rows[-1][2]
        return {
            "player": {
                "id": player.id,
                "display_name": player.display_name,
                "team": {
                    "id": latest_team.id,
                    "name": latest_team.name,
                    "abbreviation": latest_team.abbreviation,
                },
            },
            "season": season,
            "stat": definition,
            **calculated,
        }
