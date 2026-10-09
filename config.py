"""
ABUTAHUNT — Configuration
All secrets via environment variables only.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ─── BOT ───────────────────────────────────────────────────────────
    BOT_TOKEN: str
    BOT_USERNAME: str = "abutahunt_bot"

    # ─── WEBHOOK ───────────────────────────────────────────────────────
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PATH: str = "/webhook"
    WEBHOOK_SECRET: str = "CHANGE_THIS_SECRET"
    WEBAPP_HOST: str = "0.0.0.0"
    # Railway injects PORT; fall back to 8080
    WEBAPP_PORT: int = int(os.environ.get("PORT", 8080))

    # ─── DATABASE ──────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://abutahunt:password@db:5432/abutahunt"

    # ─── REDIS ─────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ─── ADMIN ─────────────────────────────────────────────────────────
    ADMIN_IDS: list[int] = []
    ADMIN_SECRET: str = "CHANGE_ADMIN_SECRET"

    # ─── CAMPAIGN DEFAULTS ─────────────────────────────────────────────
    DEFAULT_CAMPAIGN_REWARD: float = 50.0
    DEFAULT_REFERRAL_REWARD: float = 10.0
    MIN_WITHDRAWAL: float = 50.0
    MAX_WITHDRAWAL: float = 10000.0

    # ─── ANTI-FRAUD ────────────────────────────────────────────────────
    FRAUD_RATE_LIMIT_SECONDS: int = 5
    FRAUD_MAX_DAILY_WITHDRAWALS: int = 3
    FRAUD_MIN_ACCOUNT_AGE_DAYS: int = 0
    FRAUD_RISK_AUTO_REVIEW_THRESHOLD: str = "HIGH"

    # ─── NOTIFICATIONS ─────────────────────────────────────────────────
    NOTIFICATION_ADMIN_CHAT: Optional[int] = None

    # ─── LOCALIZATION ──────────────────────────────────────────────────
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: list[str] = ["en", "am"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def WEBHOOK_FULL_URL(self) -> Optional[str]:
        """Ensure WEBHOOK_URL always has https:// prefix."""
        if self.WEBHOOK_URL:
            url = self.WEBHOOK_URL.strip()
            if not url.startswith("http"):
                return f"https://{url}"
            return url
        return None


settings = Settings()
