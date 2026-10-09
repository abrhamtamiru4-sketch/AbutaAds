"""
ABUTAHUNT — Notification Service
Prepared by Abuta (@abuta_art)
"""

import asyncio
import logging
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import AsyncSessionLocal
from database.models import User, Notification, NotificationType
from locales.strings import t
from config import settings

logger = logging.getLogger(__name__)


async def send_notification(
    bot: Bot,
    user_id: int,
    notif_type: str,
    text: str,
    session: Optional[AsyncSession] = None,
    reply_markup=None,
) -> bool:
    """Send Telegram message and persist notification record."""
    try:
        await bot.send_message(user_id, text, parse_mode="HTML", reply_markup=reply_markup)
        if session:
            notif = Notification(
                user_id=user_id,
                notif_type=notif_type,
                message=text,
            )
            session.add(notif)
        return True
    except TelegramForbiddenError:
        logger.info(f"User {user_id} blocked the bot")
        return False
    except TelegramBadRequest as e:
        logger.warning(f"Bad request sending to {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to notify {user_id}: {e}")
        return False


async def notify_reward_approved(bot: Bot, user_id: int, amount, lang: str = "en") -> None:
    text = t("notif_reward_approved", lang, amount=amount)
    await send_notification(bot, user_id, NotificationType.REWARD_APPROVED, text)


async def notify_reward_rejected(bot: Bot, user_id: int, reason: str, lang: str = "en") -> None:
    text = t("notif_reward_rejected", lang, reason=reason)
    await send_notification(bot, user_id, NotificationType.REWARD_REJECTED, text)


async def notify_payment_done(bot: Bot, user_id: int, amount, lang: str = "en") -> None:
    text = t("notif_payment_done", lang, amount=amount)
    await send_notification(bot, user_id, NotificationType.PAYMENT_COMPLETED, text)


async def notify_referral_qualified(
    bot: Bot, referrer_id: int, referred_name: str, bonus, lang: str = "en"
) -> None:
    text = t("notif_referral_qualified", lang, name=referred_name, bonus=bonus)
    await send_notification(bot, referrer_id, NotificationType.REFERRAL_QUALIFIED, text)


async def notify_new_campaign(bot: Bot, user_id: int, amount, lang: str = "en") -> None:
    text = t("notif_new_campaign", lang, amount=amount)
    await send_notification(bot, user_id, NotificationType.NEW_CAMPAIGN, text)


async def alert_admins(bot: Bot, message: str) -> None:
    """Send alert to all configured admin IDs."""
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, f"🚨 <b>ADMIN ALERT</b>\n\n{message}", parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Could not alert admin {admin_id}: {e}")
        await asyncio.sleep(0.05)


async def broadcast_to_segment(
    bot: Bot,
    segment: str,
    text: str,
    media_file_id: Optional[str] = None,
    media_type: Optional[str] = None,
    reply_markup=None,
) -> dict:
    """
    Broadcast to a segment. Rate-limited to respect Telegram flood limits.
    segments: all | active | completed | pending_withdrawal | referral_leaders
    """
    from sqlalchemy import select
    from database.models import Withdrawal, WithdrawalStatus, Referral

    async with AsyncSessionLocal() as session:
        if segment == "all":
            result = await session.execute(select(User.id).where(User.is_active == True))
        elif segment == "active":
            from datetime import datetime, timezone, timedelta
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            result = await session.execute(
                select(User.id).where(User.last_activity >= cutoff, User.is_active == True)
            )
        elif segment == "completed":
            from database.models import TaskCompletion
            result = await session.execute(
                select(TaskCompletion.user_id).distinct()
            )
        elif segment == "pending_withdrawal":
            result = await session.execute(
                select(Withdrawal.user_id).where(Withdrawal.status == WithdrawalStatus.PENDING).distinct()
            )
        else:
            result = await session.execute(select(User.id).where(User.is_active == True))

        user_ids = [row[0] for row in result.all()]

    sent = 0
    failed = 0

    for uid in user_ids:
        try:
            if media_file_id and media_type == "photo":
                await bot.send_photo(uid, media_file_id, caption=text, parse_mode="HTML", reply_markup=reply_markup)
            elif media_file_id and media_type == "video":
                await bot.send_video(uid, media_file_id, caption=text, parse_mode="HTML", reply_markup=reply_markup)
            else:
                await bot.send_message(uid, text, parse_mode="HTML", reply_markup=reply_markup)
            sent += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        except Exception:
            failed += 1

        # Flood protection: 30 messages per second max
        await asyncio.sleep(1 / 25)

    return {"sent": sent, "failed": failed, "total": len(user_ids)}
