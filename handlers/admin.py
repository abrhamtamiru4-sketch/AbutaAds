"""
ABUTAHUNT — Admin Panel Handler
Prepared by Abuta (@abuta_art)
"""

from decimal import Decimal
from datetime import datetime, timezone

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
)
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    User, Campaign, TaskCompletion, Withdrawal, WithdrawalStatus,
    RewardStatus, SupportTicket, TicketStatus, FraudEvent, Broadcast
)
from locales.strings import t
from services.analytics_service import get_daily_report, get_global_stats
from services.wallet_service import approve_withdrawal, reject_withdrawal, get_pending_withdrawals
from services.campaign_service import (
    create_campaign, set_campaign_active, delete_campaign, get_active_campaigns
)
from services.notification_service import (
    notify_reward_approved, notify_reward_rejected, notify_payment_done,
    alert_admins, broadcast_to_segment
)
from services.fraud_service import get_fraud_alerts, resolve_fraud_event
from config import settings

router = Router()


def is_admin(user: User) -> bool:
    return user.is_admin or user.id in settings.ADMIN_IDS


def admin_check(user: User) -> bool:
    return is_admin(user)


def admin_main_kb(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("admin_campaigns_btn", lang), callback_data="adm_campaigns"),
            InlineKeyboardButton(text=t("admin_users_btn", lang), callback_data="adm_users"),
        ],
        [
            InlineKeyboardButton(text=t("admin_payments_btn", lang), callback_data="adm_payments"),
            InlineKeyboardButton(text=t("admin_broadcast_btn", lang), callback_data="adm_broadcast"),
        ],
        [
            InlineKeyboardButton(text=t("admin_stats_btn", lang), callback_data="adm_stats"),
            InlineKeyboardButton(text=t("admin_fraud_btn", lang), callback_data="adm_fraud"),
        ],
        [
            InlineKeyboardButton(text=t("admin_settings_btn", lang), callback_data="adm_settings"),
        ],
    ])


# ── ENTRY ───────────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, user: User, lang: str):
    if not is_admin(user):
        await message.answer(t("error_not_admin", lang))
        return
    await message.answer(t("admin_panel", lang), reply_markup=admin_main_kb(lang), parse_mode="HTML")


@router.callback_query(F.data == "adm_main")
async def cb_adm_main(cq: CallbackQuery, user: User, lang: str):
    if not is_admin(user):
        await cq.answer(t("error_not_admin", lang), show_alert=True)
        return
    await cq.message.edit_text(t("admin_panel", lang), reply_markup=admin_main_kb(lang), parse_mode="HTML")
    await cq.answer()


# ── ANALYTICS ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_stats")
async def cb_adm_stats(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    if not is_admin(user):
        await cq.answer(t("error_not_admin", lang), show_alert=True)
        return

    daily = await get_daily_report(session)
    global_s = await get_global_stats(session)

    text = (
        f"📊 <b>DAILY ABUTAHUNT REPORT</b>\n\n"
        f"👥 New Users: <b>{daily['new_users']}</b>\n"
        f"🎯 Completed Tasks: <b>{daily['completions']}</b>\n"
        f"💰 Rewards Issued: <b>{daily['rewards_issued']:,.2f} ETB</b>\n"
        f"💸 Paid Withdrawals: <b>{daily['paid_withdrawals']:,.2f} ETB</b>\n"
        f"👥 New Referrals: <b>{daily['new_referrals']}</b>\n"
        f"🚨 Fraud Alerts: <b>{daily['fraud_alerts']}</b>\n"
        f"📈 Conversion: <b>{daily['conversion']}%</b>\n\n"
        f"━━━ Global Stats ━━━\n"
        f"👤 Total Users: <b>{global_s['total_users']:,}</b>\n"
        f"✅ Total Completions: <b>{global_s['total_completions']:,}</b>\n"
        f"💰 Total Rewards: <b>{global_s['total_rewards']:,.2f} ETB</b>\n"
        f"💸 Total Paid: <b>{global_s['total_paid']:,.2f} ETB</b>\n"
        f"⏳ Pending Payouts: <b>{global_s['pending_payouts']:,.2f} ETB</b>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data="adm_main")]
    ])
    await cq.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await cq.answer()


# ── PAYMENTS ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_payments")
async def cb_adm_payments(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    if not is_admin(user):
        await cq.answer(t("error_not_admin", lang), show_alert=True)
        return

    withdrawals = await get_pending_withdrawals(session)
    if not withdrawals:
        text = "💸 <b>Payments</b>\n\n✅ No pending withdrawals."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back", callback_data="adm_main")]
        ])
        await cq.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await cq.answer()
        return

    text = f"💸 <b>Pending Withdrawals ({len(withdrawals)})</b>\n\n"
    buttons = []
    for w in withdrawals[:10]:
        text += f"#{w.id} — User {w.user_id} — <b>{w.amount} ETB</b> — {w.payment_method_id}\n"
        buttons.append([
            InlineKeyboardButton(text=f"✅ Approve #{w.id}", callback_data=f"adm_pay_approve_{w.id}"),
            InlineKeyboardButton(text=f"❌ Reject #{w.id}", callback_data=f"adm_pay_reject_{w.id}"),
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="adm_main")])

    await cq.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML"
    )
    await cq.answer()


