from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:  # pragma: no cover
    from .inline_keyboard_markup import InlineKeyboardMarkup


class InlineQueryResultGame(InlineQueryResult):
    """
    Represents a Game.
    Note: This will only work in Telegram versions released after October 1, 2016. Older clients
    will not display any inline results if a game result is among them.

    Source: https://core.telegram.org/bots/api#inlinequeryresultgame
    """

    type: str = Field("game", const=True)
    """Type of the result, must be game"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    game_short_name: str
    """Short name of the game"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """Inline keyboard attached to the message"""
