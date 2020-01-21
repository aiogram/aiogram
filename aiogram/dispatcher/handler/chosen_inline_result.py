from abc import ABC

from aiogram.api.types import ChosenInlineResult, User
from aiogram.dispatcher.handler import BaseHandler


class ChosenInlineResultHandler(BaseHandler[ChosenInlineResult], ABC):
    """
    Base class for chosen inline result handlers
    """

    @property
    def from_user(self) -> User:
        return self.event.from_user

    @property
    def query(self) -> str:
        return self.event.query
