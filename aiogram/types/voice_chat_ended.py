from __future__ import annotations

from .base import TelegramObject


class VoiceChatEnded(TelegramObject):
    """
    This object represents a service message about a voice chat ended in the chat.

    Source: https://core.telegram.org/bots/api#voicechatended
    """

    duration: int
    """Voice chat duration in seconds"""
