import datetime
from aiogram.types import Chat, Message
from tests.mocked_bot import MockedBot


class TestGetMessageUrl:
    def test_method(self, bot: MockedBot):
        fake_message_id = 10

        fake_chat_pm = Chat(id=123456, username="username", type="private")
        fake_message = Message(
            message_id=fake_message_id,
            date=datetime.datetime.now(),
            text="test",
            chat=fake_chat_pm,
        )

        # get_url() in PM must return None
        assert fake_message.get_url() is None

        # get_url() in basic group must return None
        fake_chat_group = Chat(id=-123456, username="username", type="group")
        fake_message = Message(
            message_id=fake_message_id,
            date=datetime.datetime.now(),
            text="test",
            chat=fake_chat_group,
        )
        assert fake_message.get_url() is None

        # get_url() in supergroup without username must return private link
        fake_chat_supergroup_no_username = Chat(id=-1001234567890, type="supergroup")
        fake_message = Message(
            message_id=fake_message_id,
            date=datetime.datetime.now(),
            text="test",
            chat=fake_chat_supergroup_no_username,
        )
        assert fake_message.chat.shifted_id == 1234567890
        assert fake_message.get_url() == f"https://t.me/c/1234567890/{fake_message_id}"

        # get_url() in supergroup with username must return link with username or private link
        # if force_private set to True
        fake_chat_supergroup_username = Chat(
            id=-1001234567890, username="username", type="supergroup"
        )
        fake_message = Message(
            message_id=fake_message_id,
            date=datetime.datetime.now(),
            text="test",
            chat=fake_chat_supergroup_username,
        )
        assert fake_message.chat.shifted_id == 1234567890
        assert fake_message.get_url() == f"https://t.me/username/{fake_message_id}"
        assert (
            fake_message.get_url(force_private=True)
            == f"https://t.me/c/1234567890/{fake_message_id}"
        )

        # get_url() in channel without username must return private link
        fake_chat_channel_no_username = Chat(id=-1001234567890, type="channel")
        fake_message = Message(
            message_id=fake_message_id,
            date=datetime.datetime.now(),
            text="test",
            chat=fake_chat_channel_no_username,
        )
        assert fake_message.chat.shifted_id == 1234567890
        assert fake_message.get_url() == f"https://t.me/c/1234567890/{fake_message_id}"

        # get_url() in channel with username must return link with username or private link
        # if force_private set to True
        fake_chat_channel_username = Chat(id=-1001234567890, username="username", type="channel")
        fake_message = Message(
            message_id=fake_message_id,
            date=datetime.datetime.now(),
            text="test",
            chat=fake_chat_channel_username,
        )
        assert fake_message.chat.shifted_id == 1234567890
        assert fake_message.get_url() == f"https://t.me/username/{fake_message_id}"
        assert (
            fake_message.get_url(force_private=True)
            == f"https://t.me/c/1234567890/{fake_message_id}"
        )
