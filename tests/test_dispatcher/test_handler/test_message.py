from typing import Any

import pytest

from aiogram.dispatcher.filters import CommandObject
from aiogram.dispatcher.handler.message import MessageHandler, MessageHandlerCommandMixin
from tests.factories.message import MessageFactory


class MyHandler(MessageHandler):
    async def handle(self) -> Any:
        return self.event.text


class TestClassBasedMessageHandler:
    @pytest.mark.asyncio
    async def test_message_handler(self):
        event = MessageFactory()
        handler = MyHandler(event=event)

        assert handler.from_user == event.from_user
        assert handler.chat == event.chat


class HandlerWithCommand(MessageHandlerCommandMixin, MessageHandler):
    async def handle(self) -> Any:
        return self.command


class TestBaseMessageHandlerCommandMixin:
    def test_command_accessible(self):
        handler = HandlerWithCommand(
            MessageFactory(text="/test args"),
            command=CommandObject(prefix="/", command="command", args="args"),
        )

        assert isinstance(handler.command, CommandObject)
        assert handler.command.command == "command"

    def test_command_not_presented(self):
        handler = HandlerWithCommand(MessageFactory())

        assert handler.command is None
