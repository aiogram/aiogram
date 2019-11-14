from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .base import TelegramObject

if TYPE_CHECKING:
    from .user import User
    from .location import Location


class ChosenInlineResult(TelegramObject):
    """
    Represents a result of an inline query that was chosen by the user and sent to their chat partner.
    Note: It is necessary to enable inline feedback via @Botfather in order to receive these objects in updates.

    Source: https://core.telegram.org/bots/api#choseninlineresult
    """

    result_id: str
    """The unique identifier for the result that was chosen"""
    from_user: User = Field(..., alias="from")
    """The user that chose the result"""
    query: str
    """The query that was used to obtain the result"""
    location: Optional[Location] = None
    """Sender location, only for bots that require user location"""
    inline_message_id: Optional[str] = None
    """Identifier of the sent inline message. Available only if there is an inline keyboard attached to the message. Will be also received in callback queries and can be used to edit the message."""
