from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TournamentType(str, Enum):
    TOURNAMENT = "tournament"
    CASH_GAME = "cash_game"


class TournamentStatus(str, Enum):
    SCHEDULED = "scheduled"
    REGISTRATION = "registration"
    RUNNING = "running"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    type: Mapped[TournamentType] = mapped_column(
        SQLEnum(TournamentType),
        default=TournamentType.TOURNAMENT,
        nullable=False,
    )

    format: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    image_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    rules: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    prize_info: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    registration_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    max_players: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[TournamentStatus] = mapped_column(
        SQLEnum(TournamentStatus),
        default=TournamentStatus.SCHEDULED,
        nullable=False,
    )