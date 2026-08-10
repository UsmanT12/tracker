from fastapi import APIRouter
from sqlalchemy import select

from app.api.dependencies import DbSession
from app.db.models import Team

router = APIRouter(tags=["teams"])


@router.get("/teams")
def list_teams(session: DbSession) -> list[dict[str, str | None]]:
    teams = session.scalars(select(Team).order_by(Team.name)).all()
    return [
        {"id": str(team.id), "name": team.name, "abbreviation": team.abbreviation}
        for team in teams
    ]

