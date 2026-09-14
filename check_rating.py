import asyncio

from sqlalchemy import select

from app.db.models import Rating, User
from app.db.session import async_session_maker


async def main():
    async with async_session_maker() as db:
        result = await db.execute(
            select(Rating, User)
            .join(User, Rating.user_id == User.id)
        )

        rows = result.all()

        print("КОЛИЧЕСТВО РЕЙТИНГОВ:", len(rows))

        for rating, user in rows:
            print(
                "USER:",
                user.id,
                user.telegram_id,
                user.first_name,
                "| RATING:",
                rating.rating,
                "| GAMES:",
                rating.games_played,
            )


asyncio.run(main())
