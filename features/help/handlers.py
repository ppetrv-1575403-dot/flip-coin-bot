from aiogram import Router, types
from aiogram.filters import Command
from features.help.texts import HELP_TEXT

router = Router()


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(HELP_TEXT, parse_mode="HTML")