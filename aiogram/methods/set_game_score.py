from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from ..types import Message
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class SetGameScore(TelegramMethod[Union[Message, bool]]):
    """
    Use this method to set the score of the specified user in a game message. On success, if the message is not an inline message, the :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned. Returns an error, if the new score is not greater than the user's current score in the chat and *force* is :code:`False`.

    Source: https://core.telegram.org/bots/api#setgamescore
    """

    __returning__ = Union[Message, bool]

    user_id: int
    """User identifier"""
    score: int
    """New score, must be non-negative"""
    force: Optional[bool] = None
    """Pass :code:`True` if the high score is allowed to decrease. This can be useful when fixing mistakes or banning cheaters"""
    disable_edit_message: Optional[bool] = None
    """Pass :code:`True` if the game message should not be automatically edited to include the current scoreboard"""
    chat_id: Optional[int] = None
    """Required if *inline_message_id* is not specified. Unique identifier for the target chat"""
    message_id: Optional[int] = None
    """Required if *inline_message_id* is not specified. Identifier of the sent message"""
    inline_message_id: Optional[str] = None
    """Required if *chat_id* and *message_id* are not specified. Identifier of the inline message"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="setGameScore", data=data)
