import asyncio
from aiogram import Router, F
from aiogram.types import Message, BotCommand, BotCommandScopeChat
from sqlalchemy import select, func

from src.utils.config import settings
from src.db.db import async_session_maker
from src.models.users import UserModel


router = Router(name="admin_messages")


async def is_admin(user_id: int) -> bool:
    if user_id in set(settings.ADMIN_IDS or []):
        return True
    async with async_session_maker() as session:
        q = select(UserModel.is_admin).where(UserModel.user_id == str(user_id))
        res = await session.execute(q)
        row = res.first()
    return bool(row and row[0])


@router.message(F.text == "/admin")
async def cmd_admin(message: Message):
    if not await is_admin(message.from_user.id):
        return
    await message.answer(
        "Админ-панель:\n"
        "- /users_count — количество пользователей\n"
        "- /broadcast &lt;текст&gt; — рассылка\n"
        "- /block &lt;user_id|@username&gt; — заблокировать пользователя\n"
        "- /unblock &lt;user_id|@username&gt; — разблокировать пользователя\n"
        "- /blocked_list — список заблокированных\n"
        "- /add_admin &lt;user_id|@username&gt; — назначить админом\n"
        "- /remove_admin &lt;user_id|@username&gt; — снять админа"
    )


@router.message(F.text.regexp(r"^/add_admin\s+.+"))
async def cmd_add_admin(message: Message):
    if not await is_admin(message.from_user.id):
        return
    token = message.text.split(maxsplit=1)[1]
    user = await _get_user_by_token(token)
    if not user:
        await message.answer("Пользователь не найден в базе.")
        return
    async with async_session_maker() as session:
        q = select(UserModel).where(UserModel.id == user.id)
        res = await session.execute(q)
        db_user = res.scalar_one()
        db_user.is_admin = True
        await session.commit()
    who = f"@{user.username}" if user.username else user.user_id
    await message.answer(f"Пользователь {who} назначен админом.")

    try:
        target_chat_id = int(user.user_id)
        user_commands = [
            BotCommand(command="start", description="Старт"),
            BotCommand(command="catalog", description="Каталог"),
            BotCommand(command="cart", description="Корзина"),
        ]
        admin_extra_commands = [
            BotCommand(command="admin", description="Админ-панель"),
            BotCommand(command="users_count", description="Пользователи в БД"),
            BotCommand(command="broadcast", description="Рассылка"),
            BotCommand(command="block", description="Заблокировать пользователя"),
            BotCommand(command="unblock", description="Разблокировать пользователя"),
            BotCommand(command="blocked_list", description="Список заблокированных"),
            BotCommand(command="add_admin", description="Назначить админом"),
            BotCommand(command="remove_admin", description="Снять админа"),
        ]
        await message.bot.set_my_commands(
            commands=user_commands + admin_extra_commands,
            scope=BotCommandScopeChat(chat_id=target_chat_id)
        )
    except Exception:
        pass


@router.message(F.text.regexp(r"^/remove_admin\s+.+"))
async def cmd_remove_admin(message: Message):
    if not await is_admin(message.from_user.id):
        return
    token = message.text.split(maxsplit=1)[1]
    user = await _get_user_by_token(token)
    if not user:
        await message.answer("Пользователь не найден в базе.")
        return
    async with async_session_maker() as session:
        q = select(UserModel).where(UserModel.id == user.id)
        res = await session.execute(q)
        db_user = res.scalar_one()
        db_user.is_admin = False
        await session.commit()
    who = f"@{user.username}" if user.username else user.user_id
    await message.answer(f"Пользователь {who} снят с админов.")

    try:
        target_chat_id = int(user.user_id)
        user_commands = [
            BotCommand(command="start", description="Старт"),
            BotCommand(command="catalog", description="Каталог"),
            BotCommand(command="cart", description="Корзина"),
        ]
        await message.bot.set_my_commands(
            commands=user_commands,
            scope=BotCommandScopeChat(chat_id=target_chat_id)
        )
    except Exception:
        pass


@router.message(F.text == "/users_count")
async def cmd_users_count(message: Message):
    if not await is_admin(message.from_user.id):
        return
    async with async_session_maker() as session:
        q = select(func.count()).select_from(UserModel)
        res = await session.execute(q)
        count = res.scalar_one()
    await message.answer(f"Пользователей в базе: {count}")


@router.message(F.text.regexp(r"^/broadcast\s+.+"))
async def cmd_broadcast(message: Message):
    if not await is_admin(message.from_user.id):
        return

    text = message.text.split(maxsplit=1)[1]

    async with async_session_maker() as session:
        q = select(UserModel.user_id)
        res = await session.execute(q)
        user_ids = [int(uid) for (uid,) in res.fetchall()]

    sent = 0
    for uid in user_ids:
        try:
            await message.bot.send_message(chat_id=uid, text=text)
            sent += 1
            await asyncio.sleep(0.03)
        except Exception:
            continue

    await message.answer(f"Рассылка завершена. Отправлено: {sent}")


def _normalize_username(value: str) -> str:
    v = value.strip()
    if v.startswith("@"):
        v = v[1:]
    return v.lower()


async def _get_user_by_token(token: str) -> UserModel | None:
    async with async_session_maker() as session:
        if token.isdigit():
            q = select(UserModel).where(UserModel.user_id == token)
            res = await session.execute(q)
            return res.scalar_one_or_none()
        username = _normalize_username(token)
        q = select(UserModel).where(func.lower(UserModel.username) == username)
        res = await session.execute(q)
        return res.scalar_one_or_none()


@router.message(F.text.regexp(r"^/block\s+.+"))
async def cmd_block(message: Message):
    if not await is_admin(message.from_user.id):
        return
    token = message.text.split(maxsplit=1)[1]
    user = await _get_user_by_token(token)
    if not user:
        await message.answer("Пользователь не найден в базе.")
        return
    async with async_session_maker() as session:
        q = select(UserModel).where(UserModel.id == user.id)
        res = await session.execute(q)
        db_user = res.scalar_one()
        db_user.is_blocked = True
        await session.commit()
    who = f"@{user.username}" if user.username else user.user_id
    await message.answer(f"Пользователь {who} заблокирован.")


@router.message(F.text.regexp(r"^/unblock\s+.+"))
async def cmd_unblock(message: Message):
    if not await is_admin(message.from_user.id):
        return
    token = message.text.split(maxsplit=1)[1]
    user = await _get_user_by_token(token)
    if not user:
        await message.answer("Пользователь не найден в базе.")
        return
    async with async_session_maker() as session:
        q = select(UserModel).where(UserModel.id == user.id)
        res = await session.execute(q)
        db_user = res.scalar_one()
        db_user.is_blocked = False
        await session.commit()
    who = f"@{user.username}" if user.username else user.user_id
    await message.answer(f"Пользователь {who} разблокирован.")


@router.message(F.text == "/blocked_list")
async def cmd_blocked_list(message: Message):
    if not await is_admin(message.from_user.id):
        return
    async with async_session_maker() as session:
        q = select(UserModel).where(UserModel.is_blocked == True).order_by(UserModel.id.desc()).limit(50)
        res = await session.execute(q)
        users = res.scalars().all()
    if not users:
        await message.answer("Заблокированных пользователей нет.")
        return
    lines = ["Заблокированные (макс. 50):"]
    for u in users:
        uname = f"@{u.username}" if u.username else "—"
        lines.append(f"- {uname} (id={u.user_id})")
    await message.answer("\n".join(lines))

