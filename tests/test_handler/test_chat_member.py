import datetime
from typing import Any

from aiogram.handlers import ChatMemberHandler
from aiogram.types import Chat, ChatMemberMember, ChatMemberUpdated, User


class TestChatMemberUpdated:
    async def test_attributes_aliases(self):
        event = ChatMemberUpdated(
            chat=Chat(id=42, type="private"),
            from_user=User(id=42, is_bot=False, first_name="Test"),
            date=datetime.datetime.now(),
            old_chat_member=ChatMemberMember(user=User(id=42, is_bot=False, first_name="Test")),
            new_chat_member=ChatMemberMember(user=User(id=42, is_bot=False, first_name="Test")),
        )

        class MyHandler(ChatMemberHandler):
            async def handle(self) -> Any:
                assert self.event == event
                assert self.from_user == self.event.from_user

                return True

        assert await MyHandler(event)
