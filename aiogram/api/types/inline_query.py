from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .base import TelegramObject

if TYPE_CHECKING:  # pragma: no cover
    from .location import Location
    from .user import User


class InlineQuery(TelegramObject):
    """
    This object represents an incoming inline query. When the user sends an empty query, your bot
    could return some default or trending results.

    Source: https://core.telegram.org/bots/api#inlinequery
    """

    id: str
    """Unique identifier for this query"""
    from_user: User = Field(..., alias="from")
    """Sender"""
    query: str
    """Text of the query (up to 256 characters)"""
    offset: str
    """Offset of the results to be returned, can be controlled by the bot"""
    location: Optional[Location] = None
    """Sender location, only for bots that request user location"""
