from pydantic import BaseModel


class BookingCreate(BaseModel):
    user_id: int
    tournament_id: int