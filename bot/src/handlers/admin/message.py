import asyncio
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, BotCommandScopeChat
from sqlalchemy import select, func

from src.utils.config import settings
from src.db.db import async_session_maker
from src.models.users import UserModel


router = Router(name="admin_messages")

# Simple in-memory state for actions that require a next message input
admin_action_state: dict[int, str] = {}


async def is_admin(user_id: int) -> bool:
    if user_id in set(settings.ADMIN_IDS or []):
        return True
    async with async_session_maker() as session:
        q = select(UserModel.is_admin).where(UserModel.user_id == str(user_id))
        res = await session.execute(q)
        row = res.first()
    return bool(row and row[0])


@router.message(F.text == "🛠 Админ-панель")
async def open_admin_panel(message: Message):
    if not await is_admin(message.from_user.id):
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Пользователи в БД", callback_data="admin:users_count")],
        [InlineKeyboardButton(text="🚫 Список заблокированных", callback_data="admin:blocked_list")],
        [InlineKeyboardButton(text="📣 Рассылка", callback_data="admin:broadcast")],
        [InlineKeyboardButton(text="🔒 Заблокировать", callback_data="admin:block")],
        [InlineKeyboardButton(text="🔓 Разблокировать", callback_data="admin:unblock")],
        [InlineKeyboardButton(text="➕ Назначить админом", callback_data="admin:add_admin")],
        [InlineKeyboardButton(text="➖ Снять админа", callback_data="admin:remove_admin")],
    ])
    await message.answer("Админ-панель:", reply_markup=kb)


@router.message(F.text)
async def handle_admin_text_actions(message: Message):
    if not await is_admin(message.from_user.id):
        return
    pending = admin_action_state.pop(message.from_user.id, None)
    if not pending:
        return
    text_payload = message.text.strip()
    if pending == "broadcast":
        text = text_payload
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
        return

    # Actions that expect a user token
    token = text_payload
    user = await _get_user_by_token(token)
    if not user:
        await message.answer("Пользователь не найден в базе.")
        return
    async with async_session_maker() as session:
        q = select(UserModel).where(UserModel.id == user.id)
        res = await session.execute(q)
        db_user = res.scalar_one()
        if pending == "add_admin":
            db_user.is_admin = True
        elif pending == "remove_admin":
            db_user.is_admin = False
        elif pending == "block":
            db_user.is_blocked = True
        elif pending == "unblock":
            db_user.is_blocked = False
        await session.commit()
    who = f"@{user.username}" if user.username else user.user_id
    if pending == "add_admin":
        await message.answer(f"Пользователь {who} назначен админом.")
        try:
            target_chat_id = int(user.user_id)
            user_commands = [
                BotCommand(command="start", description="Старт"),
                BotCommand(command="help", description="Помощь"),
            ]
            await message.bot.set_my_commands(
                commands=user_commands,
                scope=BotCommandScopeChat(chat_id=target_chat_id)
            )
        except Exception:
            pass
    elif pending == "remove_admin":
        await message.answer(f"Пользователь {who} снят с админов.")
        try:
            target_chat_id = int(user.user_id)
            user_commands = [
                BotCommand(command="start", description="Старт"),
                BotCommand(command="help", description="Помощь"),
            ]
            await message.bot.set_my_commands(
                commands=user_commands,
                scope=BotCommandScopeChat(chat_id=target_chat_id)
            )
        except Exception:
            pass
    elif pending == "block":
        await message.answer(f"Пользователь {who} заблокирован.")
    elif pending == "unblock":
        await message.answer(f"Пользователь {who} разблокирован.")


@router.message(Command("admin"))
async def cmd_admin_legacy(message: Message):
    # Backward compatibility: open panel if user still types /admin
    await open_admin_panel(message)


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


@router.message(Command("help"))
async def help_legacy(message: Message):
    # Handled in user help; keep for completeness
    from src.handlers.user.message import cmd_help
    await cmd_help(message)

