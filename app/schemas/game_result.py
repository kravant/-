from pydantic import BaseModel


class GameResultCreate(BaseModel):
    user_id: int
    tournament_id: int
    place: int


class GameResultItem(BaseModel):
    user_id: int
    place: int


class FinishGameRequest(BaseModel):
    results: list[GameResultItem]