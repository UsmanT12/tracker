from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.dependencies import DbSession
from app.db.models import Game, Player, PlayerGameStat, ScraperRun
from app.schemas.api import DataStatusResponse

router = APIRouter(tags=["status"])


@router.get("/data-status", response_model=DataStatusResponse)
def data_status(session: DbSession) -> DataStatusResponse:
    latest_run = session.scalar(
        select(ScraperRun)
        .where(ScraperRun.status == "completed")
        .order_by(ScraperRun.completed_at.desc())
        .limit(1)
    )
    return DataStatusResponse(
        latest_successful_run_at=latest_run.completed_at if latest_run else None,
        latest_game_date=session.scalar(select(func.max(Game.game_date))),
        players=session.scalar(select(func.count(Player.id))) or 0,
        games=session.scalar(select(func.count(Game.id))) or 0,
        player_stat_rows=session.scalar(select(func.count(PlayerGameStat.id))) or 0,
    )

