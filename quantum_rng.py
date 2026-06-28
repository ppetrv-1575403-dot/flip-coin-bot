import asyncio
import logging
import random
import secrets
from collections import deque
from typing import Optional

# Импортируем компоненты платформы "Квант"
try:
    from qunt import QuantumCircuit, Simulator
    QUNT_AVAILABLE = True
except ImportError:
    QUNT_AVAILABLE = False

logger = logging.getLogger(__name__)


class QuantumRNG:
    """
    Квантовый RNG на базе платформы Росатома "Квант".
    Использует шумовой симулятор для генерации истинно случайных битов.
    """

    def __init__(self, pool_size: int = 500, refill_threshold: int = 100):
        if not QUNT_AVAILABLE:
            raise RuntimeError("Библиотека 'qunt' не установлена. Выполните: pip install qunt")
            
        self._pool: deque[int] = deque(maxlen=pool_size)
        self._pool_size = pool_size
        self._refill_threshold = refill_threshold
        self._lock = asyncio.Lock()
        self._is_refilling = False
        
        # Инициализация шумового симулятора Росатома
        # noise_model=True включает реалистичную модель шума оборудования
        self._simulator = Simulator(noise_model=True)

    async def start(self):
        """Первичное заполнение пула при старте бота"""
        await self._refill_pool()
        logger.info(f"[Rosatom QRNG] Пул инициализирован. Доступно битов: {len(self._pool)}")

    async def get_bit(self) -> int:
        """Получить квантово-случайный бит с автоматическим пополнением"""
        # Запускаем фоновое пополнение, если порог достигнут
        if len(self._pool) <= self._refill_threshold and not self._is_refilling:
            asyncio.create_task(self._refill_pool())

        async with self._lock:
            # Fallback на случай полного истощения пула или сбоя платформы
            if not self._pool:
                logger.warning("[Rosatom QRNG] Пул пуст! Включаем fallback на secrets...")
                return secrets.randbelow(2)
                
            return self._pool.popleft()

    async def _refill_pool(self):
        """Генерация пачки битов на симуляторе Росатома"""
        async with self._lock:
            if self._is_refilling:
                return
            self._is_refilling = True

        try:
            bits_needed = self._pool_size - len(self._pool)
            if bits_needed <= 0:
                return

            logger.info(f"[Rosatom QRNG] Запрос {bits_needed} шотов на шумовом симуляторе...")

            # Создаем базовую квантовую схему: H + Measurement
            qc = QuantumCircuit(1)
            qc.h(0)
            qc.measure_all()

            # Выполняем на симуляторе (синхронный вызов оборачиваем в to_thread)
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self._simulator.run(qc, shots=bits_needed).get_counts()
            )

            # Парсим counts {'0': N, '1': M} в плоский список битов
            new_bits = []
            for bit_str, count in result.items():
                # Убираем пробелы, которые могут встречаться в некоторых версиях SDK
                clean_bit = int(bit_str.replace(" ", "").strip())
                new_bits.extend([clean_bit] * count)

            # Перемешиваем, чтобы избежать кластеризации одинаковых битов
            random.shuffle(new_bits)

            async with self._lock:
                self._pool.extend(new_bits[:bits_needed])

            logger.info(f"[Rosatom QRNG] Пул успешно пополнен. Текущий размер: {len(self._pool)}")

        except Exception as e:
            logger.error(f"[Rosatom QRNG] Ошибка генерации: {e}", exc_info=True)
        finally:            self._is_refilling = False