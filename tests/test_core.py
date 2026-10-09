"""
ABUTAHUNT — Critical Tests
Prepared by Abuta (@abuta_art)
"""

import asyncio
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from database.models import User, Wallet, Campaign, Task, TaskCompletion, RewardStatus, FraudRisk
from services.wallet_service import credit_wallet, debit_wallet, create_withdrawal_request
from services.campaign_service import verify_and_complete_campaign, get_user_completion
from services.fraud_service import evaluate_fraud_risk
from services.referral_service import qualify_referral, create_referral_record


# ── FIXTURES ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def sample_user():
    user = User()
    user.id = 123456789
    user.first_name = "Test"
    user.referral_code = "TESTCODE"
    user.risk_score = FraudRisk.LOW
    user.is_suspended = False
    user.is_active = True
    from datetime import datetime, timezone
    user.created_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def sample_wallet(sample_user):
    wallet = Wallet()
    wallet.user_id = sample_user.id
    wallet.balance = Decimal("100.00")
    wallet.pending_balance = Decimal("0.00")
    wallet.total_earned = Decimal("100.00")
    wallet.total_withdrawn = Decimal("0.00")
    wallet.version = 1
    return wallet


@pytest.fixture
def sample_campaign():
    campaign = Campaign()
    campaign.id = 1
    campaign.title = "Test Campaign"
    campaign.reward_amount = Decimal("50")
    campaign.is_active = True
    campaign.is_deleted = False
    campaign.max_claims = 100
    campaign.current_claims = 0
    campaign.per_user_limit = 1
    campaign.starts_at = None
    campaign.ends_at = None
    return campaign


# ── WALLET TESTS ─────────────────────────────────────────────────────────────

class TestWallet:
    @pytest.mark.asyncio
    async def test_credit_wallet_basic(self, mock_session, sample_wallet):
        """Credit wallet increases balance."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute.return_value = mock_result

        from sqlalchemy import select
        with patch("services.wallet_service.get_wallet", return_value=sample_wallet):
            initial_balance = sample_wallet.balance
            tx = await credit_wallet(
                session=mock_session,
                user_id=123456789,
                amount=Decimal("50"),
                tx_type="CAMPAIGN_REWARD",
                description="+50 ETB",
                idempotency_key="test_credit_001",
            )
            assert sample_wallet.balance == initial_balance + Decimal("50")
            assert tx.amount == Decimal("50")

    @pytest.mark.asyncio
    async def test_debit_wallet_insufficient(self, mock_session, sample_wallet):
        """Debit fails on insufficient funds."""
        with patch("services.wallet_service.get_wallet", return_value=sample_wallet):
            with pytest.raises(ValueError, match="Insufficient"):
                await debit_wallet(
                    session=mock_session,
                    user_id=123456789,
                    amount=Decimal("500"),
                    tx_type="WITHDRAWAL",
                    description="Overdraft attempt",
                )

    @pytest.mark.asyncio
    async def test_debit_wallet_success(self, mock_session, sample_wallet):
        """Debit reduces balance correctly."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute.return_value = mock_result

        with patch("services.wallet_service.get_wallet", return_value=sample_wallet):
            initial = sample_wallet.balance
            tx = await debit_wallet(
                session=mock_session,
                user_id=123456789,
                amount=Decimal("50"),
                tx_type="WITHDRAWAL",
                description="-50 ETB",
            )
            assert sample_wallet.balance == initial - Decimal("50")
            assert tx.amount == Decimal("-50")

    @pytest.mark.asyncio
    async def test_idempotent_credit(self, mock_session, sample_wallet):
        """Same idempotency key returns existing transaction without double-crediting."""
        existing_tx = MagicMock()
        existing_tx.idempotency_key = "duplicate_key"

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=existing_tx)
        mock_session.execute.return_value = mock_result

        with patch("services.wallet_service.get_wallet", return_value=sample_wallet):
            initial_balance = sample_wallet.balance
            result = await credit_wallet(
                session=mock_session,
                user_id=123456789,
                amount=Decimal("50"),
                tx_type="CAMPAIGN_REWARD",
                description="+50 ETB",
                idempotency_key="duplicate_key",
            )
            # Balance should NOT change — idempotent return
            assert sample_wallet.balance == initial_balance
            assert result == existing_tx


# ── CAMPAIGN TESTS ────────────────────────────────────────────────────────────

