from __future__ import annotations

from typing import Optional

from ..types import InlineKeyboardMarkup, Message
from ..types.base import UNSET_PROTECT_CONTENT
from .base import TelegramMethod


class SendGame(TelegramMethod[Message]):
    """
    Use this method to send a game. On success, the sent :class:`aiogram.types.message.Message` is returned.

    Source: https://core.telegram.org/bots/api#sendgame
    """

    __returning__ = Message
    __api_method__ = "sendGame"

    chat_id: int
    """Unique identifier for the target chat"""
    game_short_name: str
    """Short name of the game, serves as the unique identifier for the game. Set up your games via `@BotFather <https://t.me/botfather>`_."""
    message_thread_id: Optional[int] = None
    """Unique identifier for the target message thread (topic) of the forum; for forum supergroups only"""
    disable_notification: Optional[bool] = None
    """Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    protect_content: Optional[bool] = UNSET_PROTECT_CONTENT
    """Protects the contents of the sent message from forwarding and saving"""
    reply_to_message_id: Optional[int] = None
    """If the message is a reply, ID of the original message"""
    allow_sending_without_reply: Optional[bool] = None
    """Pass :code:`True` if the message should be sent even if the specified replied-to message is not found"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_. If empty, one 'Play game_title' button will be shown. If not empty, the first button must launch the game."""
