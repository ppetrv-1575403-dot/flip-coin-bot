import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import os
from datetime import datetime

import aiohttp
import uuid

from quantum_rng1 import QuantumRNG

# Токен вашего бота (получите у @BotFather)
load_dotenv()
TOKEN = os.environ["TG_BOT_TOKEN"]

# Инициализация БЕЗ токена (для симулятора он не нужен)
qrng = QuantumRNG(pool_size=500, refill_threshold=100)

# ID анимации монетки (можно отправить гифку в @RawDataBot и скопировать file_id)
# Если оставить None, будет использоваться просто текст
COIN_ANIMATION_ID =os.environ["COIN_ANIMATION_ID"]

URL_QRNG = "https://qrng.anu.edu.au/API/jsonI.php?length=1&type=uint8"

START_TEXT = "Привет! Я бот для подбрасывания монетки.\nЯ работаю с использованием квантовых вычислений - реальная связь с вселенной, которая поможет принять решение!\nНажми кнопку ниже или напиши /flip"

UNKNOWN_MSG_TEXT = "Не понимаю эту команд.\nНажми «🪙 Подбросить монету» или используй /flip"

FLIP_COIN_BTN_TEXT = "🪙 Подбросить монету"

COIN_SIDE = ["Орёл 🦅", "Решка 🪙"]

BOT_USERNAME = os.environ["BOT_USERNAME"]

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def get_anu_quantum_bit() -> int:
    async with aiohttp.ClientSession() as session:
        async with session.get(
           URL_QRNG 
        ) as resp:
            data = await resp.json()
            return data["data"][0] % 2  # 0 или 1

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Клавиатура с кнопкой
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text= FLIP_COIN_BTN_TEXT)]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    await message.answer(START_TEXT,
        reply_markup=keyboard
    )

@dp.message(F.text.in_([FLIP_COIN_BTN_TEXT, "/flip"]))
async def flip_coin(message: types.Message):
    """Основная логика подбрасывания"""
    
    # Сначала отправляем анимацию (если есть ID) или сообщение о процессе
    if COIN_ANIMATION_ID and len(COIN_ANIMATION_ID) > 10:
        try:
            anim_msg = await message.answer_animation(
                animation=COIN_ANIMATION_ID,
                caption="Монетка подброшена..."
            )
            # Небольшая задержка для реалистичности
            await asyncio.sleep(2)
            await anim_msg.delete()
        except Exception:
            pass  # Если анимация невалидна, просто продолжаем

    # Генерация результата
    #result = random.choice(COIN_SIDE)
    #idx = await get_anu_quantum_bit()
    #result = COIN_SIDE[idx]
    
    bit = await qrng.get_bit()
    result = COIN_SIDE[bit]
    
    # Отправляем итоговый результат
    flip_answer = f"Результат: <b>{result}</b>"
    logging.info(flip_answer)
    await message.answer(
        flip_answer,
        parse_mode="HTML",
        reply_markup=keyboard
    )

@dp.message(F.text.startswith("/start duel_"))
async def accept_duel(message: types.Message):
    """Обработка принятия спора через deep link"""
    duel_id = message.text.split("_")[1]
    
    # Оба участника получают ОДИНАКОВЫЙ бит
    bit = await qrng.get_shared_bit(duel_id)
    result = COIN_SIDE[bit]
    
    await message.answer(
        f"⚔️ <b>Квантовый спор решён!</b>\n\n"
        f"Результат общего измерения: <b>{result}</b>\n\n"
        f"<i>Этот же результат видит твой оппонент. "
        f"Квантовая физика не врёт.</i>",
        parse_mode="HTML"
    )

@dp.message(Command("qstatus"))
async def q_status(message: types.Message):
    status = "✅ Норма" if len(qrng._pool) > qrng._refill_threshold else "⚠️ Пополняется"
    qstatus_answer = (f"📊 Статус квантового пула:\n"
        f"• Битов в запасе: {len(qrng._pool)}\n"
        f"• Состояние: {status}\n"
        f"• Провайдер: Росатом «Квант»"
    )
    logging.info(qstatus_answer)
    await message.answer(qstatus_answer)

@dp.message(Command("duel"))
async def create_duel(message: types.Message):
    """Создание квантового спора"""
    duel_id = uuid.uuid4().hex[:8]
    
    keyboard = Inline0KeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎲 Принять вызов",
            url=f"https://t.me/{BOT_USERNAME}?start=duel_{duel_id}"
        )]
    ])
    
    await message.answer(
        f"⚔️ <b>Квантовый спор создан!</b>\n\n"
        f"Отправь эту кнопку другу.\n"
        f"Когда он нажмёт «Принять вызов», вы оба получите "
        f"результат <i>одного и того же</i> квантового измерения.\n\n"
        f"<code>ID: {duel_id}</code>",
        parse_mode="HTML",
        reply_markup=keyboard
    )

@dp.message()
async def unknown_message(message: types.Message):
    """Реакция на непонятные сообщения"""
    logging.info(UNKNOWN_MSG_TEXT)
    await message.answer(
        UNKNOWN_MSG_TEXT,
        reply_markup=keyboard
    )
    
async def main():
    await qrng.start()
    try:
        """Запуск бота"""
        logging.info("Бот запущен!")
        await dp.start_polling(bot)
    finally:
        # Корректное закрытие HTTP-сессии при остановке
        logging.info("Остановка бота...")
        await qrng.close()
        logging.info("Бот остановлен")  


if __name__ == "__main__":
    asyncio.run(main())    