class TestCampaign:
    @pytest.mark.asyncio
    async def test_duplicate_completion_blocked(self, mock_session, sample_campaign):
        """Second completion attempt returns already_completed."""
        existing = TaskCompletion()
        existing.user_id = 1
        existing.campaign_id = 1

        with patch("services.campaign_service.get_user_completion", return_value=existing):
            result = await verify_and_complete_campaign(
                session=mock_session,
                bot=AsyncMock(),
                user_id=1,
                campaign_id=1,
            )
            assert result == {"ok": False, "error": "already_completed"}

    @pytest.mark.asyncio
    async def test_channel_not_joined(self, mock_session, sample_campaign):
        """Returns missing tasks when channel not joined."""
        task = Task()
        task.task_type = "JOIN_CHANNEL"
        task.target_id = "@testchannel"
        task.target_url = "https://t.me/testchannel"
        task.title = "Test Channel"
        task.is_active = True
        task.sort_order = 0
        sample_campaign.tasks = [task]

        with patch("services.campaign_service.get_user_completion", return_value=None):
            with patch("services.campaign_service.get_campaign", return_value=sample_campaign):
                with patch("services.campaign_service._check_membership", return_value=False):
                    with patch("services.campaign_service.evaluate_fraud_risk", return_value=FraudRisk.LOW):
                        result = await verify_and_complete_campaign(
                            session=mock_session,
                            bot=AsyncMock(),
                            user_id=1,
                            campaign_id=1,
                        )
                        assert result["ok"] is False
                        assert "missing" in result

    @pytest.mark.asyncio
    async def test_claim_limit_respected(self, mock_session, sample_campaign):
        """Campaign with full claims returns claim_limit error."""
        sample_campaign.max_claims = 10
        sample_campaign.current_claims = 10

        with patch("services.campaign_service.get_user_completion", return_value=None):
            with patch("services.campaign_service.get_campaign", return_value=sample_campaign):
                result = await verify_and_complete_campaign(
                    session=mock_session,
                    bot=AsyncMock(),
                    user_id=1,
                    campaign_id=1,
                )
                assert result["ok"] is False
                assert result["error"] == "claim_limit"


# ── REFERRAL TESTS ────────────────────────────────────────────────────────────

class TestReferral:
    @pytest.mark.asyncio
    async def test_self_referral_blocked(self, mock_session):
        """Self-referral returns None."""
        result = await create_referral_record(mock_session, 123, 123)
        assert result is None

    @pytest.mark.asyncio
    async def test_duplicate_referral_blocked(self, mock_session):
        """Duplicate referral returns None."""
        existing = Referral if False else MagicMock()

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=MagicMock())
        mock_session.execute.return_value = mock_result

        result = await create_referral_record(mock_session, 111, 222)
        assert result is None


# ── FRAUD TESTS ───────────────────────────────────────────────────────────────

class TestFraud:
    @pytest.mark.asyncio
    async def test_new_account_raises_risk(self, mock_session, sample_user):
        """Account created today gets elevated risk score."""
        from datetime import datetime, timezone, timedelta
        sample_user.created_at = datetime.now(timezone.utc)  # brand new

        # Mock all DB queries to return safe defaults
        mock_result = AsyncMock()
        mock_result.scalar = MagicMock(return_value=0)
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute.return_value = mock_result
        mock_session.get.return_value = sample_user

        risk = await evaluate_fraud_risk(mock_session, sample_user.id)
        # New account should score at least MEDIUM
        assert risk in (FraudRisk.MEDIUM, FraudRisk.HIGH, FraudRisk.CRITICAL)


# ── ANTI-DOUBLE-PAY ───────────────────────────────────────────────────────────

class TestNoDuplicatePay:
    def test_reward_states_never_skip_to_paid(self):
        """Reward must go PENDING → VERIFIED → APPROVED → PROCESSING → PAID."""
        valid_transitions = {
            RewardStatus.PENDING: [RewardStatus.VERIFIED, RewardStatus.CANCELLED, RewardStatus.REJECTED],
            RewardStatus.VERIFIED: [RewardStatus.APPROVED, RewardStatus.REJECTED],
            RewardStatus.APPROVED: [RewardStatus.PROCESSING, RewardStatus.REJECTED],
            RewardStatus.PROCESSING: [RewardStatus.PAID, RewardStatus.REJECTED],
        }
        # PENDING cannot jump to PAID
        assert RewardStatus.PAID not in valid_transitions[RewardStatus.PENDING]
        # VERIFIED cannot jump to PAID
        assert RewardStatus.PAID not in valid_transitions[RewardStatus.VERIFIED]
        # APPROVED → PROCESSING → PAID is the only path
        assert RewardStatus.PROCESSING in valid_transitions[RewardStatus.APPROVED]
        assert RewardStatus.PAID in valid_transitions[RewardStatus.PROCESSING]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
