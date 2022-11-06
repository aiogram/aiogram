from __future__ import annotations

from .base import TelegramObject


class VideoChatEnded(TelegramObject):
    """
    This object represents a service message about a video chat ended in the chat.

    Source: https://core.telegram.org/bots/api#videochatended
    """

    duration: int
    """Video chat duration in seconds"""
