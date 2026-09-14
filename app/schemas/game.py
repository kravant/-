from datetime import datetime

from pydantic import BaseModel

from app.db.models.tournament import TournamentStatus, TournamentType


class GameCreate(BaseModel):
    name: str
    description: str | None = None
    type: TournamentType
    format: str | None = None
    location: str | None = None
    image_url: str | None = None
    rules: str | None = None
    prize_info: str | None = None
    start_at: datetime
    registration_deadline: datetime | None = None
    max_players: int


class GameUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    type: TournamentType | None = None
    format: str | None = None
    location: str | None = None
    image_url: str | None = None
    rules: str | None = None
    prize_info: str | None = None
    start_at: datetime | None = None
    registration_deadline: datetime | None = None
    max_players: int | None = None
    status: TournamentStatus | None = None