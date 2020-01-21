from abc import ABC
from typing import Optional

from aiogram.api.types import CallbackQuery, Message, User
from aiogram.dispatcher.handler import BaseHandler


class CallbackQueryHandler(BaseHandler[CallbackQuery], ABC):
    """
    Base class for callback query handlers
    """

    @property
    def from_user(self) -> User:
        return self.event.from_user

    @property
    def message(self) -> Optional[Message]:
        return self.event.message

    @property
    def callback_data(self) -> Optional[str]:
        return self.event.data
