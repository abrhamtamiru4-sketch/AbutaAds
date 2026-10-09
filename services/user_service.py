"""
ABUTAHUNT — User Service
Prepared by Abuta (@abuta_art)
"""

import random
import string
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import User, Wallet
from config import settings


def _gen_referral_code(length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    first_name: str,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    language_code: str = "en",
    referred_by_code: Optional[str] = None,
) -> tuple[User, bool]:
    """Return (user, created). Thread-safe via DB unique constraint."""
    stmt = (
        select(User)
        .options(selectinload(User.wallet))
        .where(User.id == telegram_id)
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        # Update mutable fields
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.last_activity = datetime.now(timezone.utc)
        if language_code in settings.SUPPORTED_LANGUAGES:
            user.language_code = language_code
        await session.commit()
        return user, False

    # Resolve referrer
    referred_by_id = None
    if referred_by_code:
        ref_stmt = select(User).where(User.referral_code == referred_by_code)
        ref_result = await session.execute(ref_stmt)
        referrer = ref_result.scalar_one_or_none()
        if referrer and referrer.id != telegram_id:
            referred_by_id = referrer.id

    # Generate unique referral code
    for _ in range(10):
        code = _gen_referral_code()
        exists = await session.execute(select(User).where(User.referral_code == code))
        if not exists.scalar_one_or_none():
            break

    user = User(
        id=telegram_id,
        first_name=first_name,
        last_name=last_name,
        username=username,
        language_code=language_code if language_code in settings.SUPPORTED_LANGUAGES else "en",
        referral_code=code,
        referred_by_id=referred_by_id,
        last_activity=datetime.now(timezone.utc),
        is_admin=telegram_id in settings.ADMIN_IDS,
    )
    wallet = Wallet(user=user)
    session.add(user)
    session.add(wallet)
    await session.commit()
    await session.refresh(user)
    return user, True


async def get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
    stmt = (
        select(User)
        .options(selectinload(User.wallet))
        .where(User.id == telegram_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def suspend_user(session: AsyncSession, telegram_id: int, admin_id: int) -> bool:
    user = await get_user(session, telegram_id)
    if not user:
        return False
    user.is_suspended = True
    await session.commit()
    return True


async def unsuspend_user(session: AsyncSession, telegram_id: int) -> bool:
    user = await get_user(session, telegram_id)
    if not user:
        return False
    user.is_suspended = False
    await session.commit()
    return True


async def update_language(session: AsyncSession, telegram_id: int, lang: str) -> None:
    user = await get_user(session, telegram_id)
    if user and lang in settings.SUPPORTED_LANGUAGES:
        user.language_code = lang
        await session.commit()


async def set_hide_public_name(session: AsyncSession, telegram_id: int, hide: bool) -> None:
    user = await get_user(session, telegram_id)
    if user:
        user.hide_public_name = hide
        await session.commit()
