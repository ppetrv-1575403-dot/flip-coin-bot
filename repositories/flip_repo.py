from infra.redis_client import RedisClient

DEFAULT_TTL = 86400  # сбрасываем счётчик показов рекламы раз в сутки


class FlipCounterRepository:
    """
    Счётчик подбрасываний на пользователя — нужен только для ротации рекламы.
    Раньше жил в обычном dict в памяти процесса и терялся при каждом рестарте
    на Render; теперь — в Redis.
    """

    def __init__(self, redis_client: RedisClient, ttl: int = DEFAULT_TTL):
        self._redis = redis_client
        self._ttl = ttl

    @staticmethod
    def _key(user_id: int) -> str:
        return f"flipcount:{user_id}"

    async def increment(self, user_id: int) -> int:
        key = self._key(user_id)
        new_value = await self._redis.conn.incr(key)
        if new_value == 1:
            await self._redis.conn.expire(key, self._ttl)
        return new_value
