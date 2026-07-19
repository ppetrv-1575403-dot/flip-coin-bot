import json

from infra.redis_client import RedisClient


class VoteRepository:
    """Redis-хранилище голосований: опции, голоса, автора."""

    def __init__(self, redis_client: RedisClient, ttl: int):
        self._redis = redis_client
        self._ttl = ttl

    @staticmethod
    def _key(vote_id: str) -> str:
        return f"vote:{vote_id}"

    async def create(self, vote_id: str, options: list[str], creator_id: int) -> None:
        data = {"options": options, "creator": str(creator_id), "votes": {}}
        await self._redis.conn.setex(self._key(vote_id), self._ttl, json.dumps(data))

    async def add_vote(self, vote_id: str, user_id: int, option_idx: int) -> dict | None:
        raw = await self._redis.conn.get(self._key(vote_id))
        if not raw:
            return None

        data = json.loads(raw)
        data["votes"][str(user_id)] = option_idx

        ttl = await self._redis.conn.ttl(self._key(vote_id))
        if ttl > 0:
            await self._redis.conn.setex(self._key(vote_id), ttl, json.dumps(data))

        return data

    async def get(self, vote_id: str) -> dict | None:
        raw = await self._redis.conn.get(self._key(vote_id))
        return json.loads(raw) if raw else None
