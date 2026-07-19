from infra.redis_client import RedisClient


class DailyRepository:
    """Redis-хранилище результатов /daily (один результат в сутки на пользователя)."""

    def __init__(self, redis_client: RedisClient, ttl: int):
        self._redis = redis_client
        self._ttl = ttl

    @staticmethod
    def _key(user_id: int) -> str:
        return f"daily:{user_id}"

    async def get_result(self, user_id: int) -> str | None:
        return await self._redis.conn.get(self._key(user_id))

    async def save_result(self, user_id: int, result: str) -> None:
        await self._redis.conn.setex(self._key(user_id), self._ttl, result)
