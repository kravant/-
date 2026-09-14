from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Booking,
    BookingStatus,
    GameResult,
    Rating,
    Tournament,
    TournamentStatus,
    User,
)
from app.db.session import async_session_maker
from app.schemas.game_result import (
    FinishGameRequest,
    GameResultCreate,
)


router = APIRouter(
    prefix="/results",
    tags=["Results"],
)


async def get_db():
    async with async_session_maker() as session:
        yield session


@router.post("/")
async def create_result(
    result_data: GameResultCreate,
    db: AsyncSession = Depends(get_db),
):
    # Проверяем пользователя
    user = await db.get(User, result_data.user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден",
        )

    # Проверяем игру
    game = await db.get(Tournament, result_data.tournament_id)

    if not game:
        raise HTTPException(
            status_code=404,
            detail="Игра не найдена",
        )

    # Проверяем место
    if result_data.place < 1:
        raise HTTPException(
            status_code=400,
            detail="Место должно быть больше 0",
        )

    # Проверяем, не был ли уже записан результат
    existing_result = await db.execute(
        select(GameResult).where(
            GameResult.user_id == result_data.user_id,
            GameResult.tournament_id == result_data.tournament_id,
        )
    )

    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Результат этого игрока за эту игру уже добавлен",
        )

    # Рассчитываем изменение рейтинга
    if result_data.place == 1:
        rating_change = 30
    elif result_data.place == 2:
        rating_change = 20
    elif result_data.place == 3:
        rating_change = 15
    else:
        rating_change = 10

    # Создаём результат
    new_result = GameResult(
        user_id=result_data.user_id,
        tournament_id=result_data.tournament_id,
        place=result_data.place,
        rating_change=rating_change,
    )

    db.add(new_result)

    # Получаем рейтинг игрока
    rating_result = await db.execute(
        select(Rating).where(
            Rating.user_id == result_data.user_id
        )
    )

    player_rating = rating_result.scalar_one_or_none()

    # Если рейтинга ещё нет — создаём
    if not player_rating:
        player_rating = Rating(
            user_id=result_data.user_id,
            rating=0,
            games_played=0,
        )
        db.add(player_rating)

    # Обновляем рейтинг
    player_rating.rating += rating_change
    player_rating.games_played += 1

    await db.commit()
    await db.refresh(new_result)

    return new_result


@router.get("/game/{tournament_id}")
async def get_game_results(
    tournament_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GameResult)
        .where(
            GameResult.tournament_id == tournament_id
        )
        .order_by(GameResult.place)
    )

    return result.scalars().all()


@router.get("/user/{user_id}")
async def get_user_results(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден",
        )

    result = await db.execute(
        select(GameResult)
        .where(
            GameResult.user_id == user_id
        )
        .order_by(GameResult.created_at.desc())
    )

    return result.scalars().all()

@router.post("/game/{tournament_id}/finish")
async def finish_game(
    tournament_id: int,
    data: FinishGameRequest,
    db: AsyncSession = Depends(get_db),
):
    # Проверяем игру
    game = await db.get(Tournament, tournament_id)

    if not game:
        raise HTTPException(
            status_code=404,
            detail="Игра не найдена",
        )

    # Проверяем, что результаты переданы
    if not data.results:
        raise HTTPException(
            status_code=400,
            detail="Нужно добавить хотя бы одного игрока",
        )

    # Проверяем места
    places = [item.place for item in data.results]

    if any(place < 1 for place in places):
        raise HTTPException(
            status_code=400,
            detail="Место должно быть больше 0",
        )

    # Проверяем одинаковые места
    if len(places) != len(set(places)):
        raise HTTPException(
            status_code=400,
            detail="Места игроков не должны повторяться",
        )

    # Проверяем, не добавлялись ли уже результаты
    existing_results = await db.execute(
        select(GameResult).where(
            GameResult.tournament_id == tournament_id
        )
    )

    if existing_results.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="Результаты этой игры уже были добавлены",
        )

    created_results = []

    for item in data.results:

        # Проверяем игрока
        user = await db.get(User, item.user_id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"Пользователь {item.user_id} не найден",
            )
        # Проверяем, что игрок был записан на игру
        booking_result = await db.execute(
            select(Booking).where(
                Booking.user_id == item.user_id,
                Booking.tournament_id == tournament_id,
                Booking.status == BookingStatus.CONFIRMED,
            )
        )

        booking = booking_result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=400,
                detail=f"Пользователь {item.user_id} не был записан на эту игру",
            )

        # Рассчитываем рейтинг
        if item.place == 1:
            rating_change = 30
        elif item.place == 2:
            rating_change = 20
        elif item.place == 3:
            rating_change = 15
        else:
            rating_change = 10

        # Создаём результат
        new_result = GameResult(
            user_id=item.user_id,
            tournament_id=tournament_id,
            place=item.place,
            rating_change=rating_change,
        )

        db.add(new_result)

        # Получаем рейтинг игрока
        rating_result = await db.execute(
            select(Rating).where(
                Rating.user_id == item.user_id
            )
        )

        player_rating = rating_result.scalar_one_or_none()

        # Если рейтинга ещё нет — создаём
        if not player_rating:
            player_rating = Rating(
                user_id=item.user_id,
                rating=0,
                games_played=0,
            )
            db.add(player_rating)

        # Обновляем рейтинг
        player_rating.rating += rating_change
        player_rating.games_played += 1

        created_results.append(new_result)

    # Завершаем игру
    game.status = TournamentStatus.FINISHED

    await db.commit()

    for result in created_results:
        await db.refresh(result)

    return {
        "message": "Игра завершена",
        "tournament_id": tournament_id,
        "results": created_results,
    }
