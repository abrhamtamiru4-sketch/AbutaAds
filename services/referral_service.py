"""
ABUTAHUNT — Referral Service
Prepared by Abuta (@abuta_art)
"""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Referral, User, Milestone, UserBadge, Badge, TaskCompletion, RewardStatus
from services.wallet_service import credit_wallet
from config import settings


async def qualify_referral(
    session: AsyncSession,
    referred_user_id: int,
) -> Optional[dict]:
    """
    Called when a referred user completes their first campaign.
    Awards referral bonus to referrer. Idempotent.
    """
    # Find referral record
    result = await session.execute(
        select(Referral).where(Referral.referred_id == referred_user_id)
    )
    referral = result.scalar_one_or_none()
    if not referral or referral.is_qualified or referral.reward_paid:
        return None

    # Check referred user completed at least one campaign
    completed = await session.execute(
        select(func.count()).where(
            TaskCompletion.user_id == referred_user_id,
            TaskCompletion.reward_status.in_([
                RewardStatus.APPROVED, RewardStatus.PAID
            ])
        )
    )
    if (completed.scalar() or 0) < 1:
        return None

    # Mark qualified
    referral.is_qualified = True
    referral.qualified_at = datetime.now(timezone.utc)
    referral.reward_paid = True

    bonus = Decimal(str(settings.DEFAULT_REFERRAL_REWARD))

    # Credit referrer
    await credit_wallet(
        session=session,
        user_id=referral.referrer_id,
        amount=bonus,
        tx_type="REFERRAL_BONUS",
        description=f"+{bonus} ETB — Referral Bonus",
        reference_id=referral.id,
        idempotency_key=f"referral_bonus_{referral.id}",
    )

    # Check milestones
    await _check_milestones(session, referral.referrer_id)

    await session.commit()

    # Get referred user info
    ref_user = await session.get(User, referred_user_id)
    return {
        "referrer_id": referral.referrer_id,
        "referred_name": ref_user.first_name if ref_user else "User",
        "bonus": bonus,
    }


async def get_referral_stats(session: AsyncSession, user_id: int) -> dict:
    user = await session.get(User, user_id)
    if not user:
        return {}

    stmt = select(Referral).where(Referral.referrer_id == user_id)
    result = await session.execute(stmt)
    referrals = result.scalars().all()

    total = len(referrals)
    qualified = sum(1 for r in referrals if r.is_qualified)
    pending = total - qualified

    # Earnings from referrals
    from sqlalchemy import and_
    from database.models import Transaction
    earnings_result = await session.execute(
        select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.tx_type == "REFERRAL_BONUS",
        )
    )
    earnings = earnings_result.scalar() or Decimal("0")
    rate = round((qualified / total * 100), 1) if total > 0 else 0.0

    return {
        "total": total,
        "qualified": qualified,
        "pending": pending,
        "earnings": earnings,
        "rate": rate,
        "link": f"https://t.me/{settings.BOT_USERNAME}?start={user.referral_code}",
    }


async def _check_milestones(session: AsyncSession, user_id: int) -> None:
    """Award milestone bonuses for referral counts."""
    qual_count_result = await session.execute(
        select(func.count()).where(
            Referral.referrer_id == user_id,
            Referral.is_qualified == True,
        )
    )
    qual_count = qual_count_result.scalar() or 0

    milestones_result = await session.execute(
        select(Milestone).where(
            Milestone.is_active == True,
            Milestone.referral_count <= qual_count,
        )
    )
    milestones = milestones_result.scalars().all()

    for milestone in milestones:
        idem_key = f"milestone_{user_id}_{milestone.id}"
        # Check not already awarded
        from database.models import Transaction
        existing = await session.execute(
            select(Transaction).where(Transaction.idempotency_key == idem_key)
        )
        if existing.scalar_one_or_none():
            continue
        await credit_wallet(
            session=session,
            user_id=user_id,
            amount=milestone.bonus_amount,
            tx_type="MILESTONE_BONUS",
            description=f"+{milestone.bonus_amount} ETB — Milestone: {milestone.name}",
            idempotency_key=idem_key,
        )


async def create_referral_record(
    session: AsyncSession, referrer_id: int, referred_id: int
) -> Optional[Referral]:
    """Record new referral. Prevents self-referral and duplicates via DB constraints."""
    if referrer_id == referred_id:
        return None

    existing = await session.execute(
        select(Referral).where(Referral.referred_id == referred_id)
    )
    if existing.scalar_one_or_none():
        return None

    referral = Referral(referrer_id=referrer_id, referred_id=referred_id)
    session.add(referral)
    try:
        await session.commit()
        return referral
    except Exception:
        await session.rollback()
        return None
