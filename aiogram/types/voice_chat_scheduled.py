from __future__ import annotations

from typing import TYPE_CHECKING

from .base import TelegramObject

if TYPE_CHECKING:  # pragma: no cover
    pass


class VoiceChatScheduled(TelegramObject):
    """
    This object represents a service message about a voice chat scheduled in the chat.

    Source: https://core.telegram.org/bots/api#voicechatscheduled
    """

    start_date: int
    """Point in time (Unix timestamp) when the voice chat is supposed to be started by a chat administrator"""
