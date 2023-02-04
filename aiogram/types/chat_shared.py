from aiogram.types import TelegramObject


class ChatShared(TelegramObject):
    """
    This object contains information about the chat whose identifier was shared with the bot using a :class:`aiogram.types.keyboard_button_request_chat.KeyboardButtonRequestChat` button.

    Source: https://core.telegram.org/bots/api#chatshared
    """

    request_id: int
    """Identifier of the request"""
    chat_id: int
    """Identifier of the shared chat. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a 64-bit integer or double-precision float type are safe for storing this identifier. The bot may not have access to the chat and could be unable to use this identifier, unless the chat is already known to the bot by some other means."""