@router.callback_query(F.data.startswith("adm_pay_approve_"))
async def cb_approve_payment(
    cq: CallbackQuery, user: User, lang: str, session: AsyncSession, bot: Bot
):
    if not is_admin(user):
        await cq.answer(t("error_not_admin", lang), show_alert=True)
        return

    w_id = int(cq.data.split("_")[-1])
    withdrawal = await approve_withdrawal(session, w_id, user.id)
    if withdrawal:
        target_user = await session.get(User, withdrawal.user_id)
        if target_user:
            await notify_payment_done(bot, target_user.id, withdrawal.amount, target_user.language_code)
        await cq.answer(f"✅ Withdrawal #{w_id} approved.", show_alert=True)
    else:
        await cq.answer("❌ Could not approve. Already processed?", show_alert=True)

    await cb_adm_payments(cq, user, lang, session)


@router.callback_query(F.data.startswith("adm_pay_reject_"))
async def cb_reject_payment(
    cq: CallbackQuery, user: User, lang: str, session: AsyncSession, bot: Bot
):
    if not is_admin(user):
        await cq.answer(t("error_not_admin", lang), show_alert=True)
        return

    w_id = int(cq.data.split("_")[-1])
    withdrawal = await reject_withdrawal(session, w_id, user.id, "Rejected by admin")
    if withdrawal:
        target_user = await session.get(User, withdrawal.user_id)
        if target_user:
            await notify_reward_rejected(bot, target_user.id, "Payment rejected by admin", target_user.language_code)
        await cq.answer(f"❌ Withdrawal #{w_id} rejected and refunded.", show_alert=True)
    else:
        await cq.answer("Could not reject.", show_alert=True)

    await cb_adm_payments(cq, user, lang, session)


# ── CAMPAIGNS ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_campaigns")
async def cb_adm_campaigns(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    if not is_admin(user):
        await cq.answer(t("error_not_admin", lang), show_alert=True)
        return

    result = await session.execute(
        select(Campaign).where(Campaign.is_deleted == False).order_by(Campaign.id.desc()).limit(10)
    )
    campaigns = result.scalars().all()

    text = "📢 <b>Campaign Management</b>\n\n"
    buttons = []
    for c in campaigns:
        status = "🟢" if c.is_active else "🔴"
        text += f"{status} #{c.id} — {c.title} — {c.reward_amount} ETB\n"
        toggle_action = "pause" if c.is_active else "activate"
        toggle_label = "⏸ Pause" if c.is_active else "▶️ Activate"
        buttons.append([
            InlineKeyboardButton(text=toggle_label, callback_data=f"adm_camp_{toggle_action}_{c.id}"),
            InlineKeyboardButton(text="🗑 Delete", callback_data=f"adm_camp_delete_{c.id}"),
        ])

    buttons.append([InlineKeyboardButton(text="➕ New Campaign", callback_data="adm_camp_new")])
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="adm_main")])

    await cq.message.edit_text(
        text or "No campaigns.", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML"
    )
    await cq.answer()


