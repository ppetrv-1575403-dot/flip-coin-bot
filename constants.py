import logging

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

def get_duel_url(user, duel_id):
    return f"https://t.me/{user}?start=duel_{duel_id}"

def get_cache_size_status_msg(bits_cache_size):
    return "✅ Норма" if bits_cache_size > qrng._refill_threshold else "⚠️ Пополняется"

def get_flip_answer_msg(bit):
    result = COIN_SIDE[bit]
    return f"Результат: <b>{result}</b>"

def get_accept_duel_answer_msg(bit):
    result = COIN_SIDE[bit]
    return (f"⚔️ <b>Квантовый спор решён!</b>\n\n"
        f"Результат общего измерения: <b>{result}</b>\n\n"
        f"<i>Этот же результат видит твой оппонент.</i>\n"
        f"Квантовая физика не врёт.",)
        
def qstatus_answer(bits_cache_size, status): return (
        f"📊 Статус квантового пула:\n"
        f"• Битов в запасе: {bits_cache_size} \n"
        f"• Состояние: {status}\n"
        f"• Провайдер: ANU Quantum Random"
    )
    

def get_duel_answer_msg(duel_id):
    return (
        f"⚔️ <b>Квантовый спор создан!</b>\n\n"
        f"Отправь эту кнопку другу.\n"
        f"Когда он нажмёт «Принять вызов», вы оба получите "
        f"результат <i>одного и того же</i> квантового измерения.\n\n"
        f"<code>ID: {duel_id}</code>")
        
NO_WEBHOOK_ERR_MSG = ("Не задан WEBHOOK_URL и не найдена RENDER_EXTERNAL_URL. "
    "Укажи URL вручную в переменных окружения."
    )
