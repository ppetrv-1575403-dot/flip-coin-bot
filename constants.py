import logging

# ─────────────────── Константы ───────────────────

START_TEXT = (
    "⚛️ <b>Добро пожаловать в Квантовую Монетку!</b>\n\n"
    "Я не использую обычный генератор случайных чисел. Мои результаты определяются "
    "<b>истинной квантовой неопределённостью</b> на оборудовании Австралийского "
    "национального университета.\n\n"
    "Это честнее, чем любая монетка в твоём кармане. 🎲\n\n"
    "<b>Что я умею:</b>\n"
    "🪙 /flip — Подбросить монетку (Орёл или Решка)\n"
    "⚔️ /duel — Создать квантовый спор с другом (вы оба получите "
    "идентичный результат одного измерения)\n"
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


def get_cache_size_status_msg(bits_cache_size, refill_threshold):
    return "✅ Норма" if bits_cache_size > refill_threshold else "⚠️ Пополняется"


def get_flip_answer_msg(bit):
    result = COIN_SIDE[bit]
    return f"Результат: <b>{result}</b>"


def get_duel_url(user, duel_id):
    return f"https://t.me/{user}?start=duel_{duel_id}"


def get_duel_share_msg(duel_url):
    return (
        f"⚔️ Квантовый спор!\n\n"
        f"Я создал(а) честное квантовое измерение для нас.\n"
        f"Нажми кнопку ниже, чтобы узнать результат:\n"
        f"{duel_url}"
    )


def get_duel_answer_msg(bit, duel_id):
    result = COIN_SIDE[bit]
    return (
        f"⚔️ <b>Квантовый спор #{duel_id}</b>\n\n"
        f"Результат общего измерения: <b>{result}</b>\n\n"
        f"<i>Твой друг уже видит этот же результат.\n"
        f"Квантовая физика гарантирует честность.</i>"
    )


duel_accept_answer_msg = (
        "🎲 <b>Квантовый спор создан!</b>\n\n"
        "Выбери друга из списка чатов или скопируй ссылку вручную."
    )


def qstatus_answer(bits_cache_size, status):
    return (
        f"📊 Статус квантового пула:\n"
        f"• Битов в запасе: {bits_cache_size}\n"
        f"• Состояние: {status}\n"
        f"• Провайдер: ANU Quantum Random"
    )
    
def get_callback_copy_duel_url(duel_url):
    (f"📋 <b>Ссылка на спор:</b>\n<code>{duel_url}</code>\n\n"
        f"<i>Нажми на ссылку выше, чтобы скопировать, "
        f"и отправь её другу.</i>"
    )

copy_link_answer_msg = "Ссылка готова для копирования!"


NO_WEBHOOK_ERR_MSG = (
    "Не задан WEBHOOK_URL и не найдена RENDER_EXTERNAL_URL. "
    "Укажи URL вручную в переменных окружения."
)


NO_AD_LINK_ERR_MSG = "Не найдено ни одной рекламной ссылки, задайте переменные окружения вида AD_LINK_{номер}"


# Текст рекламного баннера
ad_text = (
    "🎁 <b>Специальное предложение!</b>\n\n"
    "Вы уже подбросили монетку 5 раз! Хотите удвоить свои шансы? "
    "Попробуйте новый сервис аналитики от наших партнеров."
)