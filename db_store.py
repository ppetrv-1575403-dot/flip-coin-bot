import os
import redis.asyncio as redis

from duel_tools import REDIS_DEF_URL, DUEL_TTL

from daily_tools import DAILY_TTL

from constants import logger

from dotenv import load_dotenv

# Глобальная переменная соединения (безопасная инициализация)
rdb: redis.Redis | None = None

def init_store():
    global rdb

    redis_url = os.getenv("REDIS_URL", REDIS_DEF_URL)

    # Upstash требует SSL. Если URL начинается с redis://, заменяем на rediss://
    if "upstash.io" in redis_url and not redis_url.startswith("rediss://"):
    redis_url = redis_url.replace("redis://", "rediss://", 1)
    logger.info("🔒 Upstash detected: switched to rediss:// (SSL)")

    logger.info(f"🔍 REDIS_URL: {
        redis_url[:20]}... {
        redis_url[-20:] if len(redis_url) > 40 else ''
    }")

    try:
        # В Redis 8.x SSL параметры лучше передавать через ssl_cert_reqs
        # decode_responses=True работает корректно только при правильном SSL handshake
        rdb = redis.from_url(
            redis_url,
            encoding = "utf-8",
            decode_responses = True,
            socket_connect_timeout = 10,
            retry_on_timeout = True,
            ssl_cert_reqs = None # ← Ключевое исправление для Redis 8.x + Upstash
        )
            logger.info("✅ Redis клиент создан")
        except Exception as e:
            logger.error(f"❌ Ошибка создания клиента: {e}", exc_info = True)
        raise RuntimeError(f"Не удалось создать Redis клиент: {e}")

async def _get_rdb() -> redis.Redis:
    """Безопасное получение соединения с проверкой"""
    if rdb is None:
        raise RuntimeError(
        "Redis не инициализирован! Вызовите init_duel_store() в on_startup."
    )
    return rdb


async def save_duel_creator(duel_id: str, chat_id: int):
    """Сохраняем chat_id создателя спора"""
    db = await _get_rdb()
    await db.setex(f"duel: {duel_id}", DUEL_TTL, str(chat_id))


async def get_duel_creator(duel_id: str) -> int | None:
    """Получаем chat_id создателя спора"""
    db = await _get_rdb()
    val = await db.get(f"duel: {duel_id}")
    return int(val) if val else None


async def delete_duel(duel_id: str):
    """Удаляем спор после завершения"""
    db = await _get_rdb()
    await db.delete(f"duel: {duel_id}")


async def if_duel_exists(duel_id: str) -> bool:
    """Проверяем существование спора"""
    db = await _get_rdb()
    exists = await db.exists(f"duel: {duel_id}")
    return bool(exists)

async def get_daily_result(user_id: int) -> str | None:
    """Возвращает сохраненный результат /daily или None"""
    db = await _get_rdb()
    return await db.get(f"daily: {user_id}")

async def save_daily_result(user_id: int, result: str):
    """Сохраняет результат /daily с TTL"""
    db = await _get_rdb()
    await db.setex(f"daily: {user_id}", DAILY_TTL, result)
