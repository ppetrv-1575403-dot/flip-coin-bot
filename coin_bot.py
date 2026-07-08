import asyncio
import os
import uuid
from datetime import datetime

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

from quantum_rng1 import QuantumRNG

from constants import (
    logger, START_TEXT, UNKNOWN_MSG_TEXT, FLIP_COIN_BTN_TEXT, COIN_SIDE,
    get_duel_url, get_cache_size_status_msg, get_accept_duel_answer_msg,
    qstatus_answer, get_duel_answer_msg, get_flip_answer_msg, NO_WEBHOOK_ERR_MSG, ad_text
)

from ad_tools import POOL_SIZE, TRESHOLD, load_ad_links, calc_user_flip_coins, get_link, show_ad

# ─────────────────── Конфиг ───────────────────
#load_dotenv()
load_ad_links()

TOKEN = os.environ["TG_BOT_TOKEN"]
BOT_USERNAME = os.environ["BOT_USERNAME"]
COIN_ANIMATION_ID = os.environ.get("COIN_ANIMATION_ID", "None")

BASE_WEBHOOK_URL = os.environ.get(
    "WEBHOOK_URL",
    os.environ.get("RENDER_EXTERNAL_URL", "")
)

if not BASE_WEBHOOK_URL:
    raise RuntimeError(NO_WEBHOOK_ERR_MSG)

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{BASE_WEBHOOK_URL.rstrip('/')}{WEBHOOK_PATH}"

logger.info(f"WEBHOOK_URL = {WEBHOOK_URL}")
logger.info(f"BASE_WEBHOOK_URL = {BASE_WEBHOOK_URL}")

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 8080))

#AD_LINK_1 = os.environ["AD_LINK_1"]
load_ad_links()

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
    await message.answer(START_TEXT,
parse_mode="HTML", reply_markup=keyboard)


@dp.message(F.text.in_([FLIP_COIN_BTN_TEXT, "/flip"]))
async def flip_coin(message: types.Message):
    user_id = message.from_user.id
    
    if COIN_ANIMATION_ID and len(COIN_ANIMATION_ID) > 10:
        try:
            anim_msg = await message.answer_animation(
                animation=COIN_ANIMATION_ID,
                caption="Монетка подброшена...",
            )
            await asyncio.sleep(2)
            await anim_msg.delete()
        except Exception:
            pass

    bit = await qrng.get_bit()
    flip_answer = get_flip_answer_msg(bit)
    logger.info(flip_answer)
    
    # 2. Отправляем сам результат подбрасывания
    await message.answer(flip_answer, parse_mode="HTML", reply_markup=keyboard)

    # ═══════════════════════ ЛОГИКА РЕКЛАМЫ ═══════════════════════
    show_ad(user_id)


@dp.message(F.text.startswith("/start duel_"))
async def accept_duel(message: types.Message):
    duel_id = message.text.split("_")[1]
    bit = await qrng.get_shared_bit(duel_id)
    answer_msg = get_accept_duel_answer_msg(bit)
    await message.answer(answer_msg, parse_mode="HTML")


@dp.message(Command("qstatus"))
async def q_status(message: types.Message):
    bits_cache_size = len(qrng._pool)
    status = get_cache_size_status_msg(bits_cache_size, TRESHOLD)
    qstatus_answer_msg = qstatus_answer(bits_cache_size, status)
    logger.info(qstatus_answer_msg)
    await message.answer(qstatus_answer_msg)


@dp.message(Command("duel"))
async def create_duel(message: types.Message):
    duel_id = uuid.uuid4().hex[:8]
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎲 Принять вызов",
            url=get_duel_url(BOT_USERNAME, duel_id)
        )]
    ])
    duel_answer_msg = get_duel_answer_msg(duel_id)
    await message.answer(
        duel_answer_msg,
        parse_mode="HTML",
        reply_markup=inline_kb,
    )


@dp.message()
async def unknown_message(message: types.Message):
    logger.info(UNKNOWN_MSG_TEXT)
    await message.answer(UNKNOWN_MSG_TEXT, reply_markup=keyboard)


# ═══════════════════════ Webhook setup ═══════════════════════


async def on_startup(app: web.Application):
    try:
        await qrng.start()
        logger.info(f"Setting webhook → {WEBHOOK_URL}")
        await bot.set_webhook(
            url=WEBHOOK_URL,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
        logger.info("Webhook установлен успешно.")
    except Exception as e:
        logger.error(f"Ошибка при старте: {e}", exc_info=True)
        # Продолжаем работу даже если QRNG не инициализирован
        # (fallback на secrets всё равно сработает)

async def on_shutdown(app: web.Application):
    """Корректное завершение."""
    logger.info("Stopping bot...")
    await bot.delete_webhook()
    await qrng.close()
    await bot.session.close()
    logger.info("Bot stopped.")


async def health_check(request: web.Request):
    """Health-check endpoint для Render."""
    return web.Response(text="OK", status=200)


def create_app() -> web.Application:
    """Сборка aiohttp-приложения."""
    app = web.Application()

    # Health-check на корневом URL (нужен для Render)
    app.router.add_get("/", health_check)

    # Lifecycle hooks
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Aiogram webhook handler
    request_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    request_handler.register(app, path=WEBHOOK_PATH)

    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)