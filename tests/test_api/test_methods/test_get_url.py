import datetime

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
    def test_get_url_non_topic_message(
        self,
        bot: MockedBot,
        chat_type: str,
        chat_id: int,
        chat_username: str | None,
        force_private: bool,
        expected_result: str | None,
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
            assert (
                fake_message.get_url(force_private=force_private, include_thread_id=True) is None
            )
        else:
            assert fake_message.get_url(force_private=force_private) == expected_result
            assert (
                fake_message.get_url(force_private=force_private, include_thread_id=True)
                == expected_result
            )

    @pytest.mark.parametrize(
        "chat_username,force_private,include_thread_id,fake_thread_id_topic,expected_result",
        [
            [None, False, False, None, "https://t.me/c/1234567890/10"],
            [None, False, False, 3, "https://t.me/c/1234567890/10"],
            [None, False, True, None, "https://t.me/c/1234567890/10"],
            [None, False, True, 3, "https://t.me/c/1234567890/3/10"],
            [None, True, False, None, "https://t.me/c/1234567890/10"],
            [None, True, False, 3, "https://t.me/c/1234567890/10"],
            [None, True, True, None, "https://t.me/c/1234567890/10"],
            [None, True, True, 3, "https://t.me/c/1234567890/3/10"],
            ["name", False, False, None, "https://t.me/name/10"],
            ["name", False, False, 3, "https://t.me/name/10"],
            ["name", False, True, None, "https://t.me/name/10"],
            ["name", False, True, 3, "https://t.me/name/3/10"],
            ["name", True, False, None, "https://t.me/c/1234567890/10"],
            ["name", True, False, 3, "https://t.me/c/1234567890/10"],
            ["name", True, True, None, "https://t.me/c/1234567890/10"],
            ["name", True, True, 3, "https://t.me/c/1234567890/3/10"],
        ],
    )
    def test_get_url_if_topic_message(
        self,
        bot: MockedBot,
        chat_username: str | None,
        force_private: bool,
        include_thread_id: bool,
        fake_thread_id_topic: int | None,
        expected_result: str | None,
    ):
        fake_message_id = 10
        fake_chat_id = -1001234567890
        fake_chat_type = "supergroup"
        fake_chat_with_topics = Chat(
            id=fake_chat_id, username=chat_username, type=fake_chat_type, is_forum=True
        )
        fake_message_from_topic = Message(
            message_id=fake_message_id,
            date=datetime.datetime.now(),
            text="test",
            chat=fake_chat_with_topics,
            is_topic_message=True,
            message_thread_id=fake_thread_id_topic,
        )
        actual_result = fake_message_from_topic.get_url(
            force_private=force_private, include_thread_id=include_thread_id
        )
        assert actual_result == expected_result
