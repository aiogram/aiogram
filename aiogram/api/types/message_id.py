from __future__ import annotations

from .base import TelegramObject


class MessageId(TelegramObject):
    """
    This object represents a unique message identifier.

    Source: https://core.telegram.org/bots/api#messageid
    """

    message_id: int
    """Unique message identifier"""
