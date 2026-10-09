"""
ABUTAHUNT — Stats + Notifications handlers
Prepared by Abuta (@abuta_art)
"""

from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, TaskCompletion, UserBadge, Badge
from locales.strings import t
from services.wallet_service import get_wallet

router = Router()


@router.callback_query(F.data == "stats")
async def cb_stats(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    wallet = await get_wallet(session, user.id)

    completions_result = await session.execute(
        select(func.count()).where(TaskCompletion.user_id == user.id)
    )
    campaign_count = completions_result.scalar() or 0

    badges_result = await session.execute(
        select(func.count()).where(UserBadge.user_id == user.id)
    )
    badge_count = badges_result.scalar() or 0

    referrals_result = await session.execute(
        select(func.count()).where(
            __import__("database.models", fromlist=["Referral"]).Referral.referrer_id == user.id
        )
    )
    referral_count = referrals_result.scalar() or 0

    since = user.created_at.strftime("%Y-%m-%d") if user.created_at else "N/A"

    text = t("stats_header", lang,
        since=since,
        campaigns=campaign_count,
        earned=wallet.total_earned if wallet else 0,
        withdrawn=wallet.total_withdrawn if wallet else 0,
        referrals=referral_count,
        streak=user.streak_days,
        badges=badge_count,
        risk=user.risk_score,
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("back_btn", lang), callback_data="main_menu")]
    ])
    await cq.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await cq.answer()
