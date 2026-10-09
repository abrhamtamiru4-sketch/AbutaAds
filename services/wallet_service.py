"""
ABUTAHUNT — Wallet Service
Atomic, idempotent financial operations.
Prepared by Abuta (@abuta_art)
"""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Wallet, Transaction, Withdrawal, PaymentMethod, WithdrawalStatus, TransactionType
from config import settings


async def get_wallet(session: AsyncSession, user_id: int) -> Optional[Wallet]:
    result = await session.execute(select(Wallet).where(Wallet.user_id == user_id))
    return result.scalar_one_or_none()


async def credit_wallet(
    session: AsyncSession,
    user_id: int,
    amount: Decimal,
    tx_type: str,
    description: str,
    reference_id: Optional[int] = None,
    idempotency_key: Optional[str] = None,
) -> Transaction:
    """Credit user wallet atomically. Idempotent via idempotency_key."""
    if idempotency_key:
        existing = await session.execute(
            select(Transaction).where(Transaction.idempotency_key == idempotency_key)
        )
        existing_tx = existing.scalar_one_or_none()
        if existing_tx:
            return existing_tx  # Already processed

    wallet = await get_wallet(session, user_id)
    if not wallet:
        raise ValueError(f"Wallet not found for user {user_id}")

    # Optimistic lock via version
    wallet.balance += amount
    wallet.pending_balance = max(Decimal("0"), wallet.pending_balance - amount)
    wallet.total_earned += amount
    wallet.version += 1

    tx = Transaction(
        user_id=user_id,
        tx_type=tx_type,
        amount=amount,
        balance_after=wallet.balance,
        description=description,
        reference_id=reference_id,
        idempotency_key=idempotency_key or f"credit_{user_id}_{int(datetime.now(timezone.utc).timestamp()*1000)}",
    )
    session.add(tx)
    return tx


async def debit_wallet(
    session: AsyncSession,
    user_id: int,
    amount: Decimal,
    tx_type: str,
    description: str,
    reference_id: Optional[int] = None,
    idempotency_key: Optional[str] = None,
) -> Transaction:
    """Debit wallet atomically. Raises ValueError if insufficient funds."""
    if idempotency_key:
        existing = await session.execute(
            select(Transaction).where(Transaction.idempotency_key == idempotency_key)
        )
        if existing.scalar_one_or_none():
            return existing.scalar_one_or_none()

    wallet = await get_wallet(session, user_id)
    if not wallet:
        raise ValueError(f"Wallet not found for user {user_id}")
    if wallet.balance < amount:
        raise ValueError(f"Insufficient balance: {wallet.balance} < {amount}")

    wallet.balance -= amount
    wallet.total_withdrawn += amount
    wallet.version += 1

    tx = Transaction(
        user_id=user_id,
        tx_type=tx_type,
        amount=-amount,
        balance_after=wallet.balance,
        description=description,
        reference_id=reference_id,
        idempotency_key=idempotency_key or f"debit_{user_id}_{int(datetime.now(timezone.utc).timestamp()*1000)}",
    )
    session.add(tx)
    return tx


async def create_withdrawal_request(
    session: AsyncSession,
    user_id: int,
    amount: Decimal,
    payment_method_id: int,
    payment_info: str,
) -> dict:
    """Validate and create a withdrawal request."""
    if amount < Decimal(str(settings.MIN_WITHDRAWAL)):
        return {"ok": False, "error": "below_min"}
    if amount > Decimal(str(settings.MAX_WITHDRAWAL)):
        return {"ok": False, "error": "above_max"}

    wallet = await get_wallet(session, user_id)
    if not wallet or wallet.balance < amount:
        return {"ok": False, "error": "insufficient"}

    # Daily withdrawal limit check
    from sqlalchemy import func
    from datetime import date
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    count_result = await session.execute(
        select(func.count()).where(
            Withdrawal.user_id == user_id,
            Withdrawal.created_at >= today_start,
            Withdrawal.status.not_in([WithdrawalStatus.CANCELLED, WithdrawalStatus.REJECTED])
        )
    )
    daily_count = count_result.scalar() or 0
    if daily_count >= settings.FRAUD_MAX_DAILY_WITHDRAWALS:
        return {"ok": False, "error": "daily_limit"}

    # Debit immediately (hold funds)
    idempotency_key = f"withdrawal_{user_id}_{int(datetime.now(timezone.utc).timestamp()*1000)}"
    try:
        await debit_wallet(
            session=session,
            user_id=user_id,
            amount=amount,
            tx_type=TransactionType.WITHDRAWAL,
            description=f"-{amount} ETB — Withdrawal",
            idempotency_key=idempotency_key,
        )
    except ValueError as e:
        return {"ok": False, "error": str(e)}

    withdrawal = Withdrawal(
        user_id=user_id,
        amount=amount,
        payment_method_id=payment_method_id,
        payment_info=payment_info,
        status=WithdrawalStatus.PENDING,
    )
    session.add(withdrawal)
    await session.commit()
    await session.refresh(withdrawal)
    return {"ok": True, "withdrawal": withdrawal}


async def approve_withdrawal(
    session: AsyncSession, withdrawal_id: int, admin_id: int
) -> Optional[Withdrawal]:
    result = await session.execute(select(Withdrawal).where(Withdrawal.id == withdrawal_id))
    w = result.scalar_one_or_none()
    if not w or w.status != WithdrawalStatus.PENDING:
        return None
    w.status = WithdrawalStatus.COMPLETED
    w.processed_by = admin_id
    w.processed_at = datetime.now(timezone.utc)
    await session.commit()
    return w


async def reject_withdrawal(
    session: AsyncSession, withdrawal_id: int, admin_id: int, note: str
) -> Optional[Withdrawal]:
    result = await session.execute(select(Withdrawal).where(Withdrawal.id == withdrawal_id))
    w = result.scalar_one_or_none()
    if not w or w.status != WithdrawalStatus.PENDING:
        return None

    # Refund the deducted amount
    await credit_wallet(
        session=session,
        user_id=w.user_id,
        amount=w.amount,
        tx_type=TransactionType.REFUND,
        description=f"+{w.amount} ETB — Withdrawal Rejected Refund",
        reference_id=w.id,
        idempotency_key=f"refund_withdrawal_{w.id}",
    )

    w.status = WithdrawalStatus.REJECTED
    w.admin_note = note
    w.processed_by = admin_id
    w.processed_at = datetime.now(timezone.utc)
    await session.commit()
    return w


async def get_pending_withdrawals(session: AsyncSession) -> list[Withdrawal]:
    result = await session.execute(
        select(Withdrawal)
        .where(Withdrawal.status == WithdrawalStatus.PENDING)
        .order_by(Withdrawal.created_at)
    )
    return result.scalars().all()


async def get_active_payment_methods(session: AsyncSession) -> list[PaymentMethod]:
    result = await session.execute(
        select(PaymentMethod)
        .where(PaymentMethod.is_active == True)
        .order_by(PaymentMethod.sort_order)
    )
    return result.scalars().all()


async def get_user_transactions(
    session: AsyncSession, user_id: int, limit: int = 20
) -> list[Transaction]:
    result = await session.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
