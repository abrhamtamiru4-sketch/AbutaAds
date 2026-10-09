"""
ABUTAHUNT — Support Ticket Handler
Prepared by Abuta (@abuta_art)
"""

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User, SupportTicket, TicketStatus
from locales.strings import t
from services.notification_service import alert_admins

router = Router()


class SupportFSM(StatesGroup):
    entering_message = State()


def back_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("back_btn", lang), callback_data="main_menu")]
    ])


@router.callback_query(F.data == "support")
async def cb_support(cq: CallbackQuery, user: User, lang: str, session: AsyncSession, state: FSMContext):
    result = await session.execute(
        select(SupportTicket)
        .where(SupportTicket.user_id == user.id)
        .order_by(SupportTicket.created_at.desc())
        .limit(5)
    )
    tickets = result.scalars().all()

    text = "🆘 <b>Support</b>\n\n"
    if tickets:
        text += t("support_ticket_list", lang) + "\n"
        status_icons = {
            "OPEN": "🔓", "IN_PROGRESS": "🔄", "WAITING_USER": "⏳",
            "RESOLVED": "✅", "CLOSED": "🔒"
        }
        for ticket in tickets:
            icon = status_icons.get(ticket.status, "•")
            text += f"\n{icon} #{ticket.id} — {ticket.subject[:30]}\n"
            if ticket.admin_reply:
                text += f"   💬 Admin: {ticket.admin_reply[:50]}...\n"
        text += "\n"

    text += "Tap below to open a new ticket:"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ New Ticket", callback_data="support_new")],
        [InlineKeyboardButton(text=t("back_btn", lang), callback_data="main_menu")],
    ])
    await cq.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await cq.answer()


@router.callback_query(F.data == "support_new")
async def cb_support_new(cq: CallbackQuery, lang: str, state: FSMContext):
    await cq.message.edit_text(
        t("support_enter_message", lang),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("cancel_btn", lang), callback_data="support")]
        ])
    )
    await state.set_state(SupportFSM.entering_message)
    await cq.answer()


@router.message(SupportFSM.entering_message)
async def msg_support_message(
    message: Message, user: User, lang: str, session: AsyncSession, state: FSMContext, bot: Bot
):
    text = message.text.strip() if message.text else ""
    if len(text) < 10:
        await message.answer("❌ Message too short. Please describe your issue.")
        return

    subject = text[:50] + ("..." if len(text) > 50 else "")
    ticket = SupportTicket(
        user_id=user.id,
        subject=subject,
        message=text,
        status=TicketStatus.OPEN,
    )
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)

    await state.clear()

    await message.answer(
        t("support_submitted", lang, ticket_id=ticket.id),
        reply_markup=back_kb(lang),
        parse_mode="HTML"
    )

    await alert_admins(
        bot,
        f"🎫 <b>New Support Ticket #{ticket.id}</b>\n"
        f"User: {user.id} (@{user.username or 'N/A'})\n"
        f"Subject: {subject}\n"
        f"Message: {text[:200]}"
    )
