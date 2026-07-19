import re
import uuid

DUEL_TTL = 86400  # Спор живёт 24 часа

DUEL_PATTERN = re.compile(r"^/start duel_([a-f0-9]{8})$")


def generate_duel_id() -> str:
    return uuid.uuid4().hex[:8]


def is_bot_url_match(query_text: str):
    return re.search(r"https://t\.me/\S+", query_text)


def remove_bot_name(query_text: str) -> str:
    """Убирает '@botname ' из начала текста для чистого отображения."""
    clean_text = query_text
    if clean_text.startswith("@"):
        parts = clean_text.split(" ", 1)
        if len(parts) > 1 and parts[0].startswith("@"):
            clean_text = parts[1]
    return clean_text
