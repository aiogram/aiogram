from aiogram.types import Update
from aiogram.types.base import MutableTelegramObject


class ErrorEvent(MutableTelegramObject):
    update: Update
    exception: Exception

    class Config:
        arbitrary_types_allowed = True
