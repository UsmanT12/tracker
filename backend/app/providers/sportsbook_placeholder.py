from app.providers.player_catalog import PlayerCatalogItem


class SportsbookPlayerCatalogProvider:
    """Future extension point; intentionally makes no external API calls."""

    def list_players(self, **_: object) -> tuple[list[PlayerCatalogItem], int]:
        raise NotImplementedError(
            "Sportsbook integration is outside the MVP; use DatabasePlayerCatalogProvider"
        )

