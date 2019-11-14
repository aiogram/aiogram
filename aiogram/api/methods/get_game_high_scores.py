from typing import Any, Dict, List, Optional

from ..types import GameHighScore
from .base import Request, TelegramMethod


class GetGameHighScores(TelegramMethod[List[GameHighScore]]):
    """
    Use this method to get data for high score tables. Will return the score of the specified user and several of his neighbors in a game. On success, returns an Array of GameHighScore objects.
    This method will currently return scores for the target user, plus two of his closest neighbors on each side. Will also return the top three users if the user and his neighbors are not among them. Please note that this behavior is subject to change.

    Source: https://core.telegram.org/bots/api#getgamehighscores
    """

    __returning__ = List[GameHighScore]

    user_id: int
    """Target user id"""

    chat_id: Optional[int] = None
    """Required if inline_message_id is not specified. Unique identifier for the target chat"""

    message_id: Optional[int] = None
    """Required if inline_message_id is not specified. Identifier of the sent message"""

    inline_message_id: Optional[str] = None
    """Required if chat_id and message_id are not specified. Identifier of the inline message"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getGameHighScores", data=data)
