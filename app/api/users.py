from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.db.models import User
from app.db.session import async_session_maker
from app.schemas.user import UserCreate, UserResponse


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


async def get_db():
    async with async_session_maker() as session:
        yield session


@router.get("/", response_model=list[UserResponse])
async def get_users(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User)
    )

    users = result.scalars().all()

    return users


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    new_user = User(
        telegram_id=user_data.telegram_id,
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        avatar_url=user_data.avatar_url,
    )

    db.add(new_user)

    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.get("/me")
async def get_me(
    user: User = Depends(get_current_user),
):
    """Возвращает текущего юзера по initData из заголовка X-Init-Data."""
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "avatar_url": user.avatar_url,
        "is_admin": user.is_admin,
    }


@router.get("/admin-check")
async def admin_check(
    user: User = Depends(require_admin),
):
    """Возвращает 200 только если ты админ. Иначе 403."""
    return {
        "ok": True,
        "admin_name": user.first_name,
    }
@router.post("/make-me-admin-secret")
async def make_me_admin_secret(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """ВРЕМЕННЫЙ эндпоинт. Удалить после использования!"""
    user.is_admin = True
    await db.commit()
    await db.refresh(user)
    return {
        "ok": True,
        "message": f"{user.first_name} теперь админ",
        "telegram_id": user.telegram_id,
    }