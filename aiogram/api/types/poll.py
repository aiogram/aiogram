from __future__ import annotations

from typing import TYPE_CHECKING, List

from .base import TelegramObject

if TYPE_CHECKING:  # pragma: no cover
    from .poll_option import PollOption


class Poll(TelegramObject):
    """
    This object contains information about a poll.

    Source: https://core.telegram.org/bots/api#poll
    """

    id: str
    """Unique poll identifier"""
    question: str
    """Poll question, 1-255 characters"""
    options: List[PollOption]
    """List of poll options"""
    is_closed: bool
    """True, if the poll is closed"""
