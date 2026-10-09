"""
ABUTAHUNT — Initial Data Seed
Run after first DB init to seed payment methods, badges, milestones, default campaign.
Prepared by Abuta (@abuta_art)
"""

import asyncio
from decimal import Decimal

from database.engine import init_db, AsyncSessionLocal
from database.models import PaymentMethod, Badge, Milestone, Campaign, Task


async def seed():
    await init_db()
    async with AsyncSessionLocal() as session:
        # ── PAYMENT METHODS ──────────────────────────────────────────
        methods = [
            PaymentMethod(name="Telebirr", code="telebirr", min_amount=Decimal("50"), max_amount=Decimal("10000"), sort_order=0, instructions="Enter your Telebirr phone number"),
            PaymentMethod(name="CBE Bank", code="cbe", min_amount=Decimal("100"), max_amount=Decimal("50000"), sort_order=1, instructions="Enter your CBE account number"),
            PaymentMethod(name="Dashen Bank", code="dashen", min_amount=Decimal("100"), max_amount=Decimal("50000"), sort_order=2, instructions="Enter your Dashen account number"),
            PaymentMethod(name="Awash Bank", code="awash", min_amount=Decimal("100"), max_amount=Decimal("50000"), sort_order=3, instructions="Enter your Awash account number"),
        ]
        session.add_all(methods)

        # ── BADGES ───────────────────────────────────────────────────
        badges = [
            Badge(code="first_reward", name="First Reward", emoji="🏅", description="Earned your first reward"),
            Badge(code="streak_7", name="7-Day Streak", emoji="🔥", description="7 consecutive active days"),
            Badge(code="referrals_10", name="10 Referrals", emoji="👥", description="Referred 10 qualified users"),
            Badge(code="earned_500", name="500 ETB Earned", emoji="💰", description="Earned 500+ ETB total"),
            Badge(code="top_earner", name="Top Earner", emoji="🏆", description="Ranked #1 on leaderboard"),
        ]
        session.add_all(badges)

        # ── MILESTONES ────────────────────────────────────────────────
        milestones = [
            Milestone(name="5 Referrals", referral_count=5, bonus_amount=Decimal("25")),
            Milestone(name="10 Referrals", referral_count=10, bonus_amount=Decimal("50")),
            Milestone(name="25 Referrals", referral_count=25, bonus_amount=Decimal("150")),
            Milestone(name="50 Referrals", referral_count=50, bonus_amount=Decimal("500")),
        ]
        session.add_all(milestones)

        # ── DEFAULT CAMPAIGN ──────────────────────────────────────────
        # This seeds the campaign from the spec; admin can edit/add more
        campaign = Campaign(
            title="Join & Earn 50 ETB",
            description="Join our channels and earn 50 ETB instantly!",
            reward_amount=Decimal("50"),
            max_claims=2000,
            per_user_limit=1,
            is_active=True,
            created_by=0,  # system
        )
        session.add(campaign)
        await session.flush()

        tasks_data = [
            Task(
                campaign_id=campaign.id,
                title="Global Soccer",
                task_type="JOIN_CHANNEL",
                target_id="@Globalsoccerr",
                target_url="https://t.me/Globalsoccerr",
                sort_order=0,
            ),
            Task(
                campaign_id=campaign.id,
                title="Art Share",
                task_type="JOIN_CHANNEL",
                target_id="@artshare444",
                target_url="https://t.me/artshare444",
                sort_order=1,
            ),
        ]
        session.add_all(tasks_data)

        await session.commit()
        print("✅ Initial data seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
