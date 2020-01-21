from abc import ABC

from aiogram.api.types import InlineQuery, User
from aiogram.dispatcher.handler import BaseHandler


class InlineQueryHandler(BaseHandler[InlineQuery], ABC):
    """
    Base class for inline query handlers
    """

    @property
    def from_user(self) -> User:
        return self.event.from_user

    @property
    def query(self) -> str:
        return self.event.query