@router.callback_query(F.data.startswith("adm_camp_activate_"))
async def cb_camp_activate(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    if not is_admin(user):
        return
    cid = int(cq.data.split("_")[-1])
    await set_campaign_active(session, cid, True)
    await cq.answer("✅ Campaign activated.", show_alert=False)
    await cb_adm_campaigns(cq, user, lang, session)


@router.callback_query(F.data.startswith("adm_camp_pause_"))
async def cb_camp_pause(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    if not is_admin(user):
        return
    cid = int(cq.data.split("_")[-1])
    await set_campaign_active(session, cid, False)
    await cq.answer("⏸ Campaign paused.", show_alert=False)
    await cb_adm_campaigns(cq, user, lang, session)


@router.callback_query(F.data.startswith("adm_camp_delete_"))
async def cb_camp_delete(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    if not is_admin(user):
        return
    cid = int(cq.data.split("_")[-1])
    await delete_campaign(session, cid)
    await cq.answer("🗑 Campaign deleted.", show_alert=True)
    await cb_adm_campaigns(cq, user, lang, session)


# ── FRAUD ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_fraud")
async def cb_adm_fraud(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    if not is_admin(user):
        await cq.answer(t("error_not_admin", lang), show_alert=True)
        return

    alerts = await get_fraud_alerts(session, resolved=False)
    text = f"🚨 <b>Fraud Alerts ({len(alerts)} open)</b>\n\n"

    buttons = []
    for alert in alerts[:10]:
        text += (
            f"⚠️ User {alert.user_id} — <b>{alert.risk_level}</b>\n"
            f"   {alert.event_type}: {(alert.details or '')[:60]}\n"
            f"   {alert.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        )
        buttons.append([
            InlineKeyboardButton(text=f"✅ Resolve #{alert.id}", callback_data=f"adm_fraud_resolve_{alert.id}"),
            InlineKeyboardButton(text=f"🚫 Suspend User", callback_data=f"adm_suspend_{alert.user_id}"),
        ])

    if not alerts:
        text += "✅ No open fraud alerts."

    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="adm_main")])
    await cq.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML"
    )
    await cq.answer()


@router.callback_query(F.data.startswith("adm_fraud_resolve_"))
async def cb_resolve_fraud(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    if not is_admin(user):
        return
    eid = int(cq.data.split("_")[-1])
    await resolve_fraud_event(session, eid)
    await cq.answer("✅ Fraud event resolved.", show_alert=False)
    await cb_adm_fraud(cq, user, lang, session)


@router.callback_query(F.data.startswith("adm_suspend_"))
async def cb_suspend_user(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    if not is_admin(user):
        return
    uid = int(cq.data.split("_")[-1])
    from services.user_service import suspend_user
    await suspend_user(session, uid, user.id)
    await cq.answer(f"🚫 User {uid} suspended.", show_alert=True)


# ── BROADCAST ────────────────────────────────────────────────────────────────

class BroadcastFSM(StatesGroup):
    choosing_segment = State()
    entering_text = State()


@router.callback_query(F.data == "adm_broadcast")
async def cb_adm_broadcast(cq: CallbackQuery, user: User, lang: str, state: FSMContext):
    if not is_admin(user):
        await cq.answer(t("error_not_admin", lang), show_alert=True)
        return

    segments = ["all", "active", "completed", "pending_withdrawal"]
    buttons = [
        [InlineKeyboardButton(text=f"📡 {s.replace('_', ' ').title()}", callback_data=f"adm_bc_seg_{s}")]
        for s in segments
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="adm_main")])

    await cq.message.edit_text(
        "📡 <b>Broadcast</b>\n\nSelect target segment:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await state.set_state(BroadcastFSM.choosing_segment)
    await cq.answer()


@router.callback_query(F.data.startswith("adm_bc_seg_"), BroadcastFSM.choosing_segment)
async def cb_bc_segment(cq: CallbackQuery, user: User, lang: str, state: FSMContext):
    segment = cq.data.split("adm_bc_seg_", 1)[1]
    await state.update_data(segment=segment)
    await cq.message.edit_text(
        f"📡 Broadcasting to: <b>{segment}</b>\n\nEnter the message text:",
        parse_mode="HTML"
    )
    await state.set_state(BroadcastFSM.entering_text)
    await cq.answer()


@router.message(BroadcastFSM.entering_text)
async def msg_bc_text(message: Message, user: User, lang: str, state: FSMContext, bot: Bot):
    if not is_admin(user):
        return

    data = await state.get_data()
    segment = data.get("segment", "all")
    text = message.text or ""
    await state.clear()

    await message.answer(f"⏳ Broadcasting to segment: <b>{segment}</b>...", parse_mode="HTML")
    result = await broadcast_to_segment(bot, segment, text)
    await message.answer(
        f"✅ Broadcast complete!\nSent: {result['sent']}\nFailed: {result['failed']}\nTotal: {result['total']}"
    )


# ── USER MANAGEMENT ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_users")
async def cb_adm_users(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    if not is_admin(user):
        await cq.answer(t("error_not_admin", lang), show_alert=True)
        return

    result = await session.execute(
        select(User).order_by(User.created_at.desc()).limit(10)
    )
    users = result.scalars().all()

    text = "👤 <b>Recent Users</b>\n\n"
    buttons = []
    for u in users:
        status = "🚫" if u.is_suspended else "✅"
        text += f"{status} {u.id} — {u.first_name} (@{u.username or 'N/A'}) — {u.risk_score}\n"
        buttons.append([
            InlineKeyboardButton(
                text=f"{'Unsuspend' if u.is_suspended else 'Suspend'} {u.id}",
                callback_data=f"{'adm_unsuspend' if u.is_suspended else 'adm_suspend'}_{u.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="adm_main")])
    await cq.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML"
    )
    await cq.answer()


@router.callback_query(F.data.startswith("adm_unsuspend_"))
async def cb_unsuspend_user(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    if not is_admin(user):
        return
    uid = int(cq.data.split("_")[-1])
    from services.user_service import unsuspend_user
    await unsuspend_user(session, uid)
    await cq.answer(f"✅ User {uid} unsuspended.", show_alert=True)
    await cb_adm_users(cq, user, lang, session)


# ── SETTINGS ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_settings")
async def cb_adm_settings(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    if not is_admin(user):
        await cq.answer(t("error_not_admin", lang), show_alert=True)
        return

    from database.models import SystemSetting
    result = await session.execute(select(SystemSetting).limit(20))
    settings_list = result.scalars().all()

    text = "⚙️ <b>System Settings</b>\n\n"
    for s in settings_list:
        text += f"<code>{s.key}</code>: {s.value}\n"

    if not settings_list:
        text += "No settings configured yet."

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data="adm_main")]
    ])
    await cq.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await cq.answer()
