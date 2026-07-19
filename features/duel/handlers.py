from aiogram import Bot, F, Router, types
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from common.texts import DUEL_BTN_TEXT
from features.duel import texts as duel_texts
from features.duel.service import DUEL_PATTERN, generate_duel_id, is_bot_url_match, remove_bot_name
from infra.rng import QuantumRNG
from repositories.duel_repo import DuelRepository

router = Router(name="duel")


@router.message(F.text.regexp(DUEL_PATTERN))
async def accept_duel(message: types.Message, qrng: QuantumRNG, duel_repo: DuelRepository, bot: Bot, logger):
    match = DUEL_PATTERN.match(message.text)
    if not match:
        await message.answer(duel_texts.duel_wrong_link_msg)
        return

    duel_id = match.group(1)
    bit = await qrng.get_shared_bit(duel_id)

    # Отправляем результат принимающему (Пользователь Б)
    await message.answer(duel_texts.get_duel_answer_msg(bit, duel_id), parse_mode="HTML")

    # Отправляем результат создателю (Пользователь А)
    creator_chat_id = await duel_repo.get_creator(duel_id)
    if creator_chat_id:
        try:
            await bot.send_message(
                chat_id=creator_chat_id,
                text=duel_texts.get_duel_complete_msg(bit),
                parse_mode="HTML",
            )
            logger.info(f"Уведомление отправлено создателю {creator_chat_id}")
        except Exception as e:
            logger.warning(f"Не удалось уведомить создателя {creator_chat_id}: {e}")

        await duel_repo.delete(duel_id)
    else:
        logger.warning(f"Создатель спора {duel_id} не найден в Redis")


@router.message(F.text.in_([DUEL_BTN_TEXT, "/duel"]))
async def create_duel(message: types.Message, duel_repo: DuelRepository, bot_username: str):
    duel_id = generate_duel_id()
    await duel_repo.save_creator(duel_id, message.chat.id)

    duel_url = duel_texts.get_duel_url(bot_username, duel_id)
    share_text = duel_texts.get_duel_share_msg(duel_url)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=duel_texts.duel_select_user_msg, switch_inline_query=share_text)],
        [InlineKeyboardButton(text=duel_texts.duel_copy_link_msg, callback_data=f"copy_duel:{duel_id}")],
        [InlineKeyboardButton(text=duel_texts.duel_status_msg, callback_data=f"check_duel:{duel_id}")],
    ])

    await message.answer(duel_texts.duel_accept_answer_msg, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("copy_duel:"))
async def copy_duel_link(callback: CallbackQuery, bot_username: str):
    duel_id = callback.data.split(":")[1]
    duel_url = duel_texts.get_duel_url(bot_username, duel_id)

    await callback.message.answer(duel_texts.get_callback_copy_duel_url(duel_url), parse_mode="HTML")
    await callback.answer(duel_texts.copy_link_answer_msg)


@router.callback_query(F.data.startswith("check_duel:"))
async def check_duel_status(callback: CallbackQuery, duel_repo: DuelRepository):
    duel_id = callback.data.split(":")[1]
    exists = await duel_repo.exists(duel_id)

    if exists:
        await callback.answer(duel_texts.duel_not_accepted_msg, show_alert=True)
    else:
        await callback.answer(duel_texts.duel_completed_msg, show_alert=True)


@router.inline_query()
async def handle_inline_duel(inline_query: InlineQuery, logger):
    query_text = inline_query.query.strip()
    logger.info(f"📨 Inline query received: {query_text!r}")

    if "start=duel_" in query_text:
        url_match = is_bot_url_match(query_text)
        if url_match:
            duel_url = url_match.group(0)
            clean_text = remove_bot_name(query_text)

            result = InlineQueryResultArticle(
                id="duel_share",
                title=duel_texts.send_duel_settlement_msg,
                description=duel_texts.press_to_send_msg,
                input_message_content=InputTextMessageContent(
                    message_text=clean_text,
                    parse_mode="HTML",
                ),
                url=duel_url,
                hide_url=False,
            )
            await inline_query.answer([result], cache_time=1)
            return

    await inline_query.answer([], cache_time=1)
