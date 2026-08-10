from typing import Protocol

from app.ingestion.schemas import DiscoveredGame, IngestedGame


class WnbaSource(Protocol):
    def discover_games(
        self,
        season: int,
        *,
        completed_only: bool = False,
    ) -> list[DiscoveredGame]:
        ...

    def fetch_game(self, game: DiscoveredGame, season: int) -> IngestedGame:
        ...

    def close(self) -> None:
        ...
