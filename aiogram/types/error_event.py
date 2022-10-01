from aiogram.types import Update
from aiogram.types.base import MutableTelegramObject


class ErrorEvent(MutableTelegramObject):
    """
    Internal event, should be used to receive errors while processing Updates from Telegram
    """

    update: Update
    """Received update"""
    exception: Exception
    """Exception"""

    class Config:
        arbitrary_types_allowed = True
