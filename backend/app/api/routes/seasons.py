from fastapi import APIRouter
from sqlalchemy import distinct, select

from app.api.dependencies import DbSession
from app.db.models import Game
from app.schemas.api import SeasonListResponse

router = APIRouter(tags=["seasons"])


@router.get("/seasons", response_model=SeasonListResponse)
def list_seasons(session: DbSession) -> SeasonListResponse:
    seasons = list(
        session.scalars(select(distinct(Game.season)).order_by(Game.season.desc()))
    )
    return SeasonListResponse(
        seasons=seasons,
        default_season=seasons[0] if seasons else None,
    )

