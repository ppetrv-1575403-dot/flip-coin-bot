import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from dotenv import load_dotenv
import os
from datetime import datetime

# Токен вашего бота (получите у @BotFather)
load_dotenv()
TOKEN = os.environ["TG_BOT_TOKEN"]

# ID анимации монетки (можно отправить гифку в @RawDataBot и скопировать file_id)
# Если оставить None, будет использоваться просто текст
COIN_ANIMATION_ID =os.environ["COIN_ANIMATION_ID"]

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Клавиатура с кнопкой
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🪙 Подбросить монету")]
    ],
    resize_keyboard=True
)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    await message.answer(
        "Привет! Я бот для подбрасывания монетки.\n"
        "Нажми кнопку ниже или напиши /flip",
        reply_markup=keyboard
    )


@dp.message(F.text.in_(["🪙 Подбросить монету", "/flip"]))
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
    result = random.choice(["Орёл 🦅", "Решка 🪙"])
    
    # Отправляем итоговый результат
    await message.answer(
        f"Результат: <b>{result}</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@dp.message()
async def unknown_message(message: types.Message):
    """Реакция на непонятные сообщения"""
    await message.answer(
        "Не понимаю эту команду. Нажми «🪙 Подбросить монету» или используй /flip",
        reply_markup=keyboard
    )


async def main():
    """Запуск бота"""
    logging.info("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())