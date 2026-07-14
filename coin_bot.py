import asyncio
import os
import sys

import traceback

import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from dotenv import load_dotenv

from datetime import datetime, timezone, timedelta

from quantum_rng1 import QuantumRNG

from constants import (logger, START_TEXT, UNKNOWN_MSG_TEXT, FLIP_COIN_BTN_TEXT, DAILY_BTN_TEXT, DUEL_BTN_TEXT, COIN_SIDE, get_duel_url, get_cache_size_status_msg, duel_accept_answer_msg, get_duel_share_msg, qstatus_answer, get_flip_answer_msg, get_duel_answer_msg, NO_WEBHOOK_ERR_MSG, ad_text, get_callback_copy_duel_url, copy_link_answer_msg, duel_not_accepted_msg, duel_completed_msg, get_duel_complete_msg, send_duel_settlement_msg, press_to_send_msg, duel_select_user_msg, duel_copy_link_msg, duel_status_msg
)

from ad_tools import POOL_SIZE, TRESHOLD, load_ad_links, calc_user_flip_coins, get_link, show_ad

import db_store 

from db_store import init_store, save_duel_creator, get_duel_creator, delete_duel, if_duel_exists, rdb, get_daily_result, save_daily_result

from duel_tools import generate_duel_id, DUEL_PATTERN, is_bot_url_match

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
    keyboard=[
        [KeyboardButton(text=FLIP_COIN_BTN_TEXT)],
        [KeyboardButton(text=DAILY_BTN_TEXT), 
        KeyboardButton(text=DUEL_BTN_TEXT)]
    ],
    resize_keyboard=True,
)


# ═══════════════════════ Хэндлеры ═══════════════════════


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


