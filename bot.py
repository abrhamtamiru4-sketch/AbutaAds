#!/usr/bin/env python3
"""
ABUTAHUNT BOT — Main Entry Point
Prepared by Abuta (@abuta_art)
"""

import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import settings
from database.engine import init_db
from handlers import (
    start, tasks, referral, wallet, leaderboard,
    admin, support, notifications
)
from middlewares.rate_limit import RateLimitMiddleware
from middlewares.anti_fraud import AntiFraudMiddleware
from middlewares.user_register import UserRegisterMiddleware
from scheduler import start_scheduler

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/bot.log"),
    ]
)
logger = logging.getLogger(__name__)


async def health_handler(request):
    return web.Response(text="OK", status=200)


async def on_startup(bot: Bot) -> None:
    await init_db()
    await start_scheduler()
    webhook_url = settings.WEBHOOK_FULL_URL
    if webhook_url:
        full = f"{webhook_url}{settings.WEBHOOK_PATH}"
        await bot.set_webhook(
            url=full,
            secret_token=settings.WEBHOOK_SECRET,
            drop_pending_updates=True
        )
        logger.info(f"Webhook set: {full}")
    else:
        logger.info("Running in polling mode")


async def on_shutdown(bot: Bot) -> None:
    if settings.WEBHOOK_FULL_URL:
        await bot.delete_webhook()
    logger.info("Bot shutdown complete")


def create_bot() -> Bot:
    return Bot(token=settings.BOT_TOKEN, parse_mode="HTML")


def create_dispatcher(storage) -> Dispatcher:
    dp = Dispatcher(storage=storage)

    # Middlewares (order matters)
    dp.message.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(RateLimitMiddleware())
    dp.message.middleware(UserRegisterMiddleware())
    dp.callback_query.middleware(UserRegisterMiddleware())
    dp.message.middleware(AntiFraudMiddleware())
    dp.callback_query.middleware(AntiFraudMiddleware())

    # Routers
    dp.include_router(start.router)
    dp.include_router(tasks.router)
    dp.include_router(referral.router)
    dp.include_router(wallet.router)
    dp.include_router(leaderboard.router)
    dp.include_router(support.router)
    dp.include_router(notifications.router)
    dp.include_router(admin.router)

    return dp


async def run_polling():
    bot = create_bot()
    storage = RedisStorage.from_url(settings.REDIS_URL)
    dp = create_dispatcher(storage)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def run_webhook():
    bot = create_bot()
    storage = RedisStorage.from_url(settings.REDIS_URL)
    dp = create_dispatcher(storage)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()

    # Health check endpoint (required by Railway)
    app.router.add_get("/health", health_handler)

    handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.WEBHOOK_SECRET
    )
    handler.register(app, path=settings.WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.WEBAPP_HOST, settings.WEBAPP_PORT)
    await site.start()

    logger.info(f"Webhook server started on {settings.WEBAPP_HOST}:{settings.WEBAPP_PORT}")
    await asyncio.Event().wait()


if __name__ == "__main__":
    if settings.WEBHOOK_FULL_URL:
        asyncio.run(run_webhook())
    else:
        asyncio.run(run_polling())
