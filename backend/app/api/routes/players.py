import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import DbSession
from app.providers.database_catalog import DatabasePlayerCatalogProvider
from app.schemas.api import PerformanceResponse, PlayerListItem, PlayerListResponse
from app.services.player_service import (
    PlayerNotFoundError,
    PlayerSeasonNotFoundError,
    PlayerService,
)

router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=PlayerListResponse)
def list_players(
    session: DbSession,
    season: int | None = None,
    search: str | None = Query(default=None, max_length=100),
    team: str | None = Query(default=None, max_length=50),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
) -> PlayerListResponse:
    provider = DatabasePlayerCatalogProvider(session)
    items, total = provider.list_players(
        season=season,
        search=search,
        team=team,
        offset=(page - 1) * page_size,
        limit=page_size,
    )
    return PlayerListResponse(
        items=[PlayerListItem(**item.__dict__) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{player_id}")
def get_player(
    player_id: uuid.UUID,
    session: DbSession,
    season: int,
) -> PlayerListItem:
    provider = DatabasePlayerCatalogProvider(session)
    items, _ = provider.list_players(
        season=season,
        search=None,
        team=None,
        offset=0,
        limit=10000,
    )
    item = next((candidate for candidate in items if candidate.id == player_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Player not found for the selected season")
    return PlayerListItem(**item.__dict__)


@router.get("/{player_id}/performance", response_model=PerformanceResponse)
def player_performance(
    player_id: uuid.UUID,
    session: DbSession,
    season: int,
    stat: str = "pts",
) -> PerformanceResponse:
    try:
        result = PlayerService(session).performance(player_id, season, stat)
        return PerformanceResponse.model_validate(result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PlayerNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Player not found") from exc
    except PlayerSeasonNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

