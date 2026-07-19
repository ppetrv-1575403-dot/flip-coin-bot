from aiogram import Router, types
from aiogram.filters import Command

from common.keyboards import main_keyboard
from common.texts import START_TEXT, UNKNOWN_MSG_TEXT

# Этот роутер подключается ПОСЛЕДНИМ в bot.py — его catch-all хендлер
# должен ловить только то, что не подошло ни одной фиче.
router = Router(name="core")


@router.message(Command("start"))
async def cmd_start(message: types.Message, logger):
    try:
        await message.answer(START_TEXT, reply_markup=main_keyboard, parse_mode="HTML")
        logger.info("Отправлено приветствие")
    except Exception as e:
        logger.error(f"Ошибка в cmd_start: {e}", exc_info=True)


@router.message()
async def unknown_message(message: types.Message, logger):
    logger.info(UNKNOWN_MSG_TEXT)
    await message.answer(UNKNOWN_MSG_TEXT, reply_markup=main_keyboard)
