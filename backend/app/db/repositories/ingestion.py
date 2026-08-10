from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Game, Player, PlayerGameStat, Team
from app.ingestion.normalizer import normalize_name
from app.ingestion.schemas import IngestedGame, IngestedPlayerStat, IngestedTeam


class IngestionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def game_exists(self, source_game_id: str) -> bool:
        return (
            self.session.scalar(select(Game.id).where(Game.source_game_id == source_game_id))
            is not None
        )

    def _upsert_team(self, data: IngestedTeam) -> Team:
        normalized = normalize_name(data.name)
        team = self.session.scalar(select(Team).where(Team.normalized_name == normalized))
        if team is None:
            team = Team(
                name=data.name,
                normalized_name=normalized,
                abbreviation=data.abbreviation,
                source_team_id=data.source_team_id,
            )
            self.session.add(team)
        else:
            team.name = data.name
            team.abbreviation = data.abbreviation or team.abbreviation
            team.source_team_id = data.source_team_id or team.source_team_id
        self.session.flush()
        return team

    def _upsert_player(self, data: IngestedPlayerStat) -> Player:
        player = None
        if data.source_player_id:
            player = self.session.scalar(
                select(Player).where(Player.source_player_id == data.source_player_id)
            )
        normalized = normalize_name(data.display_name)
        if player is None:
            player = self.session.scalar(
                select(Player).where(Player.normalized_name == normalized)
            )
        if player is None:
            player = Player(
                display_name=data.display_name,
                normalized_name=normalized,
                source_player_id=data.source_player_id,
            )
            self.session.add(player)
        else:
            player.display_name = data.display_name
            player.normalized_name = normalized
            player.source_player_id = data.source_player_id or player.source_player_id
            player.active = True
        self.session.flush()
        return player

    def import_game(self, data: IngestedGame) -> int:
        home_team = self._upsert_team(data.home_team)
        away_team = self._upsert_team(data.away_team)
        teams = {
            normalize_name(home_team.name): home_team,
            normalize_name(away_team.name): away_team,
        }

        game = self.session.scalar(
            select(Game).where(Game.source_game_id == data.source_game_id)
        )
        if game is None:
            game = Game(source_game_id=data.source_game_id)
            self.session.add(game)
        game.season = data.season
        game.season_type = data.season_type
        game.game_date = data.game_date
        game.status = data.status
        game.home_team_id = home_team.id
        game.away_team_id = away_team.id
        game.home_score = data.home_score
        game.away_score = data.away_score
        game.source_url = data.source_url
        self.session.flush()

        for row in data.player_stats:
            player = self._upsert_player(row)
            team = teams.get(normalize_name(row.team_name))
            opponent = teams.get(normalize_name(row.opponent_name))
            if team is None or opponent is None:
                raise ValueError(
                    f"player team mapping failed for {row.display_name}: "
                    f"{row.team_name} vs {row.opponent_name}"
                )
            stat = self.session.scalar(
                select(PlayerGameStat).where(
                    PlayerGameStat.game_id == game.id,
                    PlayerGameStat.player_id == player.id,
                )
            )
            if stat is None:
                stat = PlayerGameStat(game_id=game.id, player_id=player.id)
                self.session.add(stat)
            stat.team_id = team.id
            stat.opponent_team_id = opponent.id
            for field in (
                "is_home",
                "started",
                "played",
                "dnp_reason",
                "minutes_seconds",
                "fgm",
                "fga",
                "fg3m",
                "fg3a",
                "ftm",
                "fta",
                "oreb",
                "dreb",
                "reb",
                "ast",
                "pf",
                "stl",
                "tov",
                "blk",
                "pts",
                "plus_minus",
            ):
                setattr(stat, field, getattr(row, field))
        self.session.flush()
        return len(data.player_stats)
