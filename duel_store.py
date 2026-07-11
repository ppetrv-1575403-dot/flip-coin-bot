import os
import redis.asyncio as redis

from duel_tools import REDIS_DEF_URL, DUEL_TTL

from constants import logger

from dotenv import load_dotenv

# Глобальная переменная соединения (безопасная инициализация)
rdb: redis.Redis | None = None


def init_duel_store():
    #load_dotenv()
    """
    Инициализация подключения к Redis.
    Должна быть вызвана при старте бота (on_startup).
    """
    global rdb
    
    redis_url = os.getenv("REDIS_URL", REDIS_DEF_URL)
    
    try:
        rdb = redis.from_url(
            redis_url, 
            encoding="utf-8", 
            decode_responses=True
        )
        logger.info(f"✅ Redis подключён: {redis_url[:30]}...")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Redis: {e}", exc_info=True)
        raise RuntimeError(f"Не удалось подключиться к Redis: {e}")


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
    await db.setex(f"duel:{duel_id}", DUEL_TTL, str(chat_id))


async def get_duel_creator(duel_id: str) -> int | None:
    """Получаем chat_id создателя спора"""
    db = await _get_rdb()
    val = await db.get(f"duel:{duel_id}")
    return int(val) if val else None


async def delete_duel(duel_id: str):
    """Удаляем спор после завершения"""
    db = await _get_rdb()
    await db.delete(f"duel:{duel_id}")


async def if_duel_exists(duel_id: str) -> bool:
    """Проверяем существование спора"""
    db = await _get_rdb()
    exists = await db.exists(f"duel:{duel_id}")
    return bool(exists)