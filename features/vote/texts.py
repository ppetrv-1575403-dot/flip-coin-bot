from collections import Counter

vote_usage_msg = (
    "Использование: <code>/vote Вариант1;Вариант2;Вариант3</code>\n"
    "От 2 до 5 вариантов, разделённых точкой с запятой."
)

vote_not_found_msg = "Голосование не найдено или истекло."
vote_registered_msg = "Голос учтён!"
vote_results_btn = "📊 Итоги"


def get_too_many_options_msg(max_options: int) -> str:
    return f"Слишком много вариантов, максимум {max_options}."


def get_vote_created_msg(options: list[str]) -> str:
    lines = "\n".join(f"• {opt}" for opt in options)
    return f"🗳 <b>Голосование создано!</b>\n\n{lines}\n\nВыбери вариант ниже:"


def get_results_msg(options: list[str], votes: dict, winners: list[int], was_tiebreak: bool) -> str:
    counter = Counter(votes.values())
    lines = "\n".join(f"{opt} — {counter.get(idx, 0)} 🗳" for idx, opt in enumerate(options))
    winners_text = ", ".join(options[i] for i in winners)
    tiebreak_note = "\n\n⚛️ Была ничья — победитель определён квантовым RNG." if was_tiebreak else ""

    return (
        f"📊 <b>Результаты голосования</b>\n\n"
        f"{lines}\n\n"
        f"🏆 Победитель: <b>{winners_text}</b>"
        f"{tiebreak_note}"
    )
