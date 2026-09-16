from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.auth import router as auth_router
from app.api.bookings import router as bookings_router
from app.api.games import router as games_router
from app.api.rating import router as rating_router
from app.api.results import router as results_router
from app.api.users import router as users_router
from app.config import settings


async def run_migrations():
    engine = create_async_engine(
        settings.async_database_url,
        echo=False,
    )

    async with engine.begin() as connection:

        def upgrade(sync_connection):
            alembic_config = Config("alembic.ini")
            alembic_config.attributes["connection"] = sync_connection
            command.upgrade(
                alembic_config,
                "head",
            )

        await connection.run_sync(upgrade)

    await engine.dispose()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_migrations()
    yield


app = FastAPI(
    lifespan=lifespan,
)


app.mount(
    "/app",
    StaticFiles(
        directory="static",
        html=True,
    ),
    name="static",
)


app.include_router(users_router)
app.include_router(games_router)
app.include_router(bookings_router)
app.include_router(results_router)
app.include_router(rating_router)
app.include_router(auth_router)


@app.get("/")
async def root():
    return {
        "message": "Poker Club API работает!"
    }