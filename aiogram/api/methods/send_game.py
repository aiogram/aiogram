from typing import Any, Dict, Optional

from ..types import InlineKeyboardMarkup, Message
from .base import Request, TelegramMethod


class SendGame(TelegramMethod[Message]):
    """
    Use this method to send a game. On success, the sent Message is returned.

    Source: https://core.telegram.org/bots/api#sendgame
    """

    __returning__ = Message

    chat_id: int
    """Unique identifier for the target chat"""

    game_short_name: str
    """Short name of the game, serves as the unique identifier for the game. Set up your games via Botfather."""

    disable_notification: Optional[bool] = None
    """Sends the message silently. Users will receive a notification with no sound."""

    reply_to_message_id: Optional[int] = None
    """If the message is a reply, ID of the original message"""

    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for an inline keyboard. If empty, one ‘Play game_title’ button will be shown. If not empty, the first button must launch the game."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(exclude_unset=True, exclude={})
        files: Dict[str, Any] = {}
        return Request(method="sendGame", data=data, files=files)
