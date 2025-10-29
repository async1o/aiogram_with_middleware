__all__ = ("main_router", )

from aiogram import Router

from .admin import admin_router
from .user import user_router

main_router = Router()
main_router.include_routers(admin_router,user_router)