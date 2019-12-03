from abc import ABC
from typing import Optional

from aiogram.api.types import Message
from aiogram.dispatcher.filters import CommandObject
from aiogram.dispatcher.handler.base import BaseHandler, BaseHandlerMixin


class MessageHandler(BaseHandler, ABC):
    event: Message

    @property
    def from_user(self):
        return self.event.from_user

    @property
    def chat(self):
        return self.event.chat


class MessageHandlerCommandMixin(BaseHandlerMixin):
    @property
    def command(self) -> Optional[CommandObject]:
        if "command" in self.data:
            return self.command["data"]
        return None
