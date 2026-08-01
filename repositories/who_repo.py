"""
Redis-домен для фичи /who: хранение множества участников чата.
Ключ: who:members:{chat_id} → Redis SET из user_id.
"""

from infra.redis_client import RedisClient

MEMBERS_TTL = 7 * 24 * 3600  # 7 дней без активности — очищаем


class WhoRepository:
    def __init__(self, redis: RedisClient):
        self._redis = redis

    def _key(self, chat_id: int) -> str:
        return f"who:members:{chat_id}"

    async def add_member(self, chat_id: int, user_id: int) -> None:
        """Добавляет пользователя в множество участников чата."""
        key = self._key(chat_id)
        await self._redis.conn.sadd(key, str(user_id))
        await self._redis.conn.expire(key, MEMBERS_TTL)

    async def get_members(self, chat_id: int) -> list[int]:
        """Возвращает список user_id всех отслеживаемых участников."""
        raw = await self._redis.conn.smembers(self._key(chat_id))
        return [int(uid) for uid in raw]

    async def count(self, chat_id: int) -> int:
        return await self._redis.conn.scard(self._key(chat_id))