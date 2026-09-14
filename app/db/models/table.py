from enum import Enum

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TableStatus(str, Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    PAUSED = "paused"
    CLOSED = "closed"


class Table(Base):
    __tablename__ = "tables"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    tournament_id: Mapped[int | None] = mapped_column(
        ForeignKey("tournaments.id", ondelete="SET NULL"),
        nullable=True,
    )

    max_players: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=9,
    )

    small_blind: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    big_blind: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[TableStatus] = mapped_column(
        SQLEnum(TableStatus),
        default=TableStatus.WAITING,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )