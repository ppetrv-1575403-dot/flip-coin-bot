from aiogram.types import Message, TelegramObject

CHAT_GROUP = "group"
CHAT_SUPER_GROUP = "supergroup"

def is_from_group_chat(event: TelegramObject):
    result = False
    if isinstance(event, Message) and event.chat.type in (
                CHAT_GROUP, 
                CHAT_SUPER_GROUP
            ):
        result = True

def is_from_true_user(event: TelegramObject):
    result = False
    if event.from_user and not event.from_user.is_bot:
        result = True

def is_message_from_group(message: Message):
    result = False
    if message.chat.type in (
        CHAT_GROUP, 
        CHAT_SUPER_GROUP):
        result = True
