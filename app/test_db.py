import asyncio

from sqlalchemy import text

from app.db.session import engine


async def test_database():
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))
        print(result.scalar())


asyncio.run(test_database())