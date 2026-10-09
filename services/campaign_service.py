"""
ABUTAHUNT — Campaign & Task Service
Prepared by Abuta (@abuta_art)
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Campaign, Task, TaskCompletion, RewardStatus, FraudRisk
from services.wallet_service import credit_wallet
from services.fraud_service import evaluate_fraud_risk


async def get_active_campaigns(session: AsyncSession) -> list[Campaign]:
    now = datetime.now(timezone.utc)
    stmt = (
        select(Campaign)
        .options(selectinload(Campaign.tasks))
        .where(
            Campaign.is_active == True,
            Campaign.is_deleted == False,
            (Campaign.starts_at == None) | (Campaign.starts_at <= now),
            (Campaign.ends_at == None) | (Campaign.ends_at > now),
        )
        .order_by(Campaign.id)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_campaign(session: AsyncSession, campaign_id: int) -> Optional[Campaign]:
    stmt = (
        select(Campaign)
        .options(selectinload(Campaign.tasks))
        .where(Campaign.id == campaign_id, Campaign.is_deleted == False)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_completion(
    session: AsyncSession, user_id: int, campaign_id: int
) -> Optional[TaskCompletion]:
    stmt = select(TaskCompletion).where(
        TaskCompletion.user_id == user_id,
        TaskCompletion.campaign_id == campaign_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_campaign_stats(session: AsyncSession, campaign: Campaign) -> dict:
    """Return real DB-derived stats only."""
    count_stmt = select(func.count()).where(
        TaskCompletion.campaign_id == campaign.id,
        TaskCompletion.reward_status.in_([
            RewardStatus.VERIFIED, RewardStatus.APPROVED,
            RewardStatus.PROCESSING, RewardStatus.PAID
        ])
    )
    result = await session.execute(count_stmt)
    participants = result.scalar() or 0

    pool = Decimal(str(campaign.reward_amount)) * participants
    remaining = (campaign.max_claims - participants) if campaign.max_claims else None

    return {
        "participants": participants,
        "pool": pool,
        "remaining": remaining if remaining is not None else "∞",
        "is_active": campaign.is_active,
    }


async def verify_and_complete_campaign(
    session: AsyncSession,
    bot,
    user_id: int,
    campaign_id: int,
) -> dict:
    """
    Returns:
        {"ok": True, "amount": Decimal} on success
        {"ok": False, "missing": [...]} if channels not joined
        {"ok": False, "error": "already_completed" | "campaign_ended" | "claim_limit"}
    """
    # Duplicate check
    existing = await get_user_completion(session, user_id, campaign_id)
    if existing:
        return {"ok": False, "error": "already_completed"}

    campaign = await get_campaign(session, campaign_id)
    if not campaign or not campaign.is_active:
        return {"ok": False, "error": "campaign_ended"}

    # Claim limit check
    if campaign.max_claims and campaign.current_claims >= campaign.max_claims:
        return {"ok": False, "error": "claim_limit"}

    # Verify each task via Telegram API
    missing_tasks = []
    for task in campaign.tasks:
        if not task.is_active:
            continue
        if task.task_type in ("JOIN_CHANNEL", "JOIN_GROUP"):
            joined = await _check_membership(bot, user_id, task.target_id)
            if not joined:
                missing_tasks.append(task)

    if missing_tasks:
        return {"ok": False, "missing": missing_tasks}

    # Fraud evaluation
    fraud_risk = await evaluate_fraud_risk(session, user_id, campaign_id)

    # Create completion record (UNIQUE constraint prevents duplicates)
    completion = TaskCompletion(
        user_id=user_id,
        campaign_id=campaign_id,
        reward_status=RewardStatus.PENDING,
        verified_at=datetime.now(timezone.utc),
        fraud_score=fraud_risk,
    )
    session.add(completion)

    # Increment claim counter
    campaign.current_claims += 1

    await session.flush()  # get completion.id before commit

    # If fraud risk is high → stay PENDING for manual review
    if fraud_risk in (FraudRisk.HIGH, FraudRisk.CRITICAL):
        await session.commit()
        return {"ok": True, "amount": campaign.reward_amount, "manual_review": True}

    # Auto-approve and credit wallet
    completion.reward_status = RewardStatus.VERIFIED
    completion.approved_at = datetime.now(timezone.utc)

    await credit_wallet(
        session=session,
        user_id=user_id,
        amount=Decimal(str(campaign.reward_amount)),
        tx_type="CAMPAIGN_REWARD",
        description=f"+{campaign.reward_amount} ETB — Campaign Reward: {campaign.title}",
        reference_id=completion.id,
        idempotency_key=f"campaign_reward_{user_id}_{campaign_id}",
    )

    completion.reward_status = RewardStatus.APPROVED
    await session.commit()

    return {"ok": True, "amount": campaign.reward_amount, "manual_review": False}


async def _check_membership(bot, user_id: int, channel_id: str) -> bool:
    """Check if user is a member of a channel via Telegram API."""
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status not in ("left", "kicked", "banned")
    except Exception:
        return False


async def create_campaign(
    session: AsyncSession,
    title: str,
    description: Optional[str],
    reward_amount: Decimal,
    max_claims: Optional[int],
    per_user_limit: int,
    starts_at: Optional[datetime],
    ends_at: Optional[datetime],
    created_by: int,
    tasks_data: list[dict],
) -> Campaign:
    campaign = Campaign(
        title=title,
        description=description,
        reward_amount=reward_amount,
        max_claims=max_claims,
        per_user_limit=per_user_limit,
        starts_at=starts_at,
        ends_at=ends_at,
        created_by=created_by,
        is_active=False,
    )
    session.add(campaign)
    await session.flush()

    for i, td in enumerate(tasks_data):
        task = Task(
            campaign_id=campaign.id,
            title=td["title"],
            description=td.get("description"),
            task_type=td.get("task_type", "JOIN_CHANNEL"),
            target_id=td.get("target_id"),
            target_url=td.get("target_url"),
            sort_order=i,
        )
        session.add(task)

    await session.commit()
    await session.refresh(campaign)
    return campaign


async def set_campaign_active(
    session: AsyncSession, campaign_id: int, active: bool
) -> Optional[Campaign]:
    campaign = await get_campaign(session, campaign_id)
    if campaign:
        campaign.is_active = active
        await session.commit()
    return campaign


async def delete_campaign(session: AsyncSession, campaign_id: int) -> bool:
    campaign = await get_campaign(session, campaign_id)
    if campaign:
        campaign.is_deleted = True
        campaign.is_active = False
        await session.commit()
        return True
    return False


async def get_user_completions(session: AsyncSession, user_id: int) -> list[TaskCompletion]:
    stmt = (
        select(TaskCompletion)
        .options(selectinload(TaskCompletion.campaign))
        .where(TaskCompletion.user_id == user_id)
        .order_by(TaskCompletion.created_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()
