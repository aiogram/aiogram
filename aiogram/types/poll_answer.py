from __future__ import annotations

from typing import TYPE_CHECKING, List

from .base import TelegramObject

if TYPE_CHECKING:
    from .user import User


class PollAnswer(TelegramObject):
    """
    This object represents an answer of a user in a non-anonymous poll.

    Source: https://core.telegram.org/bots/api#pollanswer
    """

    poll_id: str
    """Unique poll identifier"""
    user: User
    """The user, who changed the answer to the poll"""
    option_ids: List[int]
    """0-based identifiers of answer options, chosen by the user. May be empty if the user retracted their vote."""
