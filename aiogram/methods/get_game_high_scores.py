from __future__ import annotations

from typing import List, Optional

from ..types import GameHighScore
from .base import TelegramMethod


class GetGameHighScores(TelegramMethod[List[GameHighScore]]):
    """
    Use this method to get data for high score tables. Will return the score of the specified user and several of their neighbors in a game. Returns an Array of :class:`aiogram.types.game_high_score.GameHighScore` objects.

     This method will currently return scores for the target user, plus two of their closest neighbors on each side. Will also return the top three users if the user and their neighbors are not among them. Please note that this behavior is subject to change.

    Source: https://core.telegram.org/bots/api#getgamehighscores
    """

    __returning__ = List[GameHighScore]
    __api_method__ = "getGameHighScores"

    user_id: int
    """Target user id"""
    chat_id: Optional[int] = None
    """Required if *inline_message_id* is not specified. Unique identifier for the target chat"""
    message_id: Optional[int] = None
    """Required if *inline_message_id* is not specified. Identifier of the sent message"""
    inline_message_id: Optional[str] = None
    """Required if *chat_id* and *message_id* are not specified. Identifier of the inline message"""
