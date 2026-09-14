import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GameResult, Rating, User
from app.db.session import async_session_maker


router = APIRouter(
    prefix="/rating",
    tags=["Rating"],
)


async def get_db():
    async with async_session_maker() as session:
        yield session


@router.get("/user/{user_id}")
async def get_user_rating(
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
        select(Rating).where(
            Rating.user_id == user_id
        )
    )

    rating = result.scalar_one_or_none()

    if not rating:
        return {
            "user_id": user_id,
            "rating": 0,
            "games_played": 0,
        }

    return rating


@router.get("/")
async def get_rating_leaderboard(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Rating, User)
        .join(User, Rating.user_id == User.id)
        .order_by(Rating.rating.desc())
    )

    rows = result.all()

    leaderboard = []

    for place, (rating, user) in enumerate(rows, start=1):

        leaderboard.append({
            "place": place,
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "rating": rating.rating,
            "games_played": rating.games_played,
        })

    return Response(
        content=json.dumps(
            leaderboard,
            ensure_ascii=False
        ),
        media_type="application/json; charset=utf-8",
    )


@router.get("/profile/{user_id}")
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден",
        )

    rating_result = await db.execute(
        select(Rating).where(
            Rating.user_id == user_id
        )
    )

    rating = rating_result.scalar_one_or_none()

    if not rating:
        current_rating = 0
        games_played = 0
    else:
        current_rating = rating.rating
        games_played = rating.games_played

    results_query = await db.execute(
        select(GameResult)
        .where(GameResult.user_id == user_id)
        .order_by(GameResult.created_at.desc())
    )

    results = results_query.scalars().all()

    history = []

    for result in results:

        history.append({
            "game_id": result.tournament_id,
            "place": result.place,
            "rating_change": result.rating_change,
            "created_at": result.created_at,
        })

    return {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "avatar_url": user.avatar_url,
        "rating": current_rating,
        "games_played": games_played,
        "history": history,
    }