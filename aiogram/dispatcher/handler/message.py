from abc import ABC
from typing import Optional

from aiogram.api.types import Message, User, Chat
from aiogram.dispatcher.filters import CommandObject
from aiogram.dispatcher.handler.base import BaseHandler, BaseHandlerMixin


class MessageHandler(BaseHandler, ABC):
    event: Message

    @property
    def from_user(self) -> User:
        return self.event.from_user

    @property
    def chat(self) -> Chat:
        return self.event.chat


class MessageHandlerCommandMixin(BaseHandlerMixin):
    @property
    def command(self) -> Optional[CommandObject]:
        if "command" in self.data:
            return self.data["command"]
        return None
