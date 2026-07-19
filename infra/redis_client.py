import logging

import redis.asyncio as redis


class RedisClient:
    """Тонкая обёртка над соединением Redis: только жизненный цикл, без бизнес-логики."""

    def __init__(self, redis_url: str, logger: logging.Logger):
        self._logger = logger
        self._redis_url = self._normalize_url(redis_url)
        self._conn: redis.Redis | None = None

    @staticmethod
    def _normalize_url(redis_url: str) -> str:
        # Upstash требует SSL
        if "upstash.io" in redis_url and not redis_url.startswith("rediss://"):
            return redis_url.replace("redis://", "rediss://", 1)
        return redis_url

    async def connect(self) -> None:
        self._conn = redis.from_url(
            self._redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=10,
            retry_on_timeout=True,
            ssl_cert_reqs=None,  # нужно для Redis 8.x + Upstash
        )
        await self._conn.ping()
        self._logger.info("✅ Redis подключён")

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> redis.Redis:
        if self._conn is None:
            raise RuntimeError("RedisClient не подключён — вызовите connect() при старте приложения")
        return self._conn
