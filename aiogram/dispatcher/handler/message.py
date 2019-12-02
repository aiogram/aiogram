from abc import ABC

from aiogram.api.types import Message
from aiogram.dispatcher.handler.base import BaseHandler


class MessageHandler(BaseHandler, ABC):
    event: Message

    @property
    def from_user(self):
        return self.event.from_user

    @property
    def chat(self):
        return self.event.chat
