import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Team(TimestampMixin, Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_team_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    abbreviation: Mapped[str | None] = mapped_column(String(10))
    normalized_name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)


class Player(TimestampMixin, Base):
    __tablename__ = "players"
    __table_args__ = (Index("ix_players_normalized_name", "normalized_name"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_player_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(150), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Game(TimestampMixin, Base):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_game_id: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    season: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    season_type: Mapped[str] = mapped_column(String(30), default="regular", nullable=False)
    game_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="completed", nullable=False)
    home_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    home_score: Mapped[int | None] = mapped_column(Integer)
    away_score: Mapped[int | None] = mapped_column(Integer)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    home_team: Mapped[Team] = relationship(foreign_keys=[home_team_id])
    away_team: Mapped[Team] = relationship(foreign_keys=[away_team_id])


class PlayerGameStat(TimestampMixin, Base):
    __tablename__ = "player_game_stats"
    __table_args__ = (
        UniqueConstraint("game_id", "player_id", name="uq_player_game_stats_game_player"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("games.id"), index=True, nullable=False)
    player_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("players.id"), index=True, nullable=False
    )
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    opponent_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    is_home: Mapped[bool | None] = mapped_column(Boolean)
    started: Mapped[bool | None] = mapped_column(Boolean)
    played: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    dnp_reason: Mapped[str | None] = mapped_column(String(150))
    minutes_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fgm: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fga: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fg3m: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fg3a: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ftm: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fta: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    oreb: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dreb: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reb: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ast: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pf: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stl: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tov: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    blk: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    plus_minus: Mapped[int | None] = mapped_column(Integer)

    game: Mapped[Game] = relationship()
    player: Mapped[Player] = relationship()
    team: Mapped[Team] = relationship(foreign_keys=[team_id])
    opponent_team: Mapped[Team] = relationship(foreign_keys=[opponent_team_id])


class ScraperRun(Base):
    __tablename__ = "scraper_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="running", nullable=False)
    games_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    games_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    games_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    games_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    player_stat_rows_upserted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text)
    run_metadata: Mapped[dict | None] = mapped_column("metadata", JSON)


class ScraperGameResult(TimestampMixin, Base):
    __tablename__ = "scraper_game_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    scraper_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scraper_runs.id"), index=True, nullable=False
    )
    source_game_id: Mapped[str] = mapped_column(String(150), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    rows_upserted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)


class ExternalPlayerMapping(TimestampMixin, Base):
    __tablename__ = "external_player_mappings"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "external_player_id",
            name="uq_external_player_mapping_provider_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("players.id"), index=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    external_player_id: Mapped[str] = mapped_column(String(150), nullable=False)
    external_display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    provider_metadata: Mapped[dict | None] = mapped_column("metadata", JSON)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    player: Mapped[Player] = relationship()

