import datetime
from typing import Any

from aiogram.filters import CommandObject
from aiogram.handlers import MessageHandler, MessageHandlerCommandMixin
from aiogram.types import Chat, Message, User


class MyHandler(MessageHandler):
    async def handle(self) -> Any:
        return self.event.text


class TestClassBasedMessageHandler:
    async def test_message_handler(self):
        event = Message(
            message_id=42,
            date=datetime.datetime.now(),
            text="test",
            chat=Chat(id=42, type="private"),
            from_user=User(id=42, is_bot=False, first_name="Test"),
        )
        handler = MyHandler(event=event)

        assert handler.from_user == event.from_user
        assert handler.chat == event.chat


class HandlerWithCommand(MessageHandlerCommandMixin, MessageHandler):
    async def handle(self) -> Any:
        return self.command


class TestBaseMessageHandlerCommandMixin:
    def test_command_accessible(self):
        handler = HandlerWithCommand(
            Message(
                message_id=42,
                date=datetime.datetime.now(),
                text="/test args",
                chat=Chat(id=42, type="private"),
                from_user=User(id=42, is_bot=False, first_name="Test"),
            ),
            command=CommandObject(prefix="/", command="command", args="args"),
        )

        assert isinstance(handler.command, CommandObject)
        assert handler.command.command == "command"

    def test_command_not_presented(self):
        handler = HandlerWithCommand(
            Message(
                message_id=42,
                date=datetime.datetime.now(),
                text="test",
                chat=Chat(id=42, type="private"),
                from_user=User(id=42, is_bot=False, first_name="Test"),
            )
        )

        assert handler.command is None
