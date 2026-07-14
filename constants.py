import logging
import hashlib

# ─────────────────── Логирование ───────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ─────────────────── Константы ───────────────────

START_TEXT = """
⚛️ <b>Добро пожаловать в Квантовую Монетку!</b>

Я не использую обычный генератор случайных чисел. Мои результаты определяются <b>истинной квантовой неопределённостью</b> на оборудовании Австралийского национального университета.

Это честнее, чем любая монетка в твоём кармане. 🎲

<b>Что я умею:</b>
🪙 /flip — Подбросить монетку (Орёл или Решка)
⚔️ /duel — Создать квантовый спор с другом
🔮 /daily — Твой персональный прогноз на день от квантового поля

<i>Выбирай команду ниже или нажми кнопку в меню 👇</i>
"""


UNKNOWN_MSG_TEXT = (
    "Не понимаю эту команду.\n"
    "Нажми «🪙 Подбросить монету» или используй /flip"
)


FLIP_COIN_BTN_TEXT = "🪙 Подбросить монету"
DAILY_BTN_TEXT = "🔮 Прогноз на день"
DUEL_BTN_TEXT = "⚔️ Квантовый спор"


COIN_SIDE = ["Орёл 🦅", "Решка 🪙"]


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
    return (f"📋 <b>Ссылка на спор:</b>\n<code>{duel_url}</code>\n\n"
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

duel_not_accepted_msg = "Друг ещё не принял вызов..."

duel_completed_msg = "✅ Спор уже завершён! Проверь сообщения выше."

duel_wrong_link_msg = "❌ Неверная ссылка на спор."

def get_duel_complete_msg(bit):
    result = COIN_SIDE[bit]
    return (
        f"⚔️ <b>Твой квантовый спор завершён!</b>\n\n"
        f"Друг принял вызов.\n"
        f"Результат общего измерения: <b>{result}</b>"
        )
 
duel_select_user_msg = "⚔️ Выбрать друга в Telegram"

duel_copy_link_msg = "📋 Скопировать ссылку"

duel_status_msg="🔄 Статус спора"

send_duel_settlement_msg = "⚔️ Отправить приглашение на квантовую дуэль"

press_to_send_msg = "Нажми, чтобы отправить другу"
 
 # constants.py или отдельный модуль daily_logic.py


DAILY_PREDICTIONS = {
    True: [  # Позитивные / Активные (Орёл / 1)
        "✨ День благоприятен для новых начинаний. Квантовая суперпозиция на твоей стороне!",
        "🚀 Высокая вероятность успеха в рискованных делах. Действуй!",
        "💡 Интуиция сегодня обострена. Доверяй первому импульсу.",
        "🤝 Отличный день для переговоров и социальных связей.",
        "🔋 Энергия на пике. Реши ту задачу, которую откладывал.",
    ],
    False: [  # Нейтральные / Осторожные (Решка / 0)
        "🌙 День для созерцания и анализа. Не спеши с выводами.",
        "⚖️ Вселенная требует баланса. Избегай крайностей сегодня.",
        "🛡️ Лучше занять выжидательную позицию. Риски превышают награду.",
        "📚 Хорошее время для обучения и сбора информации.",
        "🧘 Фокус на внутреннем состоянии. Внешние достижения подождут.",
    ]
}


def get_daily_prediction_text(user_id: int, bit: int) -> str:
    """Генерирует детерминированное предсказание на основе квантового бита"""
    is_positive = bool(bit)
    phrases = DAILY_PREDICTIONS[is_positive]
    
    # Детерминированный выбор фразы на основе user_id и текущей даты
    from datetime import date
    seed_str = f"{user_id}:{date.today().isoformat()}"
    idx = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16) % len(phrases)
    
    side_descr = " (Активность)" if is_positive else " (Покой)"
    side_name = COIN_SIDE[bit]
    
    return (
        f"<b>🔮 Твой квантовый прогноз на сегодня</b>\n\n"
        f"Выпало: <b>{side_name+side_descr}</b>\n\n"
        f"{phrases[idx]}\n\n"
        f"<i>Результат зафиксирован до завтрашнего утра.</i>"
    )
