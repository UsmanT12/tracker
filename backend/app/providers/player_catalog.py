import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PlayerCatalogItem:
    id: uuid.UUID
    display_name: str
    team_name: str | None
    team_abbreviation: str | None
    games_played: int
    ppg: float | None = None
    rpg: float | None = None
    apg: float | None = None


class PlayerCatalogProvider(Protocol):
    def list_players(
        self,
        *,
        season: int | None,
        search: str | None,
        team: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[PlayerCatalogItem], int]:
        ...

