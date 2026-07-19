from common.texts import COIN_SIDE


def get_duel_url(bot_username: str, duel_id: str) -> str:
    return f"https://t.me/{bot_username}?start=duel_{duel_id}"


def get_duel_share_msg(duel_url: str) -> str:
    return (
        f"⚔️ Квантовый спор!\n\n"
        f"Я создал(а) честное квантовое измерение для нас.\n"
        f"Нажми кнопку ниже, чтобы узнать результат:\n"
        f"{duel_url}"
    )


def get_duel_answer_msg(bit: int, duel_id: str) -> str:
    result = COIN_SIDE[bit]
    return (
        f"⚔️ <b>Квантовый спор #{duel_id}</b>\n\n"
        f"Результат общего измерения: <b>{result}</b>\n\n"
        f"<i>Твой друг уже видит этот же результат.\n"
        f"Квантовая физика гарантирует честность.</i>"
    )


def get_duel_complete_msg(bit: int) -> str:
    result = COIN_SIDE[bit]
    return (
        f"⚔️ <b>Твой квантовый спор завершён!</b>\n\n"
        f"Друг принял вызов.\n"
        f"Результат общего измерения: <b>{result}</b>"
    )


def get_callback_copy_duel_url(duel_url: str) -> str:
    return (
        f"📋 <b>Ссылка на спор:</b>\n<code>{duel_url}</code>\n\n"
        f"<i>Нажми на ссылку выше, чтобы скопировать, "
        f"и отправь её другу.</i>"
    )


duel_accept_answer_msg = (
    "🎲 <b>Квантовый спор создан!</b>\n\n"
    "Выбери друга из списка чатов или скопируй ссылку вручную."
)

duel_not_accepted_msg = "Друг ещё не принял вызов..."
duel_completed_msg = "✅ Спор уже завершён! Проверь сообщения выше."
duel_wrong_link_msg = "❌ Неверная ссылка на спор."

duel_select_user_msg = "⚔️ Выбрать друга в Telegram"
duel_copy_link_msg = "📋 Скопировать ссылку"
duel_status_msg = "🔄 Статус спора"

copy_link_answer_msg = "Ссылка готова для копирования!"

send_duel_settlement_msg = "⚔️ Отправить приглашение на квантовую дуэль"
press_to_send_msg = "Нажми, чтобы отправить другу"
