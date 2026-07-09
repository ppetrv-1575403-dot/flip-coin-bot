import asyncio
import os
import sys
import uuid
import traceback

import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from dotenv import load_dotenv

import uuid

from quantum_rng1 import QuantumRNG
from constants import (
    logger, START_TEXT, UNKNOWN_MSG_TEXT, FLIP_COIN_BTN_TEXT, COIN_SIDE,
    get_duel_url, get_cache_size_status_msg, duel_answer_msg, get_duel_share_msg, qstatus_answer, get_flip_answer_msg, get_duel_answer_msg, NO_WEBHOOK_ERR_MSG, ad_text
)
from ad_tools import POOL_SIZE, TRESHOLD, load_ad_links, calc_user_flip_coins, get_link, show_ad

# ─────────────────── Конфиг ───────────────────
print("=" * 50, flush=True)
print("🚀 БОТ ЗАПУСКАЕТСЯ", flush=True)
print("=" * 50, flush=True)

load_dotenv()
load_ad_links()

TOKEN = os.environ.get("TG_BOT_TOKEN", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
COIN_ANIMATION_ID = os.environ.get("COIN_ANIMATION_ID", "")

print(f"✅ TG_BOT_TOKEN получен: {TOKEN[:10]}...", flush=True)
print(f"✅ BOT_USERNAME: {BOT_USERNAME}", flush=True)

if not TOKEN:
    print("❌ TG_BOT_TOKEN не задан!", flush=True)
    sys.exit(1)

# Определяем webhook URL
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "")
MANUAL_URL = os.environ.get("WEBHOOK_URL", "")

print(f"🔍 RENDER_EXTERNAL_URL = '{RENDER_URL}'", flush=True)
print(f"🔍 WEBHOOK_URL (manual) = '{MANUAL_URL}'", flush=True)

BASE_WEBHOOK_URL = MANUAL_URL or RENDER_URL

if not BASE_WEBHOOK_URL:
    print("❌ WEBHOOK_URL не задан! Установи переменную окружения WEBHOOK_URL", flush=True)
    sys.exit(1)

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{BASE_WEBHOOK_URL.rstrip('/')}{WEBHOOK_PATH}"

print(f"✅ ИТОГОВЫЙ WEBHOOK_URL = {WEBHOOK_URL}", flush=True)

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 8080))
print(f"✅ PORT = {WEBAPP_PORT}", flush=True)

# ─────────────────── QRNG ───────────────────
qrng = QuantumRNG(pool_size=POOL_SIZE, refill_threshold=TRESHOLD)

# ─────────────────── Bot / Dispatcher ───────────────────
bot = Bot(token=TOKEN)
dp = Dispatcher()

keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=FLIP_COIN_BTN_TEXT)]],
    resize_keyboard=True,
)

# ═══════════════════════ Хэндлеры ═══════════════════════

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        await message.answer(START_TEXT, reply_markup=keyboard, parse_mode="HTML")
        logger.info("Отправлено приветствие")
    except Exception as e:
        logger.error(f"Ошибка в cmd_start: {e}", exc_info=True)

@dp.message(F.text.in_([FLIP_COIN_BTN_TEXT, "/flip"]))
async def flip_coin(message: types.Message):
    try:
        user_id = message.from_user.id
        
        if COIN_ANIMATION_ID and len(COIN_ANIMATION_ID) > 10:
            try:
                anim_msg = await message.answer_animation(
                    animation=COIN_ANIMATION_ID,
                    caption="Монетка подброшена...",
                )
                await asyncio.sleep(2)
                await anim_msg.delete()
            except Exception as e:
                logger.warning(f"Ошибка анимации: {e}")
        
        bit = await qrng.get_bit()
        flip_answer = get_flip_answer_msg(bit)
        logger.info(f"Результат flip: {flip_answer}")
        
        await message.answer(flip_answer, parse_mode="HTML", reply_markup=keyboard)
        await show_ad(user_id, message)
    except Exception as e:
        logger.error(f"Ошибка в flip_coin: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка. Попробуй позже.")

@dp.message(F.text.startswith("/start duel_"))
async def accept_duel(message: types.Message):
    try:
        duel_id = message.text.split("_")[1]
        bit = await qrng.get_shared_bit(duel_id)
        answer_msg = get_accept_duel_answer_msg(bit)
        await message.answer(answer_msg, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка в accept_duel: {e}", exc_info=True)


@dp.message(F.text.regexp(r"^/start duel_([a-f0-9]{8})$"))
async def accept_duel(message: types.Message):
    """Обработка принятия спора с контекстом"""
    duel_id = message.regexp_match.group(1)
    
    duel_answer_msg = get_duel_answer_msg(bit, duel_id)
    
    await message.answer(duel_answer_msg,
       parse_mode="HTML"
    )


@dp.message(Command("qstatus"))
async def q_status(message: types.Message):
    bits_cache_size = len(qrng._pool)
    status = get_cache_size_status_msg(bits_cache_size, TRESHOLD)
    qstatus_answer_msg = qstatus_answer(bits_cache_size, status)
    logger.info(qstatus_answer_msg)
    await message.answer(qstatus_answer_msg)


@dp.message(Command("duel"))
async def create_duel(message: types.Message):
    """Создание квантового спора с нативным выбором чата"""
    duel_id = uuid.uuid4().hex[:8]
    
    # Текст, который автоматически подставится в поле ввода при выборе чата
    
    duel_url = get_duel_url(user, duel_id)
    
    share_text = get_duel_share_msg(duel_url)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="⚔️ Выбрать друга в Telegram",
            switch_inline_query=share_text  # ← Ключевой параметр
        )],
        [InlineKeyboardButton(
            text="📋 Скопировать ссылку вручную",
            url=duel_url
        )]
    ])
    
    await message.answer(duel_answer_msg,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@dp.message()
async def unknown_message(message: types.Message):
    logger.info(UNKNOWN_MSG_TEXT)
    await message.answer(UNKNOWN_MSG_TEXT, reply_markup=keyboard)

# ═══════════════════════ Webhook setup ═══════════════════════

async def health_check(request: web.Request):
    return web.Response(text="OK", status=200)


async def setup_webhook():
    """Устанавливаем webhook после запуска сервера."""
    try:
        # Проверяем текущий webhook
        info = await bot.get_webhook_info()
        if info.url != WEBHOOK_URL:
            print(f"⚠️ Webhook не совпадает: {info.url} != {WEBHOOK_URL}", flush=True)

        print(f"🔄 Установка webhook на {WEBHOOK_URL}...", flush=True)
        result = await bot.set_webhook(
            url=WEBHOOK_URL,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
        print(f"✅ Webhook установлен: {result}", flush=True)
    except Exception as e:
        print(f"❌ Ошибка установки webhook: {e}", flush=True)


async def main():
    """Главная функция запуска."""
    print("🏁 Запуск бота...", flush=True)
    
    # Инициализируем QRNG
    try:
        await qrng.start()
        print("✅ QRNG инициализирован", flush=True)
    except Exception as e:
        print(f"⚠️ QRNG не инициализирован: {e}", flush=True)
    
    # Создаём приложение
    app = web.Application()
    app.router.add_get("/", health_check)
    
    request_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    request_handler.register(app, path=WEBHOOK_PATH)
    
    # Запускаем сервер в фоне
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    await site.start()
    
    print(f"✅ Сервер запущен на {WEBAPP_HOST}:{WEBAPP_PORT}", flush=True)
    
    # Устанавливаем webhook ПОСЛЕ запуска сервера
    await setup_webhook()
    
    # Держим сервер запущенным
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Остановка бота...", flush=True)