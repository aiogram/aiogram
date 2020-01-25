from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

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
    total_voter_count: int
    """Total number of users that voted in the poll"""
    is_closed: bool
    """True, if the poll is closed"""
    is_anonymous: bool
    """True, if the poll is anonymous"""
    type: str
    """Poll type, currently can be 'regular' or 'quiz'"""
    allows_multiple_answers: bool
    """True, if the poll allows multiple answers"""
    correct_option_id: Optional[int] = None
    """0-based identifier of the correct answer option. Available only for polls in the quiz mode,
    which are closed, or was sent (not forwarded) by the bot or to the private chat with the
    bot."""
