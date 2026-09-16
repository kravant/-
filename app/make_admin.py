import asyncio

from sqlalchemy import select, update

from app.db.models import User
from app.db.session import async_session_maker


async def list_users():
    async with async_session_maker() as db:
        result = await db.execute(select(User).order_by(User.id))
        users = result.scalars().all()

        print("\n=== Все пользователи в БД ===")
        for u in users:
            print(
                f"id={u.id} | telegram_id={u.telegram_id} | "
                f"{u.first_name} {u.last_name or ''} | "
                f"@{u.username or '—'} | is_admin={u.is_admin}"
            )
        print()


async def make_admin(telegram_id: int):
    async with async_session_maker() as db:
        result = await db.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(is_admin=True)
        )
        await db.commit()

        if result.rowcount == 0:
            print(f"⚠️  Пользователь с telegram_id={telegram_id} не найден")
        else:
            print(f"✅ Пользователь {telegram_id} теперь админ")


async def main():
    await list_users()

    answer = input(
        "Введи telegram_id, кого сделать админом (или Enter чтобы выйти): "
    ).strip()

    if not answer:
        return

    try:
        tg_id = int(answer)
    except ValueError:
        print("❌ Это не число")
        return

    await make_admin(tg_id)


if __name__ == "__main__":
    asyncio.run(main())