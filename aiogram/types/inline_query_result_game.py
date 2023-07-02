from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Optional

from ..enums import InlineQueryResultType
from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:
    from .inline_keyboard_markup import InlineKeyboardMarkup


class InlineQueryResultGame(InlineQueryResult):
    """
    Represents a `Game <https://core.telegram.org/bots/api#games>`_.
    **Note:** This will only work in Telegram versions released after October 1, 2016. Older clients will not display any inline results if a game result is among them.

    Source: https://core.telegram.org/bots/api#inlinequeryresultgame
    """

    type: Literal[InlineQueryResultType.GAME] = InlineQueryResultType.GAME
    """Type of the result, must be *game*"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    game_short_name: str
    """Short name of the game"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """*Optional*. `Inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_ attached to the message"""
