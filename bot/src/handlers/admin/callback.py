from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select, func

from .message import is_admin, admin_action_state
from src.db.db import async_session_maker
from src.models.users import UserModel

router = Router(name="admin_callbacks")


@router.callback_query(F.data == "admin:users_count")
async def cb_users_count(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    async with async_session_maker() as session:
        q = select(func.count()).select_from(UserModel)
        res = await session.execute(q)
        count = res.scalar_one()
    await call.message.answer(f"Пользователей в базе: {count}")
    await call.answer()


@router.callback_query(F.data == "admin:blocked_list")
async def cb_blocked_list(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    async with async_session_maker() as session:
        q = select(UserModel).where(UserModel.is_blocked == True).order_by(UserModel.id.desc()).limit(50)
        res = await session.execute(q)
        users = res.scalars().all()
    if not users:
        await call.message.answer("Заблокированных пользователей нет.")
        await call.answer()
        return
    lines = ["Заблокированные (макс. 50):"]
    for u in users:
        uname = f"@{u.username}" if u.username else "—"
        lines.append(f"- {uname} (id={u.user_id})")
    await call.message.answer("\n".join(lines))
    await call.answer()


def _set_action(call: CallbackQuery, action: str, prompt: str):
    admin_action_state[call.from_user.id] = action
    return call.message.answer(prompt)


@router.callback_query(F.data == "admin:broadcast")
async def cb_broadcast(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    await _set_action(call, "broadcast", "Отправьте текст рассылки одним сообщением.")
    await call.answer()


@router.callback_query(F.data == "admin:block")
async def cb_block(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    await _set_action(call, "block", "Отправьте user_id или @username для блокировки.")
    await call.answer()


@router.callback_query(F.data == "admin:unblock")
async def cb_unblock(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    await _set_action(call, "unblock", "Отправьте user_id или @username для разблокировки.")
    await call.answer()


@router.callback_query(F.data == "admin:add_admin")
async def cb_add_admin(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    await _set_action(call, "add_admin", "Отправьте user_id или @username для назначения админом.")
    await call.answer()


@router.callback_query(F.data == "admin:remove_admin")
async def cb_remove_admin(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer()
        return
    await _set_action(call, "remove_admin", "Отправьте user_id или @username для снятия админа.")
    await call.answer()

