from dataclasses import dataclass

# --- Доменные константы ---

MAX_OPTIONS = 10
MAX_QUESTION_LENGTH = 300
MAX_OPTION_LENGTH = 100
DEFAULT_OPTIONS = ["Да", "Нет"]
DEFAULT_DURATION = 300  # 5 минут
MIN_DURATION = 10
MAX_DURATION = 3600  # 1 час

# --- Модели данных ---

@dataclass
class VoteRequest:
    """Запрос на создание голосования."""
    question: str
    options: list[str]
    is_anonymous: bool = False
    duration: int = DEFAULT_DURATION


@dataclass
class VoteResult:
    """Запрос на результат голосования."""
    winner_idx: int
    weights: list[int]
    probabilities: list[int]
    total_votes: int
    is_low_votes: bool = False

# --- Кастомные исключения ---

class VoteError(Exception):
    """Базовое исключение для ошибок голосования."""
    pass


class EmptyQuestionError(VoteError):
    """Вопрос пустой или отсутствует."""
    pass


class TooManyOptionsError(VoteError):
    """Превышен лимит вариантов (макс. 10)."""
    pass


class QuestionTooLongError(VoteError):
    """Вопрос превышает 300 символов."""
    pass


class OptionTooLongError(VoteError):
    """Вариант ответа превышает 100 символов."""
    pass


class InvalidDurationError(VoteError):
    """Недопустимое значение таймера (вне диапазона 10–3600 секунд)."""
    pass
