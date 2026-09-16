import json

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import validate_telegram_init_data
from app.db.models import User
from app.db.session import async_session_maker


async def get_db():
    async with async_session_maker() as session:
        yield session


async def get_current_user(
    x_init_data: str = Header(..., alias="X-Init-Data"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Достаёт юзера по initData из заголовка X-Init-Data."""
    data = validate_telegram_init_data(x_init_data)

    if "user" not in data:
        raise HTTPException(401, "Нет данных пользователя")

    telegram_user = json.loads(data["user"])
    telegram_id = telegram_user["id"]

    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(401, "Не авторизован. Открой приложение заново.")

    return user


async def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Пускает только админов."""
    if not user.is_admin:
        raise HTTPException(403, "Доступно только администратору")
    return user