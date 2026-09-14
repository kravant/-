from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.users import router as users_router
from app.api.games import router as games_router
from app.api.bookings import router as bookings_router
from app.api.results import router as results_router
from app.api.rating import router as rating_router
from app.api.auth import router as auth_router
app = FastAPI()
app.mount("/app", StaticFiles(directory="static", html=True), name="static")

app.include_router(users_router)
app.include_router(games_router)
app.include_router(bookings_router)
app.include_router(results_router)
app.include_router(rating_router)
app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "Poker Club API работает!"}