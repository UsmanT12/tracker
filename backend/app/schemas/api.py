import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class TeamSummary(BaseModel):
    id: uuid.UUID
    name: str
    abbreviation: str | None


class PlayerIdentity(BaseModel):
    id: uuid.UUID
    display_name: str
    team: TeamSummary


class StatMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    label: str
    short_label: str
    unit: str
    precision: int
    comparison_direction: str


class PerformanceSummary(BaseModel):
    games_played: int
    valid_samples: int
    average: float | None
    standard_deviation: float | None
    total: float | None
    high: float | None
    low: float | None


class PerformanceGame(BaseModel):
    game_id: str
    date: date
    team: str
    opponent: str
    is_home: bool | None
    played: bool
    minutes: float
    result: str | None
    value: float | None
    average: float | None
    delta: float | None
    z_score: float | None
    comparison_bucket: str
    comparison_label: str


class PerformanceResponse(BaseModel):
    player: PlayerIdentity
    season: int
    stat: StatMetadata
    summary: PerformanceSummary
    games: list[PerformanceGame]


class PlayerListItem(BaseModel):
    id: uuid.UUID
    display_name: str
    team_name: str | None
    team_abbreviation: str | None
    games_played: int
    ppg: float | None
    rpg: float | None
    apg: float | None


class PlayerListResponse(BaseModel):
    items: list[PlayerListItem]
    page: int
    page_size: int
    total: int


class SeasonListResponse(BaseModel):
    seasons: list[int]
    default_season: int | None


class DataStatusResponse(BaseModel):
    latest_successful_run_at: datetime | None
    latest_game_date: date | None
    players: int
    games: int
    player_stat_rows: int

