from __future__ import annotations

from typing import Optional

from .base import TelegramObject


class ResponseParameters(TelegramObject):
    """
    Contains information about why a request was unsuccessful.

    Source: https://core.telegram.org/bots/api#responseparameters
    """

    migrate_to_chat_id: Optional[int] = None
    """The group has been migrated to a supergroup with the specified identifier. This number may
    be greater than 32 bits and some programming languages may have difficulty/silent defects
    in interpreting it. But it is smaller than 52 bits, so a signed 64 bit integer or
    double-precision float type are safe for storing this identifier."""
    retry_after: Optional[int] = None
    """In case of exceeding flood control, the number of seconds left to wait before the request
    can be repeated"""
