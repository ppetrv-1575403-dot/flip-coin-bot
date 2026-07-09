import os
from dotenv import load_dotenv

from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
)

from aiogram import types

from constants import logger, NO_AD_LINK_ERR_MSG

AD_INTERVAL = 5

POOL_SIZE = 500

TRESHOLD = 100

ad_links = []


# ═══════════════════════ СЧЕТЧИК ПОЛЬЗОВАТЕЛЕЙ ═══════════════════════
# Словарь для хранения количества подбрасываний монетки каждым пользователем.
# Ключ: user_id, Значение: количество подбрасываний.
user_flip_counts = {}


def load_ad_links():
    load_dotenv()
    i = 1
    link = os.environ.get("AD_LINK_{i}", "")
    while(len(link) > 0):
        link = os.environ.get("AD_LINK_{i}", "")
        if link:
            ad_links.append(link)
            i += 1
        else:
            break
    #if not ad_links:
    #    raise RuntimeError(NO_AD_LINK_ERR_MSG)


def get_link(flip_count):
    if not ad_links:
        return ""
    idx = flip_count / AD_INTERVAL
    if idx  >= len(ad_links):
        idx = 0
    return ad_links[idx]


def calc_user_flip_coins(user_id):
    # 1. Увеличиваем счетчик подбрасываний для текущего пользователя
    user_flip_counts[user_id] = user_flip_counts.get(user_id, 0) + 1
    current_flips = user_flip_counts[user_id]
    return current_flips


async def show_ad(user_id, message: types.Message):
    current_flips = calc_user_flip_coins(user_id)
    ad_link = get_link(current_flips)
    if not ad_link:
        return
    # Показываем рекламный баннер каждые 5 подбрасываний (5, 10, 15...)
    if current_flips % AD_INTERVAL == 0:
        # Создаем inline-кнопку для перехода
        ad_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Перейти к партнеру", url= ad_link)]
        ])
        
        # Вариант А: Отправка текстового баннера
        await message.answer(ad_text, parse_mode="HTML", reply_markup=ad_kb)
        
        # Вариант Б: Если хотите отправить КАРТИНКУ-БАННЕР, 
        # закомментируйте строку выше (Вариант А) и раскомментируйте этот блок:
        #
        # ad_photo_url = "https://путь_к_вашей_картинке.jpg" # Или используйте file_id картинки
        # await message.answer_photo(
        #     photo=ad_photo_url,
        #     caption=ad_text,
        #     parse_mode="HTML",
        #     reply_markup=ad_kb
        # )
        
        logger.info(f"✅ Показана реклама пользователю {user_id} (всего подбрасываний: {current_flips})")
