from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types.base import MutableTelegramObject

if TYPE_CHECKING:
    from .update import Update


class _ErrorEvent(MutableTelegramObject):
    class Config:
        arbitrary_types_allowed = True


class ErrorEvent(_ErrorEvent):
    """
    Internal event, should be used to receive errors while processing Updates from Telegram

    Source: https://core.telegram.org/bots/api#error-event
    """

    update: Update
    """Received update"""
    exception: Exception
    """Exception"""
