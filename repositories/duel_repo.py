from infra.redis_client import RedisClient


class DuelRepository:
    """Redis-хранилище споров: кто создал спор, жив ли он ещё."""

    def __init__(self, redis_client: RedisClient, ttl: int):
        self._redis = redis_client
        self._ttl = ttl

    @staticmethod
    def _key(duel_id: str) -> str:
        return f"duel:{duel_id}"

    async def save_creator(self, duel_id: str, chat_id: int) -> None:
        await self._redis.conn.setex(self._key(duel_id), self._ttl, str(chat_id))

    async def get_creator(self, duel_id: str) -> int | None:
        val = await self._redis.conn.get(self._key(duel_id))
        return int(val) if val else None

    async def delete(self, duel_id: str) -> None:
        await self._redis.conn.delete(self._key(duel_id))

    async def exists(self, duel_id: str) -> bool:
        return bool(await self._redis.conn.exists(self._key(duel_id)))
