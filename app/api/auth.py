import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.config import settings
from app.db.models import Rating, User
from app.db.session import async_session_maker


router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


class TelegramAuthRequest(BaseModel):
    init_data: str


def validate_telegram_init_data(init_data: str) -> dict:
    data = dict(
        parse_qsl(
            init_data,
            keep_blank_values=True
        )
    )

    received_hash = data.pop(
        "hash",
        None
    )

    if not received_hash:
        raise HTTPException(
            status_code=401,
            detail="Telegram hash отсутствует",
        )

    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(
            data.items()
        )
    )

    secret_key = hmac.new(
        b"WebAppData",
        settings.bot_token.encode(),
        hashlib.sha256,
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        calculated_hash,
        received_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Неверные данные Telegram",
        )

    return data


@router.post("/telegram")
async def telegram_auth(
    auth_data: TelegramAuthRequest,
):
    data = validate_telegram_init_data(
        auth_data.init_data
    )

    if "user" not in data:
        raise HTTPException(
            status_code=401,
            detail="Данные пользователя Telegram отсутствуют",
        )

    telegram_user = json.loads(
        data["user"]
    )

    telegram_id = telegram_user["id"]

    async with async_session_maker() as db:

        result = await db.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = result.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=telegram_id,
                username=telegram_user.get("username"),
                first_name=telegram_user.get("first_name"),
                last_name=telegram_user.get("last_name"),
            )

            db.add(user)

            await db.commit()
            await db.refresh(user)

        else:
            user.username = telegram_user.get("username")
            user.first_name = telegram_user.get("first_name")
            user.last_name = telegram_user.get("last_name")

            await db.commit()

        # Создаём рейтинг игрока, если его ещё нет
        rating_result = await db.execute(
            select(Rating).where(
                Rating.user_id == user.id
            )
        )

        rating = rating_result.scalar_one_or_none()

        if not rating:
            rating = Rating(
                user_id=user.id,
                rating=0,
                games_played=0,
            )

            db.add(rating)
            await db.commit()

    return {
        "user_id": user.id,
        "telegram_id": user.telegram_id,
    }