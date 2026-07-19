import uuid

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from features.vote import texts as vote_texts
from features.vote.service import MAX_OPTIONS, calculate_vote_results
from infra.rng import QuantumRNG
from repositories.vote_repo import VoteRepository

router = Router(name="vote")


def _build_keyboard(vote_id: str, options: list[str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=option, callback_data=f"vote_opt:{vote_id}:{idx}")]
        for idx, option in enumerate(options)
    ]
    rows.append([InlineKeyboardButton(text=vote_texts.vote_results_btn, callback_data=f"vote_results:{vote_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("vote"))
async def create_vote(message: types.Message, vote_repo: VoteRepository):
    raw = message.text.partition(" ")[2].strip()
    options = [opt.strip() for opt in raw.split(";") if opt.strip()]

    if len(options) < 2:
        await message.answer(vote_texts.vote_usage_msg, parse_mode="HTML")
        return
    if len(options) > MAX_OPTIONS:
        await message.answer(vote_texts.get_too_many_options_msg(MAX_OPTIONS))
        return

    vote_id = uuid.uuid4().hex[:8]
    await vote_repo.create(vote_id, options, message.from_user.id)

    await message.answer(
        vote_texts.get_vote_created_msg(options),
        parse_mode="HTML",
        reply_markup=_build_keyboard(vote_id, options),
    )


@router.callback_query(F.data.startswith("vote_opt:"))
async def register_vote(callback: CallbackQuery, vote_repo: VoteRepository):
    _, vote_id, idx_str = callback.data.split(":")
    data = await vote_repo.add_vote(vote_id, callback.from_user.id, int(idx_str))

    if data is None:
        await callback.answer(vote_texts.vote_not_found_msg, show_alert=True)
        return

    await callback.answer(vote_texts.vote_registered_msg)


@router.callback_query(F.data.startswith("vote_results:"))
async def show_vote_results(callback: CallbackQuery, vote_repo: VoteRepository, qrng: QuantumRNG):
    vote_id = callback.data.split(":")[1]
    data = await vote_repo.get(vote_id)

    if data is None:
        await callback.answer(vote_texts.vote_not_found_msg, show_alert=True)
        return

    winners, was_tiebreak = await calculate_vote_results(data, qrng)
    text = vote_texts.get_results_msg(data["options"], data["votes"], winners, was_tiebreak)

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()
