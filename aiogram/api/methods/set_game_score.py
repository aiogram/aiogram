from typing import Any, Dict, Optional, Union

from .base import Request, TelegramMethod
from ..types import Message


class SetGameScore(TelegramMethod[Union[Message, bool]]):
    """
    Use this method to set the score of the specified user in a game. On success, if the message was sent by the bot, returns the edited Message, otherwise returns True. Returns an error, if the new score is not greater than the user's current score in the chat and force is False.

    Source: https://core.telegram.org/bots/api#setgamescore
    """

    __returning__ = Union[Message, bool]

    user_id: int
    """User identifier"""

    score: int
    """New score, must be non-negative"""

    force: Optional[bool] = None
    """Pass True, if the high score is allowed to decrease. This can be useful when fixing mistakes or banning cheaters"""

    disable_edit_message: Optional[bool] = None
    """Pass True, if the game message should not be automatically edited to include the current scoreboard"""

    chat_id: Optional[int] = None
    """Required if inline_message_id is not specified. Unique identifier for the target chat"""

    message_id: Optional[int] = None
    """Required if inline_message_id is not specified. Identifier of the sent message"""

    inline_message_id: Optional[str] = None
    """Required if chat_id and message_id are not specified. Identifier of the inline message"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(exclude_unset=True, exclude={})

        return Request(method="setGameScore", data=data)
