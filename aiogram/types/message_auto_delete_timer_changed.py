from __future__ import annotations

from typing import TYPE_CHECKING

from .base import TelegramObject

if TYPE_CHECKING:  # pragma: no cover
    pass


class MessageAutoDeleteTimerChanged(TelegramObject):
    """
    This object represents a service message about a change in auto-delete timer settings.

    Source: https://core.telegram.org/bots/api#messageautodeletetimerchanged
    """

    message_auto_delete_time: int
    """New auto-delete time for messages in the chat"""
