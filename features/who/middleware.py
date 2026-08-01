"""
Middleware для отслеживания участников групповых чатов.
Регистрируется на dp.message.outer_middleware — видит ВСЕ сообщения
до обработки хендлерами, не перехватывая их.
"""

from typing import Any, Awaitable, Callable

from aiogram import Bot
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message, TelegramObject

from repositories.who_repo import WhoRepository


class TrackMembersMiddleware(BaseMiddleware):
    """Записывает user_id отправителя в Redis для групповых чатов."""

    def __init__(self, who_repo: WhoRepository):
        self._who_repo = who_repo

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.chat.type in ("group", "supergroup"):
            if event.from_user and not event.from_user.is_bot:
                await self._who_repo.add_member(event.chat.id, event.from_user.id)

        return await handler(event, data)
