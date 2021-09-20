from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from ..types import InlineKeyboardMarkup, Message
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class SendGame(TelegramMethod[Message]):
    """
    Use this method to send a game. On success, the sent :class:`aiogram.types.message.Message` is returned.

    Source: https://core.telegram.org/bots/api#sendgame
    """

    __returning__ = Message

    chat_id: int
    """Unique identifier for the target chat"""
    game_short_name: str
    """Short name of the game, serves as the unique identifier for the game. Set up your games via `Botfather <https://t.me/botfather>`_."""
    disable_notification: Optional[bool] = None
    """Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    reply_to_message_id: Optional[int] = None
    """If the message is a reply, ID of the original message"""
    allow_sending_without_reply: Optional[bool] = None
    """Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_. If empty, one 'Play game_title' button will be shown. If not empty, the first button must launch the game."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="sendGame", data=data)
