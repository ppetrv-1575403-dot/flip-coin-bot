"""
Локальная версия бота для разработки и тестирования (Polling).
Запуск: python local_main.py
"""
import asyncio
import sys
from dotenv import load_dotenv

from aiogram import Bot
from config import ConfigError, load_settings
from logging_setup import setup_logging
from bot import build_dispatcher
from infra.redis_client import RedisClient
from infra.rng import QuantumRNG
from bot_menu import set_commands

async def main() -> None:
    # 1. Загружаем переменные окружения и логи
    load_dotenv()
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("🚀 ЛОКАЛЬНЫЙ ЗАПУСК БОТА (РЕЖИМ POLLING)")
    logger.info("=" * 50)

    # 2. Валидируем конфиг
    try:
        settings = load_settings()
    except ConfigError as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
        logger.error("💡 Подсказка: убедись, что в файле .env заполнен TG_BOT_TOKEN и WEBHOOK_URL (можно указать http://localhost).")
        sys.exit(1)

    # 3. Инициализируем базовые компоненты
    bot = Bot(token=settings.bot_token)
    
    # Создаем экземпляр клиента
    redis_client = RedisClient(settings.redis_url, logger, settings.redis_use_ssl)
    
    await redis_client.connect()
    logger.info("✅ Redis успешно подключен")
    
    qrng = QuantumRNG(pool_size=settings.qrng_pool_size, refill_threshold=settings.qrng_refill_threshold)

    # 4. Собираем Dispatcher со всеми зависимостями
    dp = await build_dispatcher(settings, redis_client, qrng, logger)
    # 5. Запускаем квантовый генератор
    try:
        await qrng.start()
        logger.info("✅ QRNG инициализирован и готов к работе")
    except Exception as e:
        logger.warning(f"⚠️ QRNG не инициализирован: {e}")

    # 6. Устанавливаем меню команд
    await set_commands(bot)
    logger.info("✅ Меню команд установлено")

    logger.info("✅ Бот готов к работе! Нажми Ctrl+C для остановки.")
    
    # 7. Запускаем polling (вместо aiohttp сервера)
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки (Ctrl+C)")
    finally:
        # Корректное завершение работы
        await bot.session.close()
        logger.info("✅ Сессия бота закрыта")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Остановка бота...")