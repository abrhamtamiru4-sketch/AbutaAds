"""
ABUTAHUNT — Analytics Service
All stats from real DB queries only.
Prepared by Abuta (@abuta_art)
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    User, TaskCompletion, Transaction, Withdrawal,
    Referral, FraudEvent, RewardStatus, WithdrawalStatus, TransactionType
)


async def get_daily_report(session: AsyncSession) -> dict:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    new_users = await session.execute(
        select(func.count()).where(User.created_at >= today_start)
    )
    completions = await session.execute(
        select(func.count()).where(TaskCompletion.created_at >= today_start)
    )
    rewards_sum = await session.execute(
        select(func.sum(Transaction.amount)).where(
            Transaction.created_at >= today_start,
            Transaction.tx_type == TransactionType.CAMPAIGN_REWARD,
            Transaction.amount > 0,
        )
    )
    paid_sum = await session.execute(
        select(func.sum(Withdrawal.amount)).where(
            Withdrawal.created_at >= today_start,
            Withdrawal.status == WithdrawalStatus.COMPLETED,
        )
    )
    new_referrals = await session.execute(
        select(func.count()).where(Referral.created_at >= today_start)
    )
    fraud_alerts = await session.execute(
        select(func.count()).where(
            FraudEvent.created_at >= today_start,
            FraudEvent.resolved == False,
        )
    )

    c_total = completions.scalar() or 0
    new_u = new_users.scalar() or 0

    return {
        "new_users": new_u,
        "completions": c_total,
        "rewards_issued": rewards_sum.scalar() or Decimal("0"),
        "paid_withdrawals": paid_sum.scalar() or Decimal("0"),
        "new_referrals": new_referrals.scalar() or 0,
        "fraud_alerts": fraud_alerts.scalar() or 0,
        "conversion": round(c_total / new_u * 100, 1) if new_u > 0 else 0.0,
    }


async def get_global_stats(session: AsyncSession) -> dict:
    total_users = await session.execute(select(func.count(User.id)))
    active_users = await session.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    total_completions = await session.execute(select(func.count(TaskCompletion.id)))
    total_paid = await session.execute(
        select(func.sum(Withdrawal.amount)).where(Withdrawal.status == WithdrawalStatus.COMPLETED)
    )
    pending_payouts = await session.execute(
        select(func.sum(Withdrawal.amount)).where(Withdrawal.status == WithdrawalStatus.PENDING)
    )
    total_rewards = await session.execute(
        select(func.sum(Transaction.amount)).where(
            Transaction.tx_type == TransactionType.CAMPAIGN_REWARD,
            Transaction.amount > 0,
        )
    )

    return {
        "total_users": total_users.scalar() or 0,
        "active_users": active_users.scalar() or 0,
        "total_completions": total_completions.scalar() or 0,
        "total_rewards": total_rewards.scalar() or Decimal("0"),
        "total_paid": total_paid.scalar() or Decimal("0"),
        "pending_payouts": pending_payouts.scalar() or Decimal("0"),
    }


async def get_leaderboard(
    session: AsyncSession,
    board_type: str = "top_earners",
    period: str = "all_time",
    limit: int = 10,
) -> list[dict]:
    """
    board_type: top_earners | top_referrers | most_active
    period: daily | weekly | monthly | all_time
    """
    now = datetime.now(timezone.utc)
    if period == "daily":
        since = now - timedelta(days=1)
    elif period == "weekly":
        since = now - timedelta(weeks=1)
    elif period == "monthly":
        since = now - timedelta(days=30)
    else:
        since = None

    rows = []

    if board_type == "top_earners":
        q = (
            select(
                Transaction.user_id,
                func.sum(Transaction.amount).label("total"),
            )
            .where(Transaction.tx_type == TransactionType.CAMPAIGN_REWARD, Transaction.amount > 0)
        )
        if since:
            q = q.where(Transaction.created_at >= since)
        q = q.group_by(Transaction.user_id).order_by(func.sum(Transaction.amount).desc()).limit(limit)
        result = await session.execute(q)
        for uid, total in result.all():
            user = await session.get(User, uid)
            name = "🕶 Hidden" if (user and user.hide_public_name) else (user.first_name if user else "Unknown")
            rows.append({"name": name, "value": total, "label": "ETB"})

    elif board_type == "top_referrers":
        q = (
            select(Referral.referrer_id, func.count(Referral.id).label("cnt"))
            .where(Referral.is_qualified == True)
        )
        if since:
            q = q.where(Referral.qualified_at >= since)
        q = q.group_by(Referral.referrer_id).order_by(func.count(Referral.id).desc()).limit(limit)
        result = await session.execute(q)
        for uid, cnt in result.all():
            user = await session.get(User, uid)
            name = "🕶 Hidden" if (user and user.hide_public_name) else (user.first_name if user else "Unknown")
            rows.append({"name": name, "value": cnt, "label": "refs"})

    elif board_type == "most_active":
        q = (
            select(TaskCompletion.user_id, func.count(TaskCompletion.id).label("cnt"))
        )
        if since:
            q = q.where(TaskCompletion.created_at >= since)
        q = q.group_by(TaskCompletion.user_id).order_by(func.count(TaskCompletion.id).desc()).limit(limit)
        result = await session.execute(q)
        for uid, cnt in result.all():
            user = await session.get(User, uid)
            name = "🕶 Hidden" if (user and user.hide_public_name) else (user.first_name if user else "Unknown")
            rows.append({"name": name, "value": cnt, "label": "tasks"})

    return rows
