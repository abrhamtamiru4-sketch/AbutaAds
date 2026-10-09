"""
ABUTAHUNT — Leaderboard Handler
Prepared by Abuta (@abuta_art)
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from locales.strings import t
from services.analytics_service import get_leaderboard

router = Router()

MEDALS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


def lb_kb(board_type: str, period: str, lang: str) -> InlineKeyboardMarkup:
    boards = [("top_earners", "💰"), ("top_referrers", "👥"), ("most_active", "🔥")]
    periods = [("daily", "D"), ("weekly", "W"), ("monthly", "M"), ("all_time", "∞")]

    board_row = [
        InlineKeyboardButton(
            text=f"{'▶ ' if b == board_type else ''}{emoji}",
            callback_data=f"lb_{b}_{period}"
        )
        for b, emoji in boards
    ]
    period_row = [
        InlineKeyboardButton(
            text=f"{'▶ ' if p == period else ''}{label}",
            callback_data=f"lb_{board_type}_{p}"
        )
        for p, label in periods
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        board_row,
        period_row,
        [InlineKeyboardButton(text=t("back_btn", lang), callback_data="main_menu")],
    ])


@router.callback_query(F.data == "leaderboard")
async def cb_leaderboard(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    await _show_leaderboard(cq, "top_earners", "all_time", lang, session)


@router.callback_query(F.data.startswith("lb_"))
async def cb_lb_filter(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    parts = cq.data.split("_", 2)
    board_type = parts[1]
    period = parts[2]
    await _show_leaderboard(cq, board_type, period, lang, session)


async def _show_leaderboard(
    cq: CallbackQuery, board_type: str, period: str, lang: str, session: AsyncSession
):
    rows = await get_leaderboard(session, board_type, period, limit=10)

    period_label = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly", "all_time": "All Time"}.get(period, period)
    board_label = {"top_earners": t("top_earners", lang), "top_referrers": t("top_referrers", lang), "most_active": t("most_active", lang)}.get(board_type, board_type)

    lines = [f"🏆 <b>{board_label}</b> — {period_label}\n"]
    for i, row in enumerate(rows):
        medal = MEDALS[i] if i < len(MEDALS) else f"{i+1}."
        lines.append(f"{medal} <b>{row['name']}</b> — {row['value']} {row['label']}")

    if not rows:
        lines.append("No data yet. Be the first!")

    text = "\n".join(lines)
    await cq.message.edit_text(
        text, reply_markup=lb_kb(board_type, period, lang), parse_mode="HTML"
    )
    await cq.answer()
