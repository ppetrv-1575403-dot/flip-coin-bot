from aiogram import F, Router, types

from common.texts import DAILY_BTN_TEXT
from features.daily.service import get_daily_prediction_text
from infra.rng import QuantumRNG
from repositories.daily_repo import DailyRepository

router = Router(name="daily")


@router.message(F.text.in_([DAILY_BTN_TEXT, "/daily"]))
async def daily_forecast(message: types.Message, qrng: QuantumRNG, daily_repo: DailyRepository):
    user_id = message.from_user.id

    cached = await daily_repo.get_result(user_id)
    if cached:
        await message.answer(cached, parse_mode="HTML")
        return

    bit = await qrng.get_bit()
    prediction = get_daily_prediction_text(user_id, bit)

    await daily_repo.save_result(user_id, prediction)
    await message.answer(prediction, parse_mode="HTML")
