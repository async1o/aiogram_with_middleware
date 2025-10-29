import logging
from typing import Callable, Any, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Update
from aiogram.types.user import User
from sqlalchemy import insert, select

from src.db.db import async_session_maker
from src.models.users import UserModel
from src.utils.config import settings

class UserAddMiddleware(BaseMiddleware):
    async def add_user_to_db(self, user: User):
        async with async_session_maker() as session:
            select_stmt = select(UserModel).where(UserModel.user_id == str(user.id))
            res = await session.execute(select_stmt)
            if res.fetchall():
                return

            dict_user = user.model_dump()
            bad_values = [
                'added_to_attachment_menu', 'can_join_groups',
                'can_connect_to_business', 'has_main_web_app',
                'can_read_all_group_messages',
                'supports_inline_queries']
            
            for value in bad_values:
                dict_user.pop(value)

            dict_user['user_id'] = str(dict_user.pop('id'))

            insert_stmt = insert(UserModel).values(**dict_user)
            await session.execute(insert_stmt)
            await session.commit()
            logging.info(f'User {user.id} saved')

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any]
    ):
        user = data['event_from_user']
        await self.add_user_to_db(user)

        try:
            async with async_session_maker() as session:
                q = select(UserModel.is_blocked).where(UserModel.user_id == str(user.id))
                res = await session.execute(q)
                row = res.first()
                is_blocked = bool(row[0]) if row else False
        except Exception:
            is_blocked = False

        is_admin = user.id in set(settings.ADMIN_IDS or [])
        if is_blocked and not is_admin:
            return None

        return await handler(event, data)
    