import logging

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from features.ads.texts import ad_text
from repositories.flip_repo import FlipCounterRepository

AD_INTERVAL = 5  # показываем рекламу каждые N подбрасываний


class AdService:
    def __init__(self, ad_links: list[str], flip_repo: FlipCounterRepository, logger: logging.Logger):
        self._ad_links = ad_links
        self._flip_repo = flip_repo
        self._logger = logger

    def _get_link(self, flip_count: int) -> str:
        if not self._ad_links:
            return ""
        idx = (flip_count // AD_INTERVAL) % len(self._ad_links)
        return self._ad_links[idx]

    async def maybe_show_ad(self, user_id: int, message: Message) -> None:
        if not self._ad_links:
            return

        # Счётчик в Redis — переживает рестарт и корректно работает
        # при нескольких инстансах бота.
        current_flips = await self._flip_repo.increment(user_id)
        if current_flips % AD_INTERVAL != 0:
            return

        ad_link = self._get_link(current_flips)
        if not ad_link:
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Перейти к партнеру", url=ad_link)]
        ])
        await message.answer(ad_text, parse_mode="HTML", reply_markup=keyboard)
        self._logger.info(f"✅ Показана реклама пользователю {user_id} (подбрасываний: {current_flips})")
