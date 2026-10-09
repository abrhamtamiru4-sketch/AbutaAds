"""
ABUTAHUNT — /start handler + main menu
Prepared by Abuta (@abuta_art)
"""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from locales.strings import t
from services.referral_service import create_referral_record

router = Router()


def main_menu_kb(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("earn_btn", lang), callback_data="earn"),
            InlineKeyboardButton(text=t("balance_btn", lang), callback_data="balance"),
        ],
        [
            InlineKeyboardButton(text=t("tasks_btn", lang), callback_data="my_tasks"),
            InlineKeyboardButton(text=t("invite_btn", lang), callback_data="referral"),
        ],
        [
            InlineKeyboardButton(text=t("withdraw_btn", lang), callback_data="withdraw"),
            InlineKeyboardButton(text=t("leaderboard_btn", lang), callback_data="leaderboard"),
        ],
        [
            InlineKeyboardButton(text=t("stats_btn", lang), callback_data="stats"),
            InlineKeyboardButton(text=t("help_btn", lang), callback_data="help"),
        ],
        [
            InlineKeyboardButton(text=t("support_btn", lang), callback_data="support"),
        ],
    ])


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    user: User,
    lang: str,
    session: AsyncSession,
    is_new_user: bool,
    state: FSMContext,
):
    await state.clear()

    # Handle referral deep link
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        referral_code = args[1].strip()
        referrer_result = await session.execute(
            __import__("sqlalchemy", fromlist=["select"]).select(User).where(
                User.referral_code == referral_code
            )
        )
        referrer = referrer_result.scalar_one_or_none()
        if referrer and referrer.id != user.id:
            await create_referral_record(session, referrer.id, user.id)

    await message.answer(
        t("welcome", lang),
        reply_markup=main_menu_kb(lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(cq: CallbackQuery, user: User, lang: str):
    await cq.message.edit_text(
        t("welcome", lang),
        reply_markup=main_menu_kb(lang),
        parse_mode="HTML",
    )
    await cq.answer()


@router.message(Command("help"))
@router.callback_query(F.data == "help")
async def cb_help(event, user: User, lang: str):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("back_btn", lang), callback_data="main_menu")]
    ])
    text = t("help_text", lang)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")
