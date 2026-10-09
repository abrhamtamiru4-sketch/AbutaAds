# 🚀 ABUTAHUNT — Telegram Reward Bot
**Prepared by Abuta (@abuta_art)**

Production-ready Telegram channel-growth, referral, task/reward, and community-engagement platform.

---

## ⚡ Quick Deploy

```bash
git clone <repo>
cd abutahunt
cp .env.example .env
# Fill in BOT_TOKEN, POSTGRES_PASSWORD, ADMIN_IDS in .env
chmod +x deploy.sh
./deploy.sh
```

---

## 🏗 Architecture

```
abutahunt/
├── bot.py                  # Entry point (polling or webhook)
├── config.py               # All settings via env vars
├── scheduler.py            # Background jobs (APScheduler)
├── database/
│   ├── engine.py           # SQLAlchemy async engine
│   └── models.py           # All ORM models (15 tables)
├── handlers/
│   ├── start.py            # /start, main menu
│   ├── tasks.py            # Campaign verification
│   ├── wallet.py           # Balance, withdrawal FSM
│   ├── referral.py         # Referral stats + share
│   ├── leaderboard.py      # Rankings
│   ├── notifications.py    # User stats
│   ├── support.py          # Ticket system
│   └── admin.py            # Full admin panel
├── middlewares/
│   ├── rate_limit.py       # Flood protection
│   ├── user_register.py    # Auto-register + DB inject
│   └── anti_fraud.py       # Block suspended/critical users
├── services/
│   ├── campaign_service.py # Telegram membership verify + reward
│   ├── wallet_service.py   # Atomic, idempotent financials
│   ├── referral_service.py # Referral engine + milestones
│   ├── fraud_service.py    # Risk scoring (behavioral only)
│   ├── analytics_service.py# Real DB-derived stats
│   ├── notification_service.py # Push notifications + broadcast
│   └── user_service.py     # User CRUD
├── locales/
│   └── strings.py          # English + Amharic (EN/AM)
├── migrations/
│   └── init_data.py        # Seed payment methods, badges, campaign
├── tests/
│   └── test_core.py        # Critical financial + reward tests
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── deploy.sh
├── requirements.txt
└── .env.example
```

---

## 🔐 Security

- All secrets via `.env` only — never in code
- Idempotency keys prevent double-pay
- Optimistic locking on wallets
- Telegram API verifies channel membership (not just button press)
- Anti-fraud behavioral scoring (no invasive fingerprinting)
- Rate limiting on all updates
- DB-level UNIQUE constraint on `(user_id, campaign_id)` prevents duplicate completions

---

## 📦 Stack

| Component | Tech |
|-----------|------|
| Bot framework | aiogram 3.x |
| Database | PostgreSQL 16 + SQLAlchemy async |
| Cache/FSM | Redis 7 |
| Background jobs | APScheduler |
| Container | Docker + Compose |
| Reverse proxy | Nginx |
| Language | Python 3.12 |

---

## 👑 Admin Commands

| Command | Action |
|---------|--------|
| `/admin` | Open admin panel |

Admin panel includes: Campaign management, User management, Payment approvals, Broadcast, Analytics, Fraud alerts, System settings.

---

## 💰 Reward Flow

```
User joins channels → Verify (Telegram API check) → 
Anti-fraud score → PENDING → APPROVED → wallet credited → 
User requests withdrawal → Admin approves → PAID
```

Every step is recorded in `transactions` (immutable ledger). Balance is never modified without a transaction record.

---

## 🧪 Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

## 🌍 Localization

English + Amharic. Add more languages in `locales/strings.py` → `STRINGS` dict.

---

*Built with ❤️ by Abuta · @abuta_art*
