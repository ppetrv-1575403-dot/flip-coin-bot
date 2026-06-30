import asyncio
import logging
import random
from collections import deque
from typing import Optional
import aiohttp
import secrets
import hashlib

logger = logging.getLogger(__name__)

ANU_API_URL = "https://qrng.anu.edu.au/API/jsonI.php"

BITS_SIZE = 1024
POOL_SIZE = 500
REFIL_TRSLD = 100

class QuantumRNG:
    """
    Квантовый RNG на базе ANU QRNG API.
    Использует истинную квантовую случайность (вакуумные флуктуации).
    Работает из РФ/РБ без блокировок и специальных SDK.
    """
    
    def __init__(self, 
        pool_size: int = POOL_SIZE, refill_threshold: int = REFIL_TRSLD):
        self._pool: deque[int] = deque(maxlen=pool_size)
        self._pool_size = pool_size
        self._refill_threshold = refill_threshold
        self._lock = asyncio.Lock()
        self._is_refilling = False
        self._session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        """Инициализация сессии и первичное заполнение пула"""
        self._session = aiohttp.ClientSession()
        await self._refill_pool()
        logger.info(f"[ANU QRNG] Пул инициализирован. Доступно битов: {len(self._pool)}")

    async def close(self):
        """Корректное закрытие сессии при остановке бота"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_bit(self) -> int:
        """Получить квантово-случайный бит с автоматическим пополнением"""
        if len(self._pool) <= self._refill_threshold and not self._is_refilling:
            asyncio.create_task(self._refill_pool())

        async with self._lock:
            if not self._pool:
                logger.warning("[ANU QRNG] Пул пуст! Fallback на secrets...")
                return secrets.randbelow(2)
            return self._pool.popleft()

    async def _refill_pool(self):
        """Запрос пачки квантовых чисел к ANU API"""
        async with self._lock:
            if self._is_refilling:
                return
            self._is_refilling = True

        try:
            bits_needed = self._pool_size - len(self._pool)
            if bits_needed <= 0:
                return

            # ANU позволяет запрашивать до 1024 чисел за раз
            request_size = min(bits_needed, BITS_SIZE)
            logger.info(f"[ANU QRNG] Запрос {request_size} квантовых чисел...")

            params = {"length": str(request_size), "type": "uint8"}
            async with self._session.get(ANU_API_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"API вернул статус {resp.status}")
                data = await resp.json()

            if data.get("success") is not True:
                raise RuntimeError(f"API ошибка: {data.get('message', 'unknown')}")

            # Преобразуем байты в биты (чёт/нечёт)
            new_bits = [b % 2 for b in data["data"]]
            random.shuffle(new_bits)

            async with self._lock:
                self._pool.extend(new_bits[:bits_needed])

            logger.info(f"[ANU QRNG] Пул пополнен. Размер: {len(self._pool)}")

        except Exception as e:
            logger.error(f"[ANU QRNG] Ошибка: {e}", exc_info=True)
        finally:
            self._is_refilling = False

async def get_shared_bit(self, duel_id: str) -> int:
    """
    Получить квантовый бит для совместного спора.
    Один и тот же duel_id всегда возвращает один и тот же бит.
    """
    
    # Детерминированный маппинг duel_id → индекс в пуле
    # Это гарантирует, что оба участника получат одинаковый результат
    hash_val = int(hashlib.sha256(duel_id.encode()).hexdigest(), 16)
    
    async with self._lock:
        if not self._pool:
            return secrets.randbelow(2)
        
        index = hash_val % len(self._pool)
        bit = self._pool[index]
        # НЕ удаляем бит из пула (popleft), чтобы второй участник получил тот же
        
    return bit