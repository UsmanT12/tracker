from datetime import date

from pydantic import BaseModel, Field, model_validator


class DiscoveredGame(BaseModel):
    source_game_id: str
    source_url: str


class IngestedTeam(BaseModel):
    name: str
    abbreviation: str | None = None
    source_team_id: str | None = None


class IngestedPlayerStat(BaseModel):
    display_name: str
    source_player_id: str | None = None
    team_name: str
    opponent_name: str
    is_home: bool | None = None
    started: bool | None = None
    played: bool = True
    dnp_reason: str | None = None
    minutes_seconds: int = Field(default=0, ge=0)
    fgm: int = Field(default=0, ge=0)
    fga: int = Field(default=0, ge=0)
    fg3m: int = Field(default=0, ge=0)
    fg3a: int = Field(default=0, ge=0)
    ftm: int = Field(default=0, ge=0)
    fta: int = Field(default=0, ge=0)
    oreb: int = Field(default=0, ge=0)
    dreb: int = Field(default=0, ge=0)
    reb: int = Field(default=0, ge=0)
    ast: int = Field(default=0, ge=0)
    pf: int = Field(default=0, ge=0)
    stl: int = Field(default=0, ge=0)
    tov: int = Field(default=0, ge=0)
    blk: int = Field(default=0, ge=0)
    pts: int = Field(default=0, ge=0)
    plus_minus: int | None = None

    @model_validator(mode="after")
    def validate_attempts(self) -> "IngestedPlayerStat":
        for made, attempted, label in (
            (self.fgm, self.fga, "field goals"),
            (self.fg3m, self.fg3a, "three-pointers"),
            (self.ftm, self.fta, "free throws"),
        ):
            if made > attempted:
                raise ValueError(f"{label} made cannot exceed attempts")
        return self


class IngestedGame(BaseModel):
    source_game_id: str
    source_url: str
    season: int
    season_type: str = "regular"
    game_date: date
    status: str = "completed"
    home_team: IngestedTeam
    away_team: IngestedTeam
    home_score: int | None = None
    away_score: int | None = None
    player_stats: list[IngestedPlayerStat]

    @model_validator(mode="after")
    def validate_game(self) -> "IngestedGame":
        if not self.player_stats:
            raise ValueError("a completed box score must contain player rows")
        return self

