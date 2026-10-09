"""
ABUTAHUNT — Tasks & Campaign Handler
Prepared by Abuta (@abuta_art)
"""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from locales.strings import t
from services.campaign_service import (
    get_active_campaigns, get_campaign_stats, verify_and_complete_campaign,
    get_user_completion, get_user_completions
)
from services.notification_service import alert_admins
from config import settings

router = Router()


def back_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("back_btn", lang), callback_data="main_menu")]
    ])


@router.callback_query(F.data == "earn")
async def cb_earn(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    campaigns = await get_active_campaigns(session)
    if not campaigns:
        await cq.message.edit_text(
            "🎯 No active campaigns right now. Check back soon!",
            reply_markup=back_kb(lang),
        )
        await cq.answer()
        return

    # Show first active campaign
    campaign = campaigns[0]
    stats = await get_campaign_stats(session, campaign)
    existing = await get_user_completion(session, user.id, campaign.id)

    # Build task rows
    task_lines = []
    for task in sorted(campaign.tasks, key=lambda t: t.sort_order):
        icon = t("task_complete", lang) if existing else t("task_incomplete", lang)
        label = t("task_join", lang)
        task_lines.append(f"{icon} {label} <a href='{task.target_url}'>{task.title}</a>")

    status_text = t("campaign_status_active", lang)
    remaining = stats["remaining"]
    remaining_display = f"{remaining:,}" if isinstance(remaining, int) else remaining

    text = (
        t("campaign_header", lang)
        + "\n".join(task_lines)
        + "\n\n"
        + t("reward_label", lang, amount=campaign.reward_amount)
        + "\n\n"
        + t("campaign_stats", lang,
            participants=stats["participants"],
            pool=float(stats["pool"]),
            remaining=remaining_display,
            status=status_text)
    )

    if existing:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("back_btn", lang), callback_data="main_menu")]
        ])
        await cq.message.edit_text(
            text + f"\n\n{t('already_completed', lang)}",
            reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=t("verify_btn", lang),
                callback_data=f"verify_{campaign.id}"
            )],
            [InlineKeyboardButton(text=t("back_btn", lang), callback_data="main_menu")],
        ])
        await cq.message.edit_text(
            text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True
        )
    await cq.answer()


@router.callback_query(F.data.startswith("verify_"))
async def cb_verify(cq: CallbackQuery, user: User, lang: str, session: AsyncSession, bot: Bot):
    campaign_id = int(cq.data.split("_", 1)[1])

    await cq.answer(t("verify_checking", lang), show_alert=False)
    await cq.message.edit_text(f"⏳ {t('verify_checking', lang)}", parse_mode="HTML")

    result = await verify_and_complete_campaign(
        session=session, bot=bot, user_id=user.id, campaign_id=campaign_id
    )

    kb = back_kb(lang)

    if result.get("ok"):
        amount = result["amount"]
        text = t("verify_success", lang, amount=amount)
        if result.get("manual_review"):
            text += "\n\n⚠️ Your submission is under manual review due to security checks."
            # Alert admins about high-risk submission
            await alert_admins(
                bot,
                f"⚠️ HIGH RISK CAMPAIGN CLAIM\nUser: {user.id} (@{user.username})\nCampaign: {campaign_id}"
            )
    elif result.get("missing"):
        missing_text = "\n".join(
            f"• <a href='{t.target_url}'>{t.title}</a>" for t in result["missing"]
        )
        text = t("verify_failed_channel", lang, missing=missing_text)
    else:
        error = result.get("error", "generic")
        if error == "already_completed":
            text = t("already_completed", lang)
        elif error == "campaign_ended":
            text = "❌ This campaign has ended."
        elif error == "claim_limit":
            text = "❌ Campaign claim limit reached."
        else:
            text = t("error_generic", lang)

    await cq.message.edit_text(text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)


@router.callback_query(F.data == "my_tasks")
async def cb_my_tasks(cq: CallbackQuery, user: User, lang: str, session: AsyncSession):
    completions = await get_user_completions(session, user.id)

    if not completions:
        text = "📋 <b>My Tasks</b>\n\nYou haven't completed any campaigns yet.\n\nPress 🎯 Earn 50 ETB to start!"
    else:
        lines = ["📋 <b>My Tasks</b>\n"]
        status_icons = {
            "PENDING": "⏳", "VERIFIED": "✅", "APPROVED": "💰",
            "PROCESSING": "🔄", "PAID": "🟢", "REJECTED": "❌", "CANCELLED": "🚫"
        }
        for c in completions[:10]:
            icon = status_icons.get(c.reward_status, "•")
            lines.append(
                f"{icon} <b>{c.campaign.title}</b>\n"
                f"   Status: {c.reward_status} | {c.created_at.strftime('%Y-%m-%d')}"
            )
        text = "\n".join(lines)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 New Campaign", callback_data="earn")],
        [InlineKeyboardButton(text=t("back_btn", lang), callback_data="main_menu")],
    ])
    await cq.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await cq.answer()
