"""
ABUTAHUNT — Wallet, Balance & Withdrawal Handler
Prepared by Abuta (@abuta_art)
"""

from decimal import Decimal, InvalidOperation

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
)
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from locales.strings import t
from services.wallet_service import (
    get_wallet, get_active_payment_methods, create_withdrawal_request,
    get_user_transactions
)
from services.notification_service import alert_admins
from config import settings

router = Router()


class WithdrawFSM(StatesGroup):
    choosing_method = State()
    entering_amount = State()
    entering_info = State()
    confirming = State()


def back_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("back_btn", lang), callback_data="main_menu")]
    ])


@router.callback_query(F.data == "balance")
async def cb_balance(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    wallet = await get_wallet(session, user.id)
    if not wallet:
        await cq.answer("Wallet not found.", show_alert=True)
        return

    txs = await get_user_transactions(session, user.id, limit=5)
    text = t("balance_header", lang,
        balance=wallet.balance,
        pending=wallet.pending_balance,
        total_earned=wallet.total_earned,
        total_withdrawn=wallet.total_withdrawn,
    )

    if txs:
        text += "\n\n📜 <b>Recent Transactions:</b>"
        for tx in txs:
            sign = "+" if tx.amount > 0 else ""
            text += f"\n{sign}{tx.amount} ETB — {tx.description[:40]}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("withdraw_btn", lang), callback_data="withdraw")],
        [InlineKeyboardButton(text=t("back_btn", lang), callback_data="main_menu")],
    ])
    await cq.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await cq.answer()


@router.callback_query(F.data == "withdraw")
async def cb_withdraw_start(
    cq: CallbackQuery, user: User, lang: str, session: AsyncSession, state: FSMContext
):
    wallet = await get_wallet(session, user.id)
    if not wallet:
        await cq.answer("Wallet not found.", show_alert=True)
        return

    methods = await get_active_payment_methods(session)
    if not methods:
        await cq.message.edit_text(
            "⚠️ No payment methods available. Contact support.",
            reply_markup=back_kb(lang)
        )
        await cq.answer()
        return

    text = t("withdraw_header", lang,
        balance=wallet.balance,
        min_amount=settings.MIN_WITHDRAWAL
    )
    buttons = [[
        InlineKeyboardButton(text=m.name, callback_data=f"wm_{m.id}")
    ] for m in methods]
    buttons.append([InlineKeyboardButton(text=t("back_btn", lang), callback_data="main_menu")])

    await cq.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
    await state.set_state(WithdrawFSM.choosing_method)
    await cq.answer()


@router.callback_query(F.data.startswith("wm_"), WithdrawFSM.choosing_method)
async def cb_choose_method(
    cq: CallbackQuery, user: User, lang: str, session: AsyncSession, state: FSMContext
):
    method_id = int(cq.data.split("_", 1)[1])
    from database.models import PaymentMethod
    method = await session.get(PaymentMethod, method_id)
    if not method:
        await cq.answer("Method not found.", show_alert=True)
        return

    await state.update_data(method_id=method_id, method_name=method.name)
    await cq.message.edit_text(t("withdraw_enter_amount", lang), parse_mode="HTML")
    await state.set_state(WithdrawFSM.entering_amount)
    await cq.answer()


@router.message(WithdrawFSM.entering_amount)
async def msg_withdraw_amount(
    message: Message, user: User, lang: str, session: AsyncSession, state: FSMContext
):
    try:
        amount = Decimal(message.text.strip().replace(",", "."))
    except InvalidOperation:
        await message.answer(t("withdraw_invalid_amount", lang))
        return

    wallet = await get_wallet(session, user.id)
    if wallet.balance < amount:
        await message.answer(t("withdraw_insufficient", lang, balance=wallet.balance))
        return
    if amount < Decimal(str(settings.MIN_WITHDRAWAL)):
        await message.answer(t("withdraw_below_min", lang, min=settings.MIN_WITHDRAWAL))
        return

    data = await state.get_data()
    await state.update_data(amount=str(amount))
    await message.answer(
        t("withdraw_enter_info", lang, method=data["method_name"]),
        parse_mode="HTML"
    )
    await state.set_state(WithdrawFSM.entering_info)


@router.message(WithdrawFSM.entering_info)
async def msg_withdraw_info(
    message: Message, user: User, lang: str, state: FSMContext
):
    payment_info = message.text.strip()
    if len(payment_info) < 5:
        await message.answer("❌ Please enter a valid account number.")
        return

    await state.update_data(payment_info=payment_info)
    data = await state.get_data()

    # Mask info for display
    masked = payment_info[:3] + "****" + payment_info[-2:] if len(payment_info) > 5 else "****"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("confirm_btn", lang), callback_data="withdraw_confirm")],
        [InlineKeyboardButton(text=t("cancel_btn", lang), callback_data="main_menu")],
    ])
    await message.answer(
        t("withdraw_confirm", lang,
            amount=data["amount"],
            method=data["method_name"],
            info=masked
        ),
        reply_markup=kb, parse_mode="HTML"
    )
    await state.set_state(WithdrawFSM.confirming)


@router.callback_query(F.data == "withdraw_confirm", WithdrawFSM.confirming)
async def cb_withdraw_confirm(
    cq: CallbackQuery, user: User, lang: str, session: AsyncSession, state: FSMContext, bot: Bot
):
    data = await state.get_data()
    result = await create_withdrawal_request(
        session=session,
        user_id=user.id,
        amount=Decimal(data["amount"]),
        payment_method_id=data["method_id"],
        payment_info=data["payment_info"],
    )

    await state.clear()

    if result["ok"]:
        w = result["withdrawal"]
        await cq.message.edit_text(
            t("withdraw_submitted", lang, amount=w.amount, method=data["method_name"]),
            reply_markup=back_kb(lang), parse_mode="HTML"
        )
        # Notify admins
        await alert_admins(
            bot,
            f"💸 <b>New Withdrawal Request</b>\n"
            f"User: {user.id} (@{user.username or 'N/A'})\n"
            f"Amount: {w.amount} ETB\n"
            f"Method: {data['method_name']}\n"
            f"Withdrawal ID: #{w.id}"
        )
    else:
        error = result.get("error", "generic")
        if error == "below_min":
            text = t("withdraw_below_min", lang, min=settings.MIN_WITHDRAWAL)
        elif error == "insufficient":
            wallet = await get_wallet(session, user.id)
            text = t("withdraw_insufficient", lang, balance=wallet.balance if wallet else 0)
        elif error == "daily_limit":
            text = t("withdraw_daily_limit", lang)
        else:
            text = t("error_generic", lang)
        await cq.message.edit_text(text, reply_markup=back_kb(lang), parse_mode="HTML")

    await cq.answer()
