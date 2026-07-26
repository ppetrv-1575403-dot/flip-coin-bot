def vote_help_text(error: str) -> str:
    return (
        f"⚠️ {error}\n\n"
        "📝 <b>Формат команды:</b>\n"
        "<code>/vote Пойдём гулять?</code> → Да/Нет, таймер 5 мин\n"
        "<code>/vote Обед?;Пицца;Суши</code> → свои варианты\n"
        "<code>/vote -a Тайный вопрос?</code> → анонимный опрос\n"
        "<code>/vote -t 60 Быстрый вопрос?</code> → таймер 60 сек\n"
        "<code>/vote -at120 Вопрос?;В1;В2</code> → анонимный, таймер 120 сек\n\n"
        "⚙️ <b>Лимиты:</b> до 10 вариантов, вопрос до 300 символов, "
        "таймер от 10 до 3600 секунд."
    )


def vote_created_text(question: str, duration: int, is_anonymous: bool) -> str:
    anon_note = " (анонимное)" if is_anonymous else ""
    return (
        f"🗳 <b>Голосование{anon_note}</b>\n\n"
        f"<b>{question}</b>\n\n"
        f"⏱ Таймер: {duration} сек.\n"
        f"Нажмите «📊 Итоги» для досрочного подсчёта."
    )


def vote_result_text(
    winner: str,
    options: list[str],
    weights: list[int],
    probabilities: list[float],
    total_votes: int,
    is_low_votes: bool,
) -> str:
    lines = [f"🏆 <b>Победитель:</b> {winner}\n"]

    if is_low_votes:
        lines.append(
            "⚠️ <i>Мало голосов — квантовая случайность "
            "может быть непредсказуемой.</i>\n"
        )

    lines.append(f"📊 <b>Голоса ({total_votes}):</b>")
    for idx, opt in enumerate(options):
        lines.append(f"• {opt} — {weights[idx]} ({probabilities[idx]}%)")

    return "\n".join(lines)


def vote_details_text(
    winner: str,
    options: list[str],
    weights: list[int],
    probabilities: list[float],
    total_votes: int,
) -> str:
    lines = [
        "🔍 <b>Квантовая математика</b>\n",
        f"Всего голосов: {total_votes}",
        f"Победитель: {winner}\n",
        "Вероятности:",
    ]
    for idx, opt in enumerate(options):
        lines.append(f"• {opt}: {probabilities[idx]}% ({weights[idx]} голосов)")

    lines.append("\n⚛️ Исход определён квантовым генератором ANU QRNG.")
    return "\n".join(lines)