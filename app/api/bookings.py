from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Booking, BookingStatus, Tournament, User
from app.db.session import async_session_maker
from app.schemas.booking import BookingCreate


router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"],
)


async def get_db():
    async with async_session_maker() as session:
        yield session


@router.post("/")
async def create_booking(
    booking: BookingCreate,
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, booking.user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден",
        )

    game = await db.get(Tournament, booking.tournament_id)

    if not game:
        raise HTTPException(
            status_code=404,
            detail="Игра не найдена",
        )

    existing_booking_result = await db.execute(
        select(Booking).where(
            Booking.user_id == booking.user_id,
            Booking.tournament_id == booking.tournament_id,
        )
    )

    existing_booking = existing_booking_result.scalar_one_or_none()

    if existing_booking:
        if existing_booking.status != BookingStatus.CANCELLED:
            raise HTTPException(
                status_code=400,
                detail="Вы уже записаны на эту игру",
            )

        await db.delete(existing_booking)
        await db.flush()
    result = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.tournament_id == booking.tournament_id,
            Booking.status == BookingStatus.CONFIRMED,
        )
    )

    confirmed_count = result.scalar_one()

    if confirmed_count < game.max_players:
        status = BookingStatus.CONFIRMED
    else:
        status = BookingStatus.WAITING

    new_booking = Booking(
        user_id=booking.user_id,
        tournament_id=booking.tournament_id,
        status=status,
    )

    db.add(new_booking)

    await db.commit()
    await db.refresh(new_booking)

    return new_booking
@router.get("/game/{tournament_id}")
async def get_game_bookings(
    tournament_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Booking).where(
            Booking.tournament_id == tournament_id
        )
    )

    bookings = result.scalars().all()

    return bookings
@router.get("/user/{user_id}")
async def get_user_bookings(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Booking).where(
            Booking.user_id == user_id
        )
    )

    bookings = result.scalars().all()

    return bookings
@router.delete("/{booking_id}")
async def cancel_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
):
    booking = await db.get(Booking, booking_id)

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Запись не найдена",
        )

    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(
            status_code=400,
            detail="Запись уже отменена",
        )

    tournament_id = booking.tournament_id

    booking.status = BookingStatus.CANCELLED

    waiting_result = await db.execute(
        select(Booking)
        .where(
            Booking.tournament_id == tournament_id,
            Booking.status == BookingStatus.WAITING,
        )
        .order_by(Booking.created_at)
    )

    waiting_booking = waiting_result.scalars().first()

    if waiting_booking:
        waiting_booking.status = BookingStatus.CONFIRMED

    await db.commit()

    return {
        "status": "cancelled",
        "booking_id": booking.id,
        "promoted_booking_id": (
            waiting_booking.id if waiting_booking else None
        ),
    }