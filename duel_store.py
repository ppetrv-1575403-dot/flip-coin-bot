import os
import redis.asyncio as redis

from constants import logger, REDIS_DEF_URL

from duel_tools import REDIS_DEF_URL, DUEL_TTL


# Подключение к Redis (Upstash Free или локальный)
REDIS_URL = ""


def init_duel_store():
    # Подключение к Redis (Upstash Free или локальный)
    REDIS_URL = os.getenv("REDIS_URL", REDIS_DEF_URL)
    rdb = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)


async def save_duel_creator(duel_id: str, chat_id: int):
    """Сохраняем chat_id создателя спора"""
    await rdb.setex(f"duel:{duel_id}", DUEL_TTL, str(chat_id))


async def get_duel_creator(duel_id: str) -> int | None:
    """Получаем chat_id создателя спора"""
    val = await rdb.get(f"duel:{duel_id}")
    return int(val) if val else None


async def delete_duel(duel_id: str):
    """Удаляем спор после завершения"""
    await rdb.delete(f"duel:{duel_id}")


async def if_duel_exists(duel_id):
    exists = await rdb.exists(f"duel:{duel_id}")
    return exists
