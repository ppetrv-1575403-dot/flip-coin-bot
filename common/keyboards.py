from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from common.texts import DAILY_BTN_TEXT, DUEL_BTN_TEXT, FLIP_COIN_BTN_TEXT

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=FLIP_COIN_BTN_TEXT)],
        [KeyboardButton(text=DAILY_BTN_TEXT), KeyboardButton(text=DUEL_BTN_TEXT)],
    ],
    resize_keyboard=True,
)
