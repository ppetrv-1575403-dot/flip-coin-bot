import re

from .schemas import (
    VoteRequest,
    EmptyQuestionError,
    TooManyOptionsError,
    QuestionTooLongError,
    OptionTooLongError,
    InvalidDurationError,
    MAX_OPTIONS,
    MAX_QUESTION_LENGTH,
    MAX_OPTION_LENGTH,
    DEFAULT_OPTIONS,
    DEFAULT_DURATION,
    MIN_DURATION,
    MAX_DURATION,
)

# Паттерн для флагов: -a, -t, -t60, -at60, -ta60
FLAG_PATTERN = re.compile(r"^-(?P<flags>[at]*)(?P<value>\d+)?$")


def _extract_flags(tokens: list[str]) -> tuple[int, bool, int]:
    """
    Извлекает флаги -a и -t из начала списка токенов.
    Возвращает: (индекс первого токена вопроса, is_anonymous, duration).
    """
    idx = 0
    is_anonymous = False
    duration = DEFAULT_DURATION

    while idx < len(tokens):
        match = FLAG_PATTERN.match(tokens[idx])
        if not match:
            break  # первый токен без флага — начало вопроса

        flags = match.group("flags")
        value = match.group("value")

        if "a" in flags:
            is_anonymous = True

        if "t" in flags:
            if value:
                duration = int(value)
                idx += 1
            else:
                # -t без числа → следующий токен должен быть значением
                if idx + 1 >= len(tokens):
                    raise InvalidDurationError("Укажите значение таймера после -t.")
                try:
                    duration = int(tokens[idx + 1])
                except ValueError:
                    raise InvalidDurationError(
                        f"Неверное значение таймера: «{tokens[idx + 1]}». "
                        f"Укажите число секунд."
                    )
                idx += 2
        else:
            # Только -a или комбинация без t
            idx += 1

    return idx, is_anonymous, duration


def parse_vote_args(args: str) -> VoteRequest:
    """
    Парсит аргументы команды /vote.

    Формат:
      /vote Вопрос?                          -> бинарный (Да/Нет), таймер 300 сек
      /vote Вопрос?;Вариант1;Вариант2        -> кастомные варианты
      /vote -a Вопрос?                       -> анонимный
      /vote -t 60 Вопрос?                    -> таймер 60 сек
      /vote -at120 Вопрос?;В1;В2             -> анонимный, таймер 120, свои варианты
    """
    if not args or not args.strip():
        raise EmptyQuestionError("Введите вопрос для голосования.")

    tokens = args.strip().split()
    idx, is_anonymous, duration = _extract_flags(tokens)

    # Оставшийся текст — вопрос и варианты
    remaining = " ".join(tokens[idx:]).strip()

    if not remaining:
        raise EmptyQuestionError("Введите вопрос для голосования.")

    # Валидация таймера
    if duration < MIN_DURATION or duration > MAX_DURATION:
        raise InvalidDurationError(
            f"Таймер должен быть от {MIN_DURATION} до {MAX_DURATION} секунд."
        )

    # Разделение по ; и фильтрация пустых элементов
    parts = [part.strip() for part in remaining.split(";")]
    parts = [part for part in parts if part]

    if not parts:
        raise EmptyQuestionError("Введите вопрос для голосования.")

    question = parts[0]

    if len(question) > MAX_QUESTION_LENGTH:
        raise QuestionTooLongError(
            f"Вопрос слишком длинный ({len(question)} символов). "
            f"Максимум: {MAX_QUESTION_LENGTH}."
        )

    # Определение вариантов
    if len(parts) == 1:
        options = DEFAULT_OPTIONS.copy()
    else:
        options = parts[1:]

        if len(options) > MAX_OPTIONS:
            raise TooManyOptionsError(
                f"Слишком много вариантов ({len(options)}). "
                f"Максимум: {MAX_OPTIONS}."
            )

        for opt in options:
            if len(opt) > MAX_OPTION_LENGTH:
                raise OptionTooLongError(
                    f"Вариант «{opt[:20]}...» слишком длинный "
                    f"({len(opt)} символов). Максимум: {MAX_OPTION_LENGTH}."
                )

    return VoteRequest(
        question=question,
        options=options,
        is_anonymous=is_anonymous,
        duration=duration,
    )