import logging

from aiogram import Dispatcher, BotCommand

from config import Settings
from features.ads.service import AdService
from features.core.handlers import router as core_router
from features.daily.handlers import router as daily_router
from features.daily.service import DAILY_TTL
from features.duel.handlers import router as duel_router
from features.duel.service import DUEL_TTL
from features.flip.handlers import router as flip_router
from features.vote.handlers import router as vote_router
from features.vote.service import VOTE_TTL
from infra.redis_client import RedisClient
from infra.rng import QuantumRNG
from repositories.daily_repo import DailyRepository
from repositories.duel_repo import DuelRepository
from repositories.flip_repo import FlipCounterRepository
from repositories.vote_repo import VoteRepository


async def build_dispatcher(
    settings: Settings,
    redis_client: RedisClient,
    qrng: QuantumRNG,
    logger: logging.Logger,
) -> Dispatcher:
    """
    Собирает Dispatcher: создаёт репозитории и сервисы, кладёт их в
    workflow-данные диспетчера (dp["имя"] = объект), после чего aiogram
    сам подставляет их в хендлеры по имени параметра — без глобальных
    синглтонов и ручного протаскивания зависимостей через импорты.
    """
    dp = Dispatcher()

    await set_commands(bot)
    
    duel_repo = DuelRepository(redis_client, DUEL_TTL)
    daily_repo = DailyRepository(redis_client, DAILY_TTL)
    vote_repo = VoteRepository(redis_client, VOTE_TTL)
    flip_repo = FlipCounterRepository(redis_client)
    ad_service = AdService(settings.ad_links, flip_repo, logger)

    dp["qrng"] = qrng
    dp["duel_repo"] = duel_repo
    dp["daily_repo"] = daily_repo
    dp["vote_repo"] = vote_repo
    dp["ad_service"] = ad_service
    dp["bot_username"] = settings.bot_username
    dp["coin_animation_id"] = settings.coin_animation_id
    dp["logger"] = logger

    # Порядок важен: core_router содержит catch-all и должен быть последним.
    dp.include_router(flip_router)
    dp.include_router(duel_router)
    dp.include_router(daily_router)
    dp.include_router(vote_router)
    dp.include_router(core_router)

    return dp


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запуск бота и знакомство"),
        BotCommand(command="daily", description="Квантовое предсказание на день"),
        BotCommand(command="flip", description="Честное подбрасывание монетки ⚛️"),
        BotCommand(command="vote", description="Создать голосование в чате"),
        BotCommand(command="who", description="Случайный выбор участника группы")
    ]
    await bot.set_my_commands(commands)