@dp.message(F.text.in_([DUEL_BTN_TEXT, "/duel"]))
async def create_duel(message: types.Message):
    """Создание квантового спора с нативным выбором чата"""
    duel_id = generate_duel_id()
    
    # 💾 Сохраняем chat_id создателя
    await save_duel_creator(duel_id, message.chat.id)
    
    # Текст, который автоматически подставится в поле ввода при выборе чата
    
    duel_url = get_duel_url(BOT_USERNAME, duel_id)
    
    share_text = get_duel_share_msg(duel_url)
    #logger.info(f"ТГ юзер, сообщение для спора:\n {share_text}")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=duel_select_user_msg, switch_inline_query=share_text  # ← Ключевой параметр
        )],
        [InlineKeyboardButton(
            text=duel_copy_link_msg,
            callback_data=f"copy_duel:{duel_id}"  # ← callback вместо url
        )],
        [InlineKeyboardButton(
            text=duel_status_msg,
            callback_data=f"check_duel:{duel_id}"
        )]

    ])

    await message.answer(duel_accept_answer_msg,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@dp.message(F.text.in_([DAILY_BTN_TEXT, "/daily"]))
async def daily_forecast(message: types.Message):

    user_id = message.from_user.id
    
    # 1. Проверяем, есть ли уже результат на сегодня
    cached = await get_daily_result(user_id)
    if cached:
        await message.answer(cached, parse_mode="HTML")
        return
    
    # 2. Генерируем новый результат
    bit = await qrng.get_bit()
    prediction = get_daily_prediction_text(user_id, bit)
    
    # 3. Сохраняем в Redis
    await save_daily_result(user_id, prediction)
    
    # 4. Отправляем
    await message.answer(prediction, parse_mode="HTML")


@dp.message(F.text.regexp(DUEL_PATTERN))
async def accept_duel(message: types.Message):
    
    # Извлекаем группы из совпадения
    match = DUEL_PATTERN.match(message.text)
    if not match:
        await message.answer(duel_wrong_link_msg)
        return
        
    duel_id = match.group(1)
    bit = await qrng.get_shared_bit(duel_id)
    duel_answer_msg = get_duel_answer_msg(bit, duel_id)
    
    # ✅ Отправляем результат принимающему (Пользователь Б)
    await message.answer(duel_answer_msg,
       parse_mode="HTML"
    )
    
    # ✅ Отправляем результат создателю (Пользователь А)
    creator_chat_id = await get_duel_creator(duel_id)
    if creator_chat_id:
        try:
            duel_complete_msg = get_duel_complete_msg(bit)
            await bot.send_message(
                chat_id=creator_chat_id,
                text=duel_complete_msg,
                parse_mode="HTML"
            )
            logger.info(f"Уведомление отправлено создателю {creator_chat_id}")
        except Exception as e:
            logger.warning(f"Не удалось уведомить создателя {creator_chat_id}: {e}")

        # Удаляем запись о споре — он завершён
        await delete_duel(duel_id)
    else:
        logger.warning(f"Создатель спора {duel_id} не найден в Redis")


dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        await message.answer(START_TEXT, reply_markup=keyboard, parse_mode="HTML")
        logger.info("Отправлено приветствие")
    except Exception as e:
        logger.error(f"Ошибка в cmd_start: {e}", exc_info=True)


@dp.message(Command("qstatus"))
async def q_status(message: types.Message):
    bits_cache_size = len(qrng._pool)
    status = get_cache_size_status_msg(bits_cache_size, TRESHOLD)
    qstatus_answer_msg = qstatus_answer(bits_cache_size, status)
    logger.info(qstatus_answer_msg)
    await message.answer(qstatus_answer_msg)


# ==================== ОБРАБОТКА КОПИРОВАНИЯ ====================

@dp.callback_query(F.data.startswith("copy_duel:"))
async def copy_duel_link(callback: CallbackQuery):
    duel_id = callback.data.split(":")[1]
    duel_url = get_duel_url(BOT_USERNAME, duel_id)
    callback_copy_duel_url = get_callback_copy_duel_url(duel_url)
    print(f"DEBUG link type={type(duel_url)}, value={repr(duel_url)}")
    print(f"DEBUG duel_id={repr(duel_id)}")
    # Отправляем ссылку отдельным сообщением, которое пользователь может скопировать
    await callback.message.answer(
        callback_copy_duel_url,
        parse_mode="HTML"
    )
    await callback.answer(copy_link_answer_msg)


@dp.callback_query(F.data.startswith("check_duel:"))
async def check_duel_status(callback: CallbackQuery):
    
    duel_id = callback.data.split(":")[1]
    exists = await if_duel_exists(duel_id)

    if exists:
        await callback.answer(duel_not_accepted_msg, show_alert=True)
    else:
        await callback.answer(duel_completed_msg, show_alert=True)


@dp.inline_query()
async def handle_inline_duel(inline_query: InlineQuery):
    query_text = inline_query.query.strip()
    logger.info(f"📨 Inline query received: {repr(query_text)}")
    
    if "start=duel_" in query_text:
        url_match = is_bot_url_match(query_text)
        
        if url_match:
            duel_url = url_match.group(0)
            
            # Убираем @username из начала текста для чистого отображения
            clean_text = query_text
            if clean_text.startswith("@"):
                # Удаляем "@botname " из начала
                parts = clean_text.split(" ", 1)
                if len(parts) > 1 and parts[0].startswith("@"):
                    clean_text = parts[1]
            
            result = InlineQueryResultArticle(
                id="duel_share",
                title=send_duel_settlement_msg,
                description=press_to_send_msg,
                input_message_content=InputTextMessageContent(
                    message_text=clean_text,
                    parse_mode="HTML"  # ← HTML, чтобы ссылки были кликабельными
                ),
                url=duel_url,
                hide_url=False  # ← Показываем ссылку в превью
            )
            
            await inline_query.answer([result], cache_time=1)
            return
    
    # Пустой ответ для нерелевантных запросов
    await inline_query.answer([], cache_time=1)


@dp.message()
async def unknown_message(message: types.Message):
    logger.info(UNKNOWN_MSG_TEXT)
    await message.answer(UNKNOWN_MSG_TEXT, reply_markup=keyboard)

# ═══════════════════════ Webhook setup ═══════════════════════

async def health_check(request: web.Request):
    return web.Response(text="OK", status=200)


async def on_startup(app):
    # 1. Сначала подключаем Redis
    init_store()
    
    # 2. Проверяем реальное соединение (ping)
    try:
        await db_store.rdb.ping()
        logger.info("✅ Redis ping успешен")
    except Exception as e:
        logger.error(f"❌ Redis ping провален: {e}")
        raise  # Не запускаем бота без Redis


async def on_shutdown(app: web.Application):
    """Вызывается при остановке сервера"""


async def setup_webhook():
    """Устанавливаем webhook после запуска сервера."""
    try:
        # Проверяем текущий w0ebhook
        info = await bot.get_webhook_info()
        if info.url != WEBHOOK_URL:
            print(f"⚠️ Webhook не совпадает: {info.url} != {WEBHOOK_URL}", flush=True)

        print(f"🔄 Установка webhook на {WEBHOOK_URL}...", flush=True)
        result = await bot.set_webhook(
            url=WEBHOOK_URL,
            allowed_updates=["message", "callback_query", "inline_query"],
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
    
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
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