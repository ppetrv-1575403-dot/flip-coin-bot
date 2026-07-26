import asyncio
import logging
import uuid

from aiogram import Router, Bot, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command, CommandObject
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from infra.rng import QuantumRNG
from repositories.vote_repo import VoteRepository
from .parser import parse_vote_args
from .service import calculate_quantum_results
from .schemas import (
    VoteError,
    EmptyQuestionError,
    TooManyOptionsError,
    QuestionTooLongError,
    OptionTooLongError,
    InvalidDurationError,
)
from .texts import (
    vote_help_text,
    vote_created_text,
    vote_result_text,
    vote_details_text,
)

logger = logging.getLogger(__name__)

router = Router(name="vote")

# Хранилище активных таймеров (vote_id -> asyncio.Task)
active_timers: dict[str, asyncio.Task] = {}


async def finalize_vote(
    vote_id: str,
    bot: Bot,
    chat_id: int,
    qrng: QuantumRNG,
    vote_repo: VoteRepository,
) -> None:
    """
    Подсчёт результатов и отправка интерактивного сообщения.
    Защита от гонки через атомарный mark_completed.
    """
    # Атомарно пытаемся завершить голосование
    if not await vote_repo.mark_completed(vote_id):
        return  # кто-то уже завершил

    vote_data = await vote_repo.get(vote_id)
    if vote_data is None:
        return

    result = await calculate_quantum_results(vote_data, qrng)
    options = vote_data["options"]
    winner = options[result.winner_idx]

    # Сохраняем результат в Redis для кнопки «Показать детали»
    await vote_repo.save_result(vote_id, {
        "winner_idx": result.winner_idx,
        "weights": result.weights,
        "probabilities": result.probabilities,
        "total_votes": result.total_votes,
        "is_low_votes": result.is_low_votes,
    })

    text = vote_result_text(
        winner=winner,
        options=options,
        weights=result.weights,
        probabilities=result.probabilities,
        total_votes=result.total_votes,
        is_low_votes=result.is_low_votes,
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔍 Показать детали",
            callback_data=f"vote_details:{vote_id}",
        )]
    ])

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except (TelegramForbiddenError, TelegramBadRequest) as e:
        logger.warning(
            "Не удалось отправить результат голосования %s: %s", vote_id, e
        )


def schedule_timer(
    vote_id: str,
    duration: int,
    bot: Bot,
    chat_id: int,
    qrng: QuantumRNG,
    vote_repo: VoteRepository,
) -> None:
    """Запускает asyncio.Task для автоматического подсчёта."""
    async def _wait_and_finalize():
        try:
            await asyncio.sleep(duration)
            await finalize_vote(vote_id, bot, chat_id, qrng, vote_repo)
        except asyncio.CancelledError:
            logger.info(
                "Таймер голосования %s отменён (досрочный подсчёт).", vote_id
            )
        finally:
            active_timers.pop(vote_id, None)

    task = asyncio.create_task(_wait_and_finalize())
    active_timers[vote_id] = task


@router.message(Command("vote"))
async def handle_vote(
    message: Message,
    command: CommandObject,
    bot: Bot,
    qrng: QuantumRNG,
    vote_repo: VoteRepository,
):
    args = command.args or ""

    try:
        vote_request = parse_vote_args(args)
    except EmptyQuestionError as e:
        await message.answer(vote_help_text(error=e), parse_mode="HTML")
        return
    except (
        TooManyOptionsError,
        QuestionTooLongError,
        OptionTooLongError,
        InvalidDurationError,
    ) as e:
        await message.answer(f"⚠️ {e}")
        return
    except VoteError as e:
        await message.answer(f"⚠️ Ошибка голосования: {e}")
        return

    vote_id = str(uuid.uuid4())

    await vote_repo.create(
        vote_id=vote_id,
        chat_id=message.chat.id,
        creator_id=message.from_user.id,
        options=vote_request.options,
        duration=vote_request.duration,
        is_anonymous=vote_request.is_anonymous,
    )

    # Кнопки голосования + кнопка «📊 Итоги»
    vote_buttons = [
        [InlineKeyboardButton(
            text=opt,
            callback_data=f"vote_cast:{vote_id}:{idx}",
        )]
        for idx, opt in enumerate(vote_request.options)
    ]
    vote_buttons.append([
        InlineKeyboardButton(
            text="📊 Итоги",
            callback_data=f"vote_finish:{vote_id}",
        )
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=vote_buttons)

    text = vote_created_text(
        question=vote_request.question,
        duration=vote_request.duration,
        is_anonymous=vote_request.is_anonymous,
    )

    try:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    except (TelegramForbiddenError, TelegramBadRequest) as e:
        await message.answer(f"⚠️ Не удалось создать голосование: {e}")
        return

    # Запускаем таймер
    schedule_timer(
        vote_id=vote_id,
        duration=vote_request.duration,
        bot=bot,
        chat_id=message.chat.id,
        qrng=qrng,
        vote_repo=vote_repo,
    )


@router.callback_query(F.data.startswith("vote_cast:"))
async def handle_cast_vote(callback: CallbackQuery, vote_repo: VoteRepository):
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Ошибка формата.", show_alert=True)
        return

    vote_id = parts[1]
    try:
        option_idx = int(parts[2])
    except ValueError:
        await callback.answer("Ошибка формата.", show_alert=True)
        return

    # Проверяем, не завершено ли голосование
    vote_data = await vote_repo.get(vote_id)
    if vote_data is None or vote_data["completed"]:
        await callback.answer("Голосование уже завершено. ⏳", show_alert=True)
        return

    success = await vote_repo.add_vote(vote_id, callback.from_user.id, option_idx)
    if success:
        await callback.answer("Голос учтён! ✅")
    else:
        await callback.answer("Вы уже голосовали. 🤔", show_alert=True)


@router.callback_query(F.data.startswith("vote_finish:"))
async def handle_finish_vote(
    callback: CallbackQuery,
    bot: Bot,
    qrng: QuantumRNG,
    vote_repo: VoteRepository,
):
    vote_id = callback.data.split(":", 1)[1]

    # Отменяем таймер, если он ещё активен
    task = active_timers.pop(vote_id, None)
    if task and not task.done():
        task.cancel()

    await finalize_vote(
        vote_id=vote_id,
        bot=bot,
        chat_id=callback.message.chat.id,
        qrng=qrng,
        vote_repo=vote_repo,
    )

    await callback.answer("Подводим итоги... 🎲")


@router.callback_query(F.data.startswith("vote_details:"))
async def handle_vote_details(callback: CallbackQuery, vote_repo: VoteRepository):
    vote_id = callback.data.split(":", 1)[1]
    vote_data = await vote_repo.get(vote_id)

    if vote_data is None or vote_data["result"] is None:
        await callback.answer("Результат ещё не подсчитан.", show_alert=True)
        return

    result = vote_data["result"]
    options = vote_data["options"]
    winner = options[result["winner_idx"]]

    text = vote_details_text(
        winner=winner,
        options=options,
        weights=result["weights"],
        probabilities=result["probabilities"],
        total_votes=result["total_votes"],
    )

    try:
        await callback.message.edit_text(text, parse_mode="HTML")
    except TelegramBadRequest:
        pass  # сообщение не изменилось или недоступно

    await callback.answer()