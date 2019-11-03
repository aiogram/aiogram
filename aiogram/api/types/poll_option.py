from __future__ import annotations

from .base import TelegramObject


class PollOption(TelegramObject):
    """
    This object contains information about one answer option in a poll.

    Source: https://core.telegram.org/bots/api#polloption
    """

    text: str
    """Option text, 1-100 characters"""
    voter_count: int
    """Number of users that voted for this option"""
