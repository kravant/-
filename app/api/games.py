from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Tournament
from app.db.session import async_session_maker
from app.schemas.game import GameCreate, GameUpdate


router = APIRouter(
    prefix="/games",
    tags=["Games"],
)


async def get_db():
    async with async_session_maker() as session:
        yield session


@router.get("/")
async def get_games(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Tournament).order_by(Tournament.start_at)
    )

    return result.scalars().all()


@router.post("/")
async def create_game(
    game: GameCreate,
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


@router.put("/{game_id}")
async def update_game(
    game_id: int,
    game_data: GameUpdate,
    db: AsyncSession = Depends(get_db),
):
    game = await db.get(Tournament, game_id)

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
        game.registration_deadline = game_data.registration_deadline

    if game_data.max_players is not None:
        game.max_players = game_data.max_players

    if game_data.status is not None:
        game.status = game_data.status

    await db.commit()
    await db.refresh(game)

    return game
@router.delete("/{game_id}")
async def delete_game(
    game_id: int,
    db: AsyncSession = Depends(get_db),
):
    game = await db.get(Tournament, game_id)

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