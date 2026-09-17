import json

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import validate_telegram_init_data
from app.db.models import Booking, Tournament, User
from app.db.session import async_session_maker
from app.schemas.game import GameCreate, GameUpdate


ADMIN_TELEGRAM_ID = 777284368


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


async def get_db():
    async with async_session_maker() as session:
        yield session


def get_telegram_user_id(
    x_telegram_init_data: str = Header(
        ...,
        alias="X-Telegram-Init-Data",
    ),
) -> int:

    data = validate_telegram_init_data(
        x_telegram_init_data
    )

    if "user" not in data:
        raise HTTPException(
            status_code=401,
            detail="Данные пользователя Telegram отсутствуют",
        )

    try:
        telegram_user = json.loads(
            data["user"]
        )

        telegram_id = int(
            telegram_user["id"]
        )

    except (
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
    ):
        raise HTTPException(
            status_code=401,
            detail="Некорректные данные Telegram",
        )

    return telegram_id


def require_admin(
    telegram_id: int = Depends(
        get_telegram_user_id
    ),
) -> int:

    if telegram_id != ADMIN_TELEGRAM_ID:
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещён",
        )

    return telegram_id


@router.get("/check")
async def check_admin(
    telegram_id: int = Depends(
        require_admin
    ),
):
    return {
        "is_admin": True,
        "telegram_id": telegram_id,
    }


@router.get("/games")
async def admin_get_games(
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Tournament).order_by(
            Tournament.start_at
        )
    )

    return result.scalars().all()


@router.post("/games")
async def admin_create_game(
    game: GameCreate,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    new_game = Tournament(
        name=game.name,
        description=game.description,
        type=game.type,
        format=game.format,
        location=game.location,
        image_url=game.image_url,
        rules=game.rules,
        prize_info=game.prize_info,
        start_at=game.start_at,
        registration_deadline=game.registration_deadline,
        max_players=game.max_players,
    )

    db.add(new_game)

    await db.commit()
    await db.refresh(new_game)

    return new_game


@router.put("/games/{game_id}")
async def admin_update_game(
    game_id: int,
    game_data: GameUpdate,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    game = await db.get(
        Tournament,
        game_id,
    )

    if not game:
        raise HTTPException(
            status_code=404,
            detail="Игра не найдена",
        )

    if game_data.name is not None:
        game.name = game_data.name

    if game_data.description is not None:
        game.description = game_data.description

    if game_data.type is not None:
        game.type = game_data.type

    if game_data.format is not None:
        game.format = game_data.format

    if game_data.location is not None:
        game.location = game_data.location

    if game_data.image_url is not None:
        game.image_url = game_data.image_url

    if game_data.rules is not None:
        game.rules = game_data.rules

    if game_data.prize_info is not None:
        game.prize_info = game_data.prize_info

    if game_data.start_at is not None:
        game.start_at = game_data.start_at

    if game_data.registration_deadline is not None:
        game.registration_deadline = (
            game_data.registration_deadline
        )

    if game_data.max_players is not None:
        game.max_players = game_data.max_players

    if game_data.status is not None:
        game.status = game_data.status

    await db.commit()
    await db.refresh(game)

    return game


@router.delete("/games/{game_id}")
async def admin_delete_game(
    game_id: int,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    game = await db.get(
        Tournament,
        game_id,
    )

    if not game:
        raise HTTPException(
            status_code=404,
            detail="Игра не найдена",
        )

    await db.delete(game)
    await db.commit()

    return {
        "message": "Игра удалена",
        "game_id": game_id,
    }


@router.get("/games/{game_id}/bookings")
async def admin_get_game_bookings(
    game_id: int,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    game = await db.get(
        Tournament,
        game_id,
    )

    if not game:
        raise HTTPException(
            status_code=404,
            detail="Игра не найдена",
        )

    result = await db.execute(
        select(Booking, User)
        .join(
            User,
            Booking.user_id == User.id,
        )
        .where(
            Booking.tournament_id == game_id
        )
        .order_by(
            Booking.created_at
        )
    )

    rows = result.all()

    bookings = []

    for booking, user in rows:

        bookings.append({
            "booking_id": booking.id,
            "user_id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "status": booking.status,
            "created_at": booking.created_at,
        })

    return bookings