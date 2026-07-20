import logging

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

from config import Settings
from infra.redis_client import RedisClient
from infra.rng import QuantumRNG


async def health_check(request: web.Request) -> web.Response:
    return web.Response(text="OK", status=200)


def build_app(
    bot: Bot,
    dp: Dispatcher,
    settings: Settings,
    redis_client: RedisClient,
    qrng: QuantumRNG,
    logger: logging.Logger,
) -> web.Application:
    app = web.Application()
    
    app.router.add_get("/", health_check)
    #app.router.add_head("/", health_check)

    async def on_startup(_app: web.Application) -> None:
        await redis_client.connect()

    async def on_shutdown(_app: web.Application) -> None:
        """Аккуратно освобождаем ресурсы: HTTP-сессию QRNG, Redis, сессию бота."""
        for close_fn, name in (
            (qrng.close, "QRNG"),
            (redis_client.close, "Redis"),
            (bot.session.close, "Bot session"),
        ):
            try:
                await close_fn()
            except Exception as e:
                logger.warning(f"Ошибка при закрытии {name}: {e}")

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=settings.webhook_path)
    return app


async def setup_webhook(bot: Bot, settings: Settings, logger: logging.Logger) -> None:
    """Устанавливаем webhook после запуска сервера."""
    try:
        info = await bot.get_webhook_info()
        if info.url != settings.full_webhook_url:
            logger.warning(f"⚠️ Webhook не совпадает: {info.url} != {settings.full_webhook_url}")

        logger.info(f"🔄 Установка webhook на {settings.full_webhook_url}...")
        result = await bot.set_webhook(
            url=settings.full_webhook_url,
            allowed_updates=[
                "message", 
                "callback_query", "inline_query"
                
            ],
            drop_pending_updates=True,
        )
        logger.info(f"✅ Webhook установлен: {result}")
    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}", exc_info=True)
