import datetime
from typing import Any

import pytest

from aiogram.api.types import Chat, Message, User
from aiogram.dispatcher.handler.message import MessageHandler


class MyHandler(MessageHandler):
    async def handle(self) -> Any:
        return self.event.text


class TestClassBasedMessageHandler:
    @pytest.mark.asyncio
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
