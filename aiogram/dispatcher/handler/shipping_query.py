from abc import ABC

from aiogram.api.types import ShippingQuery, User
from aiogram.dispatcher.handler import BaseHandler


class ShippingQueryHandler(BaseHandler[ShippingQuery], ABC):
    """
    Base class for shipping query handlers
    """

    @property
    def from_user(self) -> User:
        return self.event.from_user
