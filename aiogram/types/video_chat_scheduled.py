from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from .base import TelegramObject

if TYPE_CHECKING:
    pass


class VideoChatScheduled(TelegramObject):
    """
    This object represents a service message about a video chat scheduled in the chat.

    Source: https://core.telegram.org/bots/api#videochatscheduled
    """

    start_date: datetime
    """Point in time (Unix timestamp) when the video chat is supposed to be started by a chat administrator"""
