"""
ABUTAHUNT — User Register Middleware
Auto-registers new users and injects db session + user into handler data.
Prepared by Abuta (@abuta_art)
"""

from typing import Callable, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from database.engine import AsyncSessionLocal
from services.user_service import get_or_create_user


class UserRegisterMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable,
        event: TelegramObject,
        data: dict,
    ) -> Any:
        tg_user = None
        if isinstance(event, Message):
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user

        async with AsyncSessionLocal() as session:
            data["session"] = session

            if tg_user:
                user, is_new = await get_or_create_user(
                    session=session,
                    telegram_id=tg_user.id,
                    first_name=tg_user.first_name or "User",
                    last_name=tg_user.last_name,
                    username=tg_user.username,
                    language_code=tg_user.language_code or "en",
                )
                data["user"] = user
                data["is_new_user"] = is_new
                data["lang"] = user.language_code

            return await handler(event, data)
