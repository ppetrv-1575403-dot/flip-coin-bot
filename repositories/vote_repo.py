import time
import json
from typing import Optional

from infra.redis_client import RedisClient


class VoteRepository:
    def __init__(self, redis: RedisClient):
        self._redis = redis

    def _key(self, vote_id: str) -> str:
        return f"vote:{vote_id}"

    async def create(
        self,
        vote_id: str,
        chat_id: int,
        creator_id: int,
        options: list[str],
        duration: int,
        is_anonymous: bool = False,
    ) -> None:
        expires_at = int(time.time()) + duration
        data = {
            "chat_id": chat_id,
            "creator": creator_id,
            "options": json.dumps(options, ensure_ascii=False),
            "votes": json.dumps({}),
            "expires_at": expires_at,
            "completed": 0,
            "is_anonymous": int(is_anonymous),
            "result": json.dumps(None),  # результат подсчёта
        }
        await self._redis.conn.hset(self._key(vote_id), mapping=data)
        # TTL с запасом, чтобы данные успели прочитаться после завершения
        await self._redis.conn.expire(self._key(vote_id), duration + 3600)

    async def add_vote(self, vote_id: str, user_id: int, option_idx: int) -> bool:
        """Добавляет голос. Возвращает False, если пользователь уже голосовал."""
        votes_raw = await self._redis.conn.hget(self._key(vote_id), "votes")
        if votes_raw is None:
            return False

        votes = json.loads(votes_raw)
        user_key = str(user_id)

        if user_key in votes:
            return False

        votes[user_key] = option_idx
        await self._redis.conn.hset(
            self._key(vote_id), "votes", json.dumps(votes)
        )
        return True

    async def get(self, vote_id: str) -> Optional[dict]:
        data = await self._redis.conn.hgetall(self._key(vote_id))
        if not data:
            return None

        return {
            "chat_id": int(data["chat_id"]),
            "creator": int(data["creator"]),
            "options": json.loads(data["options"]),
            "votes": json.loads(data["votes"]),
            "expires_at": int(data["expires_at"]),
            "completed": bool(int(data["completed"])),
            "is_anonymous": bool(int(data["is_anonymous"])),
            "result": json.loads(data.get("result", "null")),
        }

    async def mark_completed(self, vote_id: str) -> bool:
        """
        Атомарно устанавливает флаг completed.
        Возвращает True, если флаг установлен впервые (защита от гонки).
        """
        result = await self._redis.conn.hsetnx(
            self._key(vote_id), "completed", 1
        )
        return bool(result)

    async def save_result(self, vote_id: str, result_dict: dict) -> None:
        """Сохраняет результат квантового подсчёта."""
        await self._redis.conn.hset(
            self._key(vote_id), "result", json.dumps(result_dict, ensure_ascii=False)
        )