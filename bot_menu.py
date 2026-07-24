from aiogram import Bot 
from aiogram.types import BotCommand

start_command_description="Запуск бота и знакомство"
daily_command_description="Квантовое предсказание на день"
flip_command_description="Честное подбрасывание монетки ⚛️"
vote_command_description="Создать голосование в чате"
who_command_description="Случайный выбор участника группы"


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description=start_command_description),
        BotCommand(command="daily", description=flip_command_description),
        BotCommand(command="flip", description=flip_command_description),
        BotCommand(command="vote", description=vote_command_description),
        BotCommand(command="who", description=who_command_description)
    ]
    await bot.set_my_commands(commands)
