import logging
import asyncio

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat

from src.utils.config import settings
from src.utils.middleware import UserAddMiddleware
from src.handlers import main_router
from src.db.db import reset_tables

logging.basicConfig(level=logging.INFO)
logger = logging.Logger(__name__)

async def main():
    session = AiohttpSession()
    bot = Bot(
        token=settings.TOKEN.get_secret_value(),
        session=session,
        default=DefaultBotProperties(parse_mode='HTML')
    )

    dp = Dispatcher()
    dp.message.outer_middleware(UserAddMiddleware())

    dp.include_router(main_router)

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
    ]


    await bot.set_my_commands(commands=user_commands, scope=BotCommandScopeAllPrivateChats())

    try:
        for admin_id in (settings.ADMIN_IDS or []):
            await bot.set_my_commands(commands=user_commands + admin_extra_commands, scope=BotCommandScopeChat(chat_id=admin_id))
    except Exception:
        pass

    await reset_tables()

    try:
        await dp.start_polling(bot)
        
    except ValueError as e:
        logger.error('ValueError occured: %s: ', e)
    except KeyError as e:
        logger.error("KeyError occured: %s: ", e)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())