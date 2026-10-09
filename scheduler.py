"""
ABUTAHUNT — Background Scheduler
Campaign auto-expire, daily reports, streak tracking, referral qualification.
Prepared by Abuta (@abuta_art)
"""

import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, and_

from database.engine import AsyncSessionLocal
from database.models import Campaign, TaskCompletion, RewardStatus, User, Referral
from services.analytics_service import get_daily_report
from services.referral_service import qualify_referral

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler(timezone="UTC")


async def start_scheduler():
    _scheduler.add_job(job_expire_campaigns, CronTrigger(minute="*/5"))
    _scheduler.add_job(job_qualify_referrals, CronTrigger(minute="*/10"))
    _scheduler.add_job(job_daily_report, CronTrigger(hour=0, minute=0))
    _scheduler.add_job(job_update_streaks, CronTrigger(hour=1, minute=0))
    _scheduler.start()
    logger.info("Scheduler started")


async def job_expire_campaigns():
    """Auto-deactivate expired campaigns."""
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Campaign).where(
                Campaign.is_active == True,
                Campaign.is_deleted == False,
                Campaign.ends_at <= now,
            )
        )
        expired = result.scalars().all()
        for c in expired:
            c.is_active = False
            logger.info(f"Campaign {c.id} expired and deactivated")
        if expired:
            await session.commit()


async def job_qualify_referrals():
    """Check pending referrals and award bonuses for completed campaigns."""
    async with AsyncSessionLocal() as session:
        # Find users who completed a campaign but haven't been qualified as referral yet
        result = await session.execute(
            select(Referral).where(Referral.is_qualified == False)
        )
        pending_referrals = result.scalars().all()

        for referral in pending_referrals:
            try:
                outcome = await qualify_referral(session, referral.referred_id)
                if outcome:
                    logger.info(
                        f"Referral qualified: referrer={outcome['referrer_id']}, "
                        f"bonus={outcome['bonus']}"
                    )
            except Exception as e:
                logger.error(f"Error qualifying referral {referral.id}: {e}")


async def job_daily_report():
    """Generate and log daily report. Extend to send to admin chat."""
    async with AsyncSessionLocal() as session:
        report = await get_daily_report(session)
        logger.info(
            f"📊 DAILY REPORT: users={report['new_users']}, "
            f"completions={report['completions']}, "
            f"rewards={report['rewards_issued']}, "
            f"paid={report['paid_withdrawals']}, "
            f"fraud={report['fraud_alerts']}, "
            f"conversion={report['conversion']}%"
        )
        # Optionally: send to admin Telegram chat via bot
        # (bot instance needed here; skip in scheduler, handle via notification_service)


async def job_update_streaks():
    """Update streak_days for active users."""
    from datetime import timedelta
    yesterday_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0) - timedelta(days=1)
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.is_active == True))
        users = result.scalars().all()
        for user in users:
            if user.last_activity and user.last_activity >= yesterday_start:
                user.streak_days += 1
            else:
                user.streak_days = 0
        await session.commit()
        logger.info(f"Streaks updated for {len(users)} users")
