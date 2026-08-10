from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import data_status, health, players, seasons, teams
from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
settings = get_settings()

app = FastAPI(
    title="WNBA Stats Tracker API",
    version="1.0.0",
    description="Performance-versus-average WNBA statistics API.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

for router in (health.router, data_status.router, seasons.router, players.router, teams.router):
    app.include_router(router, prefix="/api/v1")


@app.exception_handler(SQLAlchemyError)
def database_error(_: Request, __: SQLAlchemyError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": "Statistics database is currently unavailable"},
    )

