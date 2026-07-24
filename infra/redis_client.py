import logging
import redis.asyncio as redis


class RedisClient:
    """Тонкая обёртка над соединением Redis: только жизненный цикл, без бизнес-логики."""

    def __init__(self, redis_url: str, logger: logging.Logger, use_ssl: bool = False):
        self._logger = logger
        self._use_ssl = use_ssl
        self._redis_url = self._normalize_url(redis_url)
        self._conn: redis.Redis | None = None

    @staticmethod
    def _normalize_url(redis_url: str) -> str:
        # Upstash требует SSL
        if "upstash.io" in redis_url and not redis_url.startswith("rediss://"):
            return redis_url.replace("redis://", "rediss://", 1)
        return redis_url

    async def connect(self) -> None:
        # Общие параметры для ЛЮБОГО подключения (локального и прода)
        kwargs = {
            "encoding": "utf-8",
            "decode_responses": True,
            "socket_connect_timeout": 10,
            "retry_on_timeout": True,
        }

        # SSL-специфичные параметры добавляем только если нужно
        if self._use_ssl:
            kwargs["ssl_cert_reqs"] = None 
            
        self._logger.info(f"Подключение к Redis (SSL: {self._use_ssl})...")
        
        self._conn = redis.from_url(self._redis_url, **kwargs)

        # Проверка соединения
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