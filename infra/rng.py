import asyncio
import hashlib
import logging
import random
import secrets
from collections import deque
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

ANU_API_URL = "https://qrng.anu.edu.au/API/jsonI.php"

BITS_PER_REQUEST = 1024
NET_STATUS_OK = 200


class QuantumRNG:
    """
    Квантовый RNG на базе ANU QRNG API (вакуумные флуктуации).
    Пул чисел пополняется в фоне, при истощении — fallback на secrets.
    """

    def __init__(self, pool_size: int = 500, refill_threshold: int = 100):
        self._pool: deque[int] = deque(maxlen=pool_size)
        self._pool_size = pool_size
        self._refill_threshold = refill_threshold
        self._lock = asyncio.Lock()
        self._is_refilling = False
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def pool_size(self) -> int:
        """Текущий размер пула. Публичное свойство вместо доступа к _pool извне."""
        return len(self._pool)

    @property
    def refill_threshold(self) -> int:
        return self._refill_threshold

    async def start(self) -> None:
        self._session = aiohttp.ClientSession()
        await self._refill_pool()
        logger.info(f"[ANU QRNG] Пул инициализирован. Доступно битов: {len(self._pool)}")

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_bit(self) -> int:
        """Получить квантово-случайный бит с автоматическим фоновым пополнением."""
        if len(self._pool) <= self._refill_threshold and not self._is_refilling:
            asyncio.create_task(self._refill_pool())

        async with self._lock:
            if not self._pool:
                logger.warning("[ANU QRNG] Пул пуст! Fallback на secrets...")
                return secrets.randbelow(2)
            return self._pool.popleft()

    async def get_shared_bit(self, duel_id: str) -> int:
        """
        Возвращает один и тот же бит для одного duel_id в рамках вызова —
        бит не удаляется из пула, чтобы оба участника спора увидели один результат.
        """
        hash_val = int(hashlib.sha256(duel_id.encode()).hexdigest(), 16)

        async with self._lock:
            if not self._pool:
                return secrets.randbelow(2)
            index = hash_val % len(self._pool)
            return self._pool[index]

    async def _refill_pool(self) -> None:
        async with self._lock:
            if self._is_refilling:
                return
            self._is_refilling = True

        try:
            bits_needed = self._pool_size - len(self._pool)
            if bits_needed <= 0:
                return

            request_size = min(bits_needed, BITS_PER_REQUEST)
            logger.info(f"[ANU QRNG] Запрос {request_size} квантовых чисел...")

            params = {"length": str(request_size), "type": "uint8"}
            async with self._session.get(
                ANU_API_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != NET_STATUS_OK:
                    raise RuntimeError(f"API вернул статус {resp.status}")
                data = await resp.json()

            if data.get("success") is not True:
                raise RuntimeError(f"API ошибка: {data.get('message', 'unknown')}")

            new_bits = [b % 2 for b in data["data"]]
            random.shuffle(new_bits)

            async with self._lock:
                self._pool.extend(new_bits[:bits_needed])

            logger.info(f"[ANU QRNG] Пул пополнен. Размер: {len(self._pool)}")

        except Exception as e:
            logger.error(f"[ANU QRNG] Ошибка: {e}", exc_info=True)
        finally:
            self._is_refilling = False
