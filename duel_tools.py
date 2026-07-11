import uuid
import re

REDIS_DEF_URL = "redis://localhost:6379"

DUEL_TTL = 86400  # Спор живёт 24 часа


DUEL_PATTERN = re.compile(r"^/start duel_([a-f0-9]{8})$")


def generate_duel_id():
    return uuid.uuid4().hex[:8]
