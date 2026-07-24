import asyncio
import sys

from aiogram import Bot
from aiohttp import web
from dotenv import load_dotenv

from bot import build_dispatcher
from config import ConfigError, load_settings
from infra.redis_client import RedisClient
from infra.rng import QuantumRNG
from logging_setup import setup_logging
from server import build_app, setup_webhook
from bot_menu import set_commands

WEBAPP_HOST = "0.0.0.0"


async def main() -> None:
    load_dotenv()
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("🚀 БОТ ЗАПУСКАЕТСЯ")
    logger.info("=" * 50)

    try:
        settings = load_settings()
    except ConfigError as e:
        logger.error(f"❌ {e}")
        sys.exit(1)

    logger.info(f"✅ BOT_USERNAME: {settings.bot_username}")
    logger.info(f"✅ ИТОГОВЫЙ WEBHOOK_URL = {settings.full_webhook_url}")
    logger.info(f"✅ PORT = {settings.port}")

    bot = Bot(token=settings.bot_token)
    
    redis_client = RedisClient(settings.redis_url, logger)
    qrng = QuantumRNG(pool_size=settings.qrng_pool_size, refill_threshold=settings.qrng_refill_threshold)

    dp = await build_dispatcher(settings, redis_client, qrng, logger)

    await set_commands(bot)

    try:
        await qrng.start()
        logger.info("✅ QRNG инициализирован")
    except Exception as e:
        logger.warning(f"⚠️ QRNG не инициализирован: {e}")

    app = build_app(bot, dp, settings, redis_client, qrng, logger)

    await set_commands(bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, settings.port)
    await site.start()

    logger.info(f"✅ Сервер запущен на {WEBAPP_HOST}:{settings.port}")

    # Устанавливаем webhook ПОСЛЕ запуска сервера
    await setup_webhook(bot, settings, logger)

    # Держим сервер запущенным
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Остановка бота...")
