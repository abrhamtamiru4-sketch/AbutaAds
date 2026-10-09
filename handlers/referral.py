"""
ABUTAHUNT — Referral Handler
Prepared by Abuta (@abuta_art)
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from locales.strings import t
from services.referral_service import get_referral_stats

router = Router()


@router.callback_query(F.data == "referral")
async def cb_referral(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    from config import settings
    stats = await get_referral_stats(session, user.id)

    text = t("referral_header", lang,
        bonus=settings.DEFAULT_REFERRAL_REWARD,
        link=stats.get("link", ""),
        total=stats.get("total", 0),
        qualified=stats.get("qualified", 0),
        pending=stats.get("pending", 0),
        earnings=stats.get("earnings", 0),
        rate=stats.get("rate", 0.0),
    )

    share_text = f"🚀 Join ABUTAHUNT and earn ETB rewards!\n{stats.get('link', '')}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("share_btn", lang), switch_inline_query=share_text)],
        [InlineKeyboardButton(text=t("back_btn", lang), callback_data="main_menu")],
    ])
    await cq.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await cq.answer()
