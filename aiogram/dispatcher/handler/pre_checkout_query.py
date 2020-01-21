from abc import ABC

from aiogram.api.types import PreCheckoutQuery, User
from aiogram.dispatcher.handler import BaseHandler


class PreCheckoutQueryHandler(BaseHandler[PreCheckoutQuery], ABC):
    """
    Base class for pre-checkout handlers
    """

    @property
    def from_user(self) -> User:
        return self.event.from_user
