"""
ABUTAHUNT — Anti-Fraud Middleware Gate
Blocks CRITICAL risk users from sensitive actions.
Prepared by Abuta (@abuta_art)
"""

from typing import Callable, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from database.models import FraudRisk
from locales.strings import t


class AntiFraudMiddleware(BaseMiddleware):
    SENSITIVE_CALLBACKS = {"withdraw", "verify", "claim_reward"}

    async def __call__(
        self,
        handler: Callable,
        event: TelegramObject,
        data: dict,
    ) -> Any:
        user = data.get("user")
        lang = data.get("lang", "en")

        if not user:
            return await handler(event, data)

        # Suspended users — full block
        if user.is_suspended:
            msg = t("suspended", lang)
            if isinstance(event, Message):
                await event.answer(msg)
            elif isinstance(event, CallbackQuery):
                await event.answer(t("suspended", lang), show_alert=True)
            return

        # CRITICAL risk — block sensitive callbacks only
        if user.risk_score == FraudRisk.CRITICAL:
            if isinstance(event, CallbackQuery):
                cb_data = event.data or ""
                for key in self.SENSITIVE_CALLBACKS:
                    if key in cb_data:
                        await event.answer(t("fraud_blocked", lang), show_alert=True)
                        return

        return await handler(event, data)
