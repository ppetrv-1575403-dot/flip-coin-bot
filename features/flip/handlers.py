import asyncio

from aiogram import F, Router, types
from aiogram.filters import Command

from common.keyboards import main_keyboard
from common.texts import FLIP_COIN_BTN_TEXT, get_cache_size_status_msg, qstatus_answer
from features.ads.service import AdService
from features.flip.texts import get_flip_answer_msg
from infra.rng import QuantumRNG

router = Router(name="flip")


@router.message(F.text.in_([FLIP_COIN_BTN_TEXT, "/flip"]))
async def flip_coin(
    message: types.Message,
    qrng: QuantumRNG,
    ad_service: AdService,
    coin_animation_id: str,
    logger,
):
    try:
        user_id = message.from_user.id

        if coin_animation_id:
            try:
                anim_msg = await message.answer_animation(
                    animation=coin_animation_id,
                    caption="Монетка подброшена...",
                )
                await asyncio.sleep(2)
                await anim_msg.delete()
            except Exception as e:
                logger.warning(f"Ошибка анимации: {e}")

        bit = await qrng.get_bit()
        answer = get_flip_answer_msg(bit)
        logger.info(f"Результат flip: {answer}")

        await message.answer(answer, parse_mode="HTML", reply_markup=main_keyboard)
        await ad_service.maybe_show_ad(user_id, message)
    except Exception as e:
        logger.error(f"Ошибка в flip_coin: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка. Попробуй позже.")


@router.message(Command("qstatus"))
async def q_status(message: types.Message, qrng: QuantumRNG, logger):
    status = get_cache_size_status_msg(qrng.pool_size, qrng.refill_threshold)
    answer = qstatus_answer(qrng.pool_size, status)
    logger.info(answer)
    await message.answer(answer)
