from __future__ import annotations

import datetime

from .base import TelegramObject


class VideoChatScheduled(TelegramObject):
    """
    This object represents a service message about a video chat scheduled in the chat.

    Source: https://core.telegram.org/bots/api#videochatscheduled
    """

    start_date: datetime.datetime
    """Point in time (Unix timestamp) when the video chat is supposed to be started by a chat administrator"""
