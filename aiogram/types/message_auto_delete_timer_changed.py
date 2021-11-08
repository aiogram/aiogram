from __future__ import annotations

from .base import TelegramObject


class MessageAutoDeleteTimerChanged(TelegramObject):
    """
    This object represents a service message about a change in auto-delete timer settings.

    Source: https://core.telegram.org/bots/api#messageautodeletetimerchanged
    """

    message_auto_delete_time: int
    """New auto-delete time for messages in the chat; in seconds"""
