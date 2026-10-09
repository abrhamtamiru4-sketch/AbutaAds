"""
ABUTAHUNT — Anti-Fraud Service
Risk scoring without invasive fingerprinting.
Prepared by Abuta (@abuta_art)
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    FraudEvent, FraudRisk, TaskCompletion, Referral,
    Withdrawal, WithdrawalStatus, User
)


async def evaluate_fraud_risk(
    session: AsyncSession,
    user_id: int,
    campaign_id: Optional[int] = None,
) -> FraudRisk:
    """
    Compute risk level from behavioral signals only.
    Returns LOW / MEDIUM / HIGH / CRITICAL.
    """
    score = 0
    reasons = []

    user = await session.get(User, user_id)
    if not user:
        return FraudRisk.CRITICAL

    # 1. Account age
    age = datetime.now(timezone.utc) - user.created_at.replace(tzinfo=timezone.utc)
    if age.days < 1:
        score += 30
        reasons.append("account_age_under_1d")
    elif age.days < 7:
        score += 10
        reasons.append("account_age_under_7d")

    # 2. Rapid task completions (> 3 campaigns in 1 hour)
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    rapid_result = await session.execute(
        select(func.count()).where(
            TaskCompletion.user_id == user_id,
            TaskCompletion.created_at >= one_hour_ago,
        )
    )
    rapid_count = rapid_result.scalar() or 0
    if rapid_count >= 3:
        score += 40
        reasons.append(f"rapid_completions_{rapid_count}_per_hour")

    # 3. Referral loop detection (referred user is the referrer's referrer)
    if user.referred_by_id:
        loop_result = await session.execute(
            select(Referral).where(
                Referral.referrer_id == user_id,
                Referral.referred_id == user.referred_by_id,
            )
        )
        if loop_result.scalar_one_or_none():
            score += 50
            reasons.append("referral_loop_detected")

    # 4. Referral farming (too many referrals from same tree in 24h)
    yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
    referrals_24h = await session.execute(
        select(func.count()).where(
            Referral.referrer_id == user_id,
            Referral.created_at >= yesterday,
        )
    )
    r24 = referrals_24h.scalar() or 0
    if r24 > 20:
        score += 35
        reasons.append(f"referral_farming_{r24}_in_24h")

    # 5. Repeated withdrawal attempts in short window
    w_result = await session.execute(
        select(func.count()).where(
            Withdrawal.user_id == user_id,
            Withdrawal.created_at >= yesterday,
            Withdrawal.status.not_in([WithdrawalStatus.CANCELLED])
        )
    )
    w_count = w_result.scalar() or 0
    if w_count >= 3:
        score += 20
        reasons.append(f"withdrawal_attempts_{w_count}_24h")

    # 6. Previous fraud events
    prev_fraud = await session.execute(
        select(func.count()).where(
            FraudEvent.user_id == user_id,
            FraudEvent.resolved == False,
        )
    )
    unresolved = prev_fraud.scalar() or 0
    if unresolved > 0:
        score += 25 * unresolved
        reasons.append(f"unresolved_fraud_events_{unresolved}")

    # 7. Existing risk level escalation
    if user.risk_score == FraudRisk.MEDIUM:
        score += 10
    elif user.risk_score == FraudRisk.HIGH:
        score += 25
    elif user.risk_score == FraudRisk.CRITICAL:
        score += 50

    # Score → risk level
    if score >= 80:
        risk = FraudRisk.CRITICAL
    elif score >= 50:
        risk = FraudRisk.HIGH
    elif score >= 25:
        risk = FraudRisk.MEDIUM
    else:
        risk = FraudRisk.LOW

    # Persist fraud events for non-LOW
    if risk != FraudRisk.LOW and reasons:
        event = FraudEvent(
            user_id=user_id,
            event_type="AUTO_SCAN",
            risk_level=risk,
            details=", ".join(reasons),
        )
        session.add(event)
        # Escalate user risk score
        _escalate_risk_score(user, risk)

    return risk


def _escalate_risk_score(user: User, new_risk: FraudRisk) -> None:
    order = [FraudRisk.LOW, FraudRisk.MEDIUM, FraudRisk.HIGH, FraudRisk.CRITICAL]
    current_idx = order.index(user.risk_score) if user.risk_score in order else 0
    new_idx = order.index(new_risk)
    if new_idx > current_idx:
        user.risk_score = new_risk


async def get_fraud_alerts(session: AsyncSession, resolved: bool = False) -> list[FraudEvent]:
    result = await session.execute(
        select(FraudEvent)
        .where(FraudEvent.resolved == resolved)
        .order_by(FraudEvent.created_at.desc())
        .limit(100)
    )
    return result.scalars().all()


async def resolve_fraud_event(session: AsyncSession, event_id: int) -> bool:
    event = await session.get(FraudEvent, event_id)
    if event:
        event.resolved = True
        await session.commit()
        return True
    return False
