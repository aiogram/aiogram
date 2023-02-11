import datetime
from typing import Optional

import pytest

from aiogram.types import Chat, Message
from tests.mocked_bot import MockedBot


class TestGetMessageUrl:
    @pytest.mark.parametrize(
        "chat_type,chat_id,chat_username,force_private,expected_result",
        [
            ["private", 123456, "username", False, None],
            ["group", -123456, "username", False, None],
            ["supergroup", -1001234567890, None, False, "https://t.me/c/1234567890/10"],
            ["supergroup", -1001234567890, None, True, "https://t.me/c/1234567890/10"],
            ["supergroup", -1001234567890, "username", False, "https://t.me/username/10"],
            ["supergroup", -1001234567890, "username", True, "https://t.me/c/1234567890/10"],
            ["channel", -1001234567890, None, False, "https://t.me/c/1234567890/10"],
            ["channel", -1001234567890, None, True, "https://t.me/c/1234567890/10"],
            ["channel", -1001234567890, "username", False, "https://t.me/username/10"],
            ["channel", -1001234567890, "username", True, "https://t.me/c/1234567890/10"],
            # 2 extra cases: 9-digit ID and 11-digit ID (without "-100")
            ["supergroup", -100123456789, None, True, "https://t.me/c/123456789/10"],
            ["supergroup", -10012345678901, None, True, "https://t.me/c/12345678901/10"],
        ],
    )
    def test_method(
        self,
        bot: MockedBot,
        chat_type: str,
        chat_id: int,
        chat_username: Optional[str],
        force_private: bool,
        expected_result: Optional[str],
    ):
        fake_chat = Chat(id=chat_id, username=chat_username, type=chat_type)
        fake_message_id = 10
        fake_message = Message(
            message_id=fake_message_id,
            date=datetime.datetime.now(),
            text="test",
            chat=fake_chat,
        )

        if expected_result is None:
            assert fake_message.get_url(force_private=force_private) is None
        else:
            assert fake_message.get_url(force_private=force_private) == expected_result
