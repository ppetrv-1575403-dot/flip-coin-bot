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
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from dotenv import load_dotenv

from quantum_rng1 import QuantumRNG

from constants import (
    logger, START_TEXT, UNKNOWN_MSG_TEXT, FLIP_COIN_BTN_TEXT, COIN_SIDE,
    get_duel_url, get_cache_size_status_msg, get_accept_duel_answer_msg,
    qstatus_answer, get_duel_answer_msg, get_flip_answer_msg, NO_WEBHOOK_ERR_MSG
)

# ─────────────────── Конфиг ───────────────────
load_dotenv()

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

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 8080))

# ─────────────────── QRNG ───────────────────
qrng = QuantumRNG(pool_size=500, refill_threshold=100)

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
    await message.answer(START_TEXT, reply_markup=keyboard)


@dp.message(F.text.in_([FLIP_COIN_BTN_TEXT, "/flip"]))
async def flip_coin(message: types.Message):
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
    await message.answer(flip_answer, parse_mode="HTML", reply_markup=keyboard)


@dp.message(F.text.startswith("/start duel_"))
async def accept_duel(message: types.Message):
    duel_id = message.text.split("_")[1]
    bit = await qrng.get_shared_bit(duel_id)
    answer_msg = get_accept_duel_answer_msg(bit)
    await message.answer(answer_msg, parse_mode="HTML")


@dp.message(Command("qstatus"))
async def q_status(message: types.Message):
    bits_cache_size = len(qrng._pool)
    status = get_cache_size_status_msg(bits_cache_size)
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
    """Вызывается один раз при старте веб-сервера."""
    await qrng.start()
    logger.info(f"Setting webhook → {WEBHOOK_URL}")
    await bot.set_webhook(
        url=WEBHOOK_URL,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )
    logger.info("Webhook установлен успешно.")


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