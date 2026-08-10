from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Game, Player, PlayerGameStat, Team
from app.ingestion.normalizer import normalize_name
from app.providers.player_catalog import PlayerCatalogItem


class DatabasePlayerCatalogProvider:
    def __init__(self, session: Session) -> None:
        self.session = session

    def newest_season(self) -> int | None:
        return self.session.scalar(select(func.max(Game.season)))

    def list_players(
        self,
        *,
        season: int | None,
        search: str | None,
        team: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[PlayerCatalogItem], int]:
        selected_season = season or self.newest_season()
        filters = []
        if search:
            filters.append(Player.normalized_name.contains(normalize_name(search)))

        base_ids = (
            select(Player.id)
            .join(PlayerGameStat, PlayerGameStat.player_id == Player.id)
            .join(Game, Game.id == PlayerGameStat.game_id)
            .join(Team, Team.id == PlayerGameStat.team_id)
            .where(*filters)
            .group_by(Player.id)
        )
        if selected_season is not None:
            base_ids = base_ids.where(Game.season == selected_season)
        if team:
            base_ids = base_ids.where(
                (Team.abbreviation.ilike(team))
                | (Team.normalized_name.contains(normalize_name(team)))
            )

        total = self.session.scalar(select(func.count()).select_from(base_ids.subquery())) or 0
        ids = list(
            self.session.scalars(
                base_ids.order_by(Player.display_name).offset(offset).limit(limit)
            )
        )

        items: list[PlayerCatalogItem] = []
        for player_id in ids:
            player = self.session.get(Player, player_id)
            aggregate = (
                select(
                    func.count().filter(PlayerGameStat.played.is_(True)),
                    func.avg(PlayerGameStat.pts).filter(PlayerGameStat.played.is_(True)),
                    func.avg(PlayerGameStat.reb).filter(PlayerGameStat.played.is_(True)),
                    func.avg(PlayerGameStat.ast).filter(PlayerGameStat.played.is_(True)),
                )
                .join(Game, Game.id == PlayerGameStat.game_id)
                .where(PlayerGameStat.player_id == player_id)
            )
            if selected_season is not None:
                aggregate = aggregate.where(Game.season == selected_season)
            games_played, ppg, rpg, apg = self.session.execute(aggregate).one()

            latest_team_query = (
                select(Team)
                .join(PlayerGameStat, PlayerGameStat.team_id == Team.id)
                .join(Game, Game.id == PlayerGameStat.game_id)
                .where(PlayerGameStat.player_id == player_id)
                .order_by(Game.game_date.desc())
                .limit(1)
            )
            if selected_season is not None:
                latest_team_query = latest_team_query.where(Game.season == selected_season)
            latest_team = self.session.scalar(latest_team_query)
            items.append(
                PlayerCatalogItem(
                    id=player.id,
                    display_name=player.display_name,
                    team_name=latest_team.name if latest_team else None,
                    team_abbreviation=latest_team.abbreviation if latest_team else None,
                    games_played=games_played or 0,
                    ppg=float(ppg) if ppg is not None else None,
                    rpg=float(rpg) if rpg is not None else None,
                    apg=float(apg) if apg is not None else None,
                )
            )
        return items, total
