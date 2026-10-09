"""
ABUTAHUNT — All ORM Models
Prepared by Abuta (@abuta_art)
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, Numeric,
    String, Text, UniqueConstraint, Enum, CheckConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.engine import Base


def utcnow():
    return datetime.now(timezone.utc)


# ─── ENUMS ──────────────────────────────────────────────────────────────────

class RewardStatus(str, PyEnum):
    PENDING   = "PENDING"
    VERIFIED  = "VERIFIED"
    APPROVED  = "APPROVED"
    PROCESSING = "PROCESSING"
    PAID      = "PAID"
    REJECTED  = "REJECTED"
    CANCELLED = "CANCELLED"


class WithdrawalStatus(str, PyEnum):
    PENDING    = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED  = "COMPLETED"
    REJECTED   = "REJECTED"
    CANCELLED  = "CANCELLED"


class FraudRisk(str, PyEnum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


class TaskType(str, PyEnum):
    JOIN_CHANNEL  = "JOIN_CHANNEL"
    JOIN_GROUP    = "JOIN_GROUP"
    START_BOT     = "START_BOT"
    REFERRAL      = "REFERRAL"
    MULTI_CHANNEL = "MULTI_CHANNEL"


class TicketStatus(str, PyEnum):
    OPEN          = "OPEN"
    IN_PROGRESS   = "IN_PROGRESS"
    WAITING_USER  = "WAITING_USER"
    RESOLVED      = "RESOLVED"
    CLOSED        = "CLOSED"


class TransactionType(str, PyEnum):
    CAMPAIGN_REWARD  = "CAMPAIGN_REWARD"
    REFERRAL_BONUS   = "REFERRAL_BONUS"
    MILESTONE_BONUS  = "MILESTONE_BONUS"
    STREAK_BONUS     = "STREAK_BONUS"
    WITHDRAWAL       = "WITHDRAWAL"
    ADJUSTMENT       = "ADJUSTMENT"
    REFUND           = "REFUND"


class NotificationType(str, PyEnum):
    CAMPAIGN_LAUNCHED   = "CAMPAIGN_LAUNCHED"
    TASK_COMPLETED      = "TASK_COMPLETED"
    REWARD_APPROVED     = "REWARD_APPROVED"
    REWARD_REJECTED     = "REWARD_REJECTED"
    PAYMENT_PROCESSING  = "PAYMENT_PROCESSING"
    PAYMENT_COMPLETED   = "PAYMENT_COMPLETED"
    REFERRAL_QUALIFIED  = "REFERRAL_QUALIFIED"
    NEW_CAMPAIGN        = "NEW_CAMPAIGN"
    CAMPAIGN_ENDING     = "CAMPAIGN_ENDING"
    FRAUD_ALERT         = "FRAUD_ALERT"
    ADMIN_ALERT         = "ADMIN_ALERT"


# ─── MODELS ─────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user_id
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128))
    last_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    language_code: Mapped[str] = mapped_column(String(8), default="en")
    referral_code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    referred_by_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_score: Mapped[str] = mapped_column(Enum(FraudRisk), default=FraudRisk.LOW)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    hide_public_name: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_campaigns: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_rewards: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_referrals: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    task_completions: Mapped[list["TaskCompletion"]] = relationship("TaskCompletion", back_populates="user")
    referrals_made: Mapped[list["Referral"]] = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")
    referrals_received: Mapped[list["Referral"]] = relationship("Referral", foreign_keys="Referral.referred_id", back_populates="referred")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="user")
    withdrawals: Mapped[list["Withdrawal"]] = relationship("Withdrawal", back_populates="user")
    fraud_events: Mapped[list["FraudEvent"]] = relationship("FraudEvent", back_populates="user")
    tickets: Mapped[list["SupportTicket"]] = relationship("SupportTicket", back_populates="user")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="user")
    badges: Mapped[list["UserBadge"]] = relationship("UserBadge", back_populates="user")

    __table_args__ = (
        Index("ix_users_referral_code", "referral_code"),
        Index("ix_users_risk_score", "risk_score"),
        Index("ix_users_created_at", "created_at"),
    )


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), unique=True, index=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    pending_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    total_earned: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    total_withdrawn: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    version: Mapped[int] = mapped_column(Integer, default=1)  # optimistic lock
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="wallet")

    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_wallet_balance_non_negative"),
        CheckConstraint("pending_balance >= 0", name="ck_wallet_pending_non_negative"),
    )


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reward_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    max_claims: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_claims: Mapped[int] = mapped_column(Integer, default=0)
    per_user_limit: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="campaign", cascade="all, delete-orphan")
    completions: Mapped[list["TaskCompletion"]] = relationship("TaskCompletion", back_populates="campaign")

    __table_args__ = (
        Index("ix_campaigns_is_active", "is_active"),
        Index("ix_campaigns_ends_at", "ends_at"),
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(Integer, ForeignKey("campaigns.id"), index=True)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(Enum(TaskType), default=TaskType.JOIN_CHANNEL)
    target_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)   # channel username/id
    target_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="tasks")


class TaskCompletion(Base):
    __tablename__ = "task_completions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    campaign_id: Mapped[int] = mapped_column(Integer, ForeignKey("campaigns.id"), index=True)
    reward_status: Mapped[str] = mapped_column(Enum(RewardStatus), default=RewardStatus.PENDING)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    admin_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fraud_score: Mapped[str] = mapped_column(Enum(FraudRisk), default=FraudRisk.LOW)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="task_completions")
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="completions")

    __table_args__ = (
        UniqueConstraint("user_id", "campaign_id", name="uq_completion_user_campaign"),
        Index("ix_task_completions_status", "reward_status"),
    )


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    referred_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), unique=True)
    is_qualified: Mapped[bool] = mapped_column(Boolean, default=False)
    qualified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reward_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    referrer: Mapped["User"] = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referred: Mapped["User"] = relationship("User", foreign_keys=[referred_id], back_populates="referrals_received")

    __table_args__ = (
        CheckConstraint("referrer_id != referred_id", name="ck_referral_no_self"),
        Index("ix_referrals_referrer", "referrer_id"),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    tx_type: Mapped[str] = mapped_column(Enum(TransactionType))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    balance_after: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    description: Mapped[str] = mapped_column(String(512))
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # completion/withdrawal id
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="transactions")

    __table_args__ = (
        Index("ix_transactions_user_created", "user_id", "created_at"),
        Index("ix_transactions_idempotency", "idempotency_key"),
    )


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64))
    code: Mapped[str] = mapped_column(String(32), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    min_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("50.00"))
    max_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("10000.00"))
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    payment_method_id: Mapped[int] = mapped_column(Integer, ForeignKey("payment_methods.id"))
    payment_info: Mapped[str] = mapped_column(String(256))  # masked/hashed in display
    status: Mapped[str] = mapped_column(Enum(WithdrawalStatus), default=WithdrawalStatus.PENDING, index=True)
    admin_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="withdrawals")
    payment_method: Mapped["PaymentMethod"] = relationship("PaymentMethod")

    __table_args__ = (
        Index("ix_withdrawals_user_status", "user_id", "status"),
    )


class FraudEvent(Base):
    __tablename__ = "fraud_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    risk_level: Mapped[str] = mapped_column(Enum(FraudRisk))
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="fraud_events")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    subject: Mapped[str] = mapped_column(String(256))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Enum(TicketStatus), default=TicketStatus.OPEN, index=True)
    admin_reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    replied_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="tickets")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    notif_type: Mapped[str] = mapped_column(Enum(NotificationType))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="notifications")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(32), default="admin")  # superadmin, admin, support
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    action: Mapped[str] = mapped_column(String(128))
    target_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("ix_audit_logs_actor", "actor_id"),
        Index("ix_audit_logs_created", "created_at"),
    )


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    referral_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    earned_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    bonus_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    emoji: Mapped[str] = mapped_column(String(8))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class UserBadge(Base):
    __tablename__ = "user_badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    badge_id: Mapped[int] = mapped_column(Integer, ForeignKey("badges.id"))
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="badges")
    badge: Mapped["Badge"] = relationship("Badge")

    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )


class Broadcast(Base):
    __tablename__ = "broadcasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    target_segment: Mapped[str] = mapped_column(String(64), default="all")
    message_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_file_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    media_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
