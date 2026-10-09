"""
ABUTAHUNT — Rate Limit Middleware
Prepared by Abuta (@abuta_art)
"""

import time
from typing import Callable, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from cachetools import TTLCache

from config import settings

# In-memory rate limit store: user_id → last_request_time
_cache: TTLCache = TTLCache(maxsize=100_000, ttl=60)


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit_seconds: int = None):
        self.limit = limit_seconds or settings.FRAUD_RATE_LIMIT_SECONDS

    async def __call__(
        self,
        handler: Callable,
        event: TelegramObject,
        data: dict,
    ) -> Any:
        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user
            if not user:
                return await handler(event, data)

            now = time.monotonic()
            last = _cache.get(user.id)

            if last and (now - last) < self.limit:
                # Silently drop or answer callback to avoid spinner
                if isinstance(event, CallbackQuery):
                    await event.answer("⏳ Too fast. Please wait.", show_alert=False)
                return  # Drop update

            _cache[user.id] = now

        return await handler(event, data)
