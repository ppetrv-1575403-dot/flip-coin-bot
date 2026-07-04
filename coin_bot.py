import asyncio
import logging
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
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application_webhook
from dotenv import load_dotenv

from quantum_rng1 import QuantumRNG

# ─────────────────── Конфиг ───────────────────
load_dotenv()

TOKEN = os.environ["TG_BOT_TOKEN"]
BOT_USERNAME = os.environ["BOT_USERNAME"]
COIN_ANIMATION_ID = os.environ.get("COIN_ANIMATION_ID", "")

# URL, по которому Telegram будет слать обновления.
# На Replit это: https://<repl-name>.<username>.repl.co/webhook
# Можно задать вручную через переменную окружения WEBHOOK_URL,
# либо автоматически через PUBLIC_URL (Replit 2024+).
BASE_WEBHOOK_URL = os.environ.get(
    "WEBHOOK_URL",
    os.environ.get("PUBLIC_URL", "https://your-repl-name.your-username.repl.co")
)
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{BASE_WEBHOOK_URL.rstrip('/')}{WEBHOOK_PATH}"

# Хост и порт, которые слушает Replit (всегда 0.0.0.0:8080)
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 8080))

# ─────────────────── Константы ───────────────────
START_TEXT = (
    "Привет! Я бот для подбрасывания монетки.\n"
    "Я работаю с использованием квантовых вычислений — "
    "реальная связь с вселенной, которая поможет принять решение!\n"
    "Нажми кнопку ниже или напиши /flip"
)
UNKNOWN_MSG_TEXT = (
    "Не понимаю эту команду.\n"
    "Нажми «🪙 Подбросить монету» или используй /flip"
)
FLIP_COIN_BTN_TEXT = "🪙 Подбросить монету"
COIN_SIDE = ["Орёл 🦅", "Решка 🪙"]

# ─────────────────── Логирование ───────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────── QRNG ───────────────────
qrng = QuantumRNG(pool_size=500, refill_threshold=100)

# ─────────────────── Bot / Dispatcher ───────────────────
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Клавиатура
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
    result = COIN_SIDE[bit]

    flip_answer = f"Результат: <b>{result}</b>"
    logger.info(flip_answer)
    await message.answer(flip_answer, parse_mode="HTML", reply_markup=keyboard)


@dp.message(F.text.startswith("/start duel_"))
async def accept_duel(message: types.Message):
    duel_id = message.text.split("_")[1]
    bit = await qrng.get_shared_bit(duel_id)
    result = COIN_SIDE[bit]

    await message.answer(
        f"⚔️ <b>Квантовый спор решён!</b>\n\n"
        f"Результат общего измерения: <b>{result}</b>\n\n"
        f"<i>Этот же результат видит твой оппонент.</i>\n"
        f"Квантовая физика не врёт.",
        parse_mode="HTML",
    )


@dp.message(Command("qstatus"))
async def q_status(message: types.Message):
    status = "✅ Норма" if len(qrng._pool) > qrng._refill_threshold else "⚠️ Пополняется"
    qstatus_answer = (
        f"📊 Статус квантового пула:\n"
        f"• Битов в запасе: {len(qrng._pool)}\n"
        f"• Состояние: {status}\n"
        f"• Провайдер: ANU Quantum Random"
    )
    logger.info(qstatus_answer)
    await message.answer(qstatus_answer)


@dp.message(Command("duel"))
async def create_duel(message: types.Message):
    duel_id = uuid.uuid4().hex[:8]

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎲 Принять вызов",
            url=f"https://t.me/{BOT_USERNAME}?start=duel_{duel_id}",
        )]
    ])

    await message.answer(
        f"⚔️ <b>Квантовый спор создан!</b>\n\n"
        f"Отправь эту кнопку другу.\n"
        f"Когда он нажмёт «Принять вызов», вы оба получите "
        f"результат <i>одного и того же</i> квантового измерения.\n\n"
        f"<code>ID: {duel_id}</code>",
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

    # Устанавливаем webhook в Telegram
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
    """Health-check endpoint — нужен, чтобы Replit видел, что сервер жив."""
    return web.Response(text="OK", status=200)


def create_app() -> web.Application:
    """Сборка aiohttp-приложения."""
    app = web.Application()

    # Health-check на корневом URL
    app.router.add_get("/", health_check)

    # Lifecycle hooks
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Aiogram webhook handler
    request_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    request_handler.register(app, path=WEBHOOK_PATH)

    # Автоматически регистрирует /webhook и привязывает shutdown к aiogram
    setup_application_webhook(
        bot=bot,
        dispatcher=dp,
        app=app,
        path=WEBHOOK_PATH,
    )

    return app


if __name__ == "__main__":
    app = create_app()
    # Replit всегда запускает сервер на 0.0.0.0:8080 (или PORT)
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)