from abc import ABC
from typing import Optional, cast

from aiogram.api.types import Chat, Message, User
from aiogram.dispatcher.filters import CommandObject
from aiogram.dispatcher.handler.base import BaseHandler, BaseHandlerMixin


class MessageHandler(BaseHandler[Message], ABC):
    """
    Base class for message handlers
    """

    @property
    def from_user(self) -> Optional[User]:
        return self.event.from_user

    @property
    def chat(self) -> Chat:
        return self.event.chat


class MessageHandlerCommandMixin(BaseHandlerMixin[Message]):
    @property
    def command(self) -> Optional[CommandObject]:
        if "command" in self.data:
            return cast(CommandObject, self.data["command"])
        return None
