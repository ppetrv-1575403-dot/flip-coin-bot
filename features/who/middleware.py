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

from common.telegram_utils import is_from_group_chat, is_from_true_user

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
        if is_from_group_chat(event) and is_from_true_user(event):
            await self._who_repo.add_member(event.chat.id, event.from_user.id)

        return await handler(event, data)
