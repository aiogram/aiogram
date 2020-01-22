from abc import ABC
from typing import List

from aiogram.api.types import Poll, PollOption
from aiogram.dispatcher.handler import BaseHandler


class PollHandler(BaseHandler[Poll], ABC):
    """
    Base class for poll handlers
    """

    @property
    def question(self) -> str:
        return self.event.question

    @property
    def options(self) -> List[PollOption]:
        return self.event.options
