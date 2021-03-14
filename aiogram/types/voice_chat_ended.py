from __future__ import annotations

from typing import TYPE_CHECKING

from .base import TelegramObject

if TYPE_CHECKING:  # pragma: no cover
    pass


class VoiceChatEnded(TelegramObject):
    """
    This object represents a service message about a voice chat ended in the chat.

    Source: https://core.telegram.org/bots/api#voicechatended
    """

    duration: int
    """Voice chat duration; in seconds"""
