"""
Хендлеры фичи /who — квантово-случайный выбор участника группы.
"""

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from infra.rng import QuantumRNG
from repositories.who_repo import WhoRepository

from .texts import (
    who_error_text,
    who_no_members_text,
    who_not_group_text,
    who_result_text,
)

router = Router(name="who")


@router.message(Command("who"))
async def cmd_who(
    message: Message,
    bot: Bot,
    qrng: QuantumRNG,
    who_repo: WhoRepository,
    logger,
):
    try:
        # Только для групп
        if message.chat.type not in ("group", "supergroup"):
            await message.answer(who_not_group_text())
            return

        chat_id = message.chat.id

        # Получаем отслеживаемых участников из Redis
        member_ids = await who_repo.get_members(chat_id)

        # Fallback: если Redis пуст, берём администраторов чата
        if not member_ids:
            try:
                admins = await bot.get_chat_administrators(chat_id)
                member_ids = [
                    m.user.id for m in admins if not m.user.is_bot
                ]
            except Exception as e:
                logger.warning(f"Не удалось получить админов: {e}")

        if not member_ids:
            await message.answer(who_no_members_text())
            return

        # Квантовый выбор
        idx = await qrng.get_random_below(len(member_ids))
        chosen_id = member_ids[idx]

        # Получаем имя выбранного участника
        user_display = await _get_user_display(bot, chat_id, chosen_id)

        text = who_result_text(user_display, len(member_ids))
        await message.answer(text, parse_mode="HTML")
        logger.info(f"/who в чате {chat_id}: выбран user_id={chosen_id}")

    except Exception as e:
        logger.error(f"Ошибка в cmd_who: {e}", exc_info=True)
        await message.answer(who_error_text())


async def _get_user_display(bot: Bot, chat_id: int, user_id: int) -> str:
    """Возвращает отображаемое имя пользователя."""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        user = member.user
        if user.username:
            return f"@{user.username}"
        full = user.first_name or ""
        if user.last_name:
            full += f" {user.last_name}"
        return full or f"user_{user_id}"
    except Exception:
        return f"user_{user_id}"