from typing import Optional

from pytest import mark, param

from aiogram.types import Chat


class TestChat:
    def test_ban_sender_chat(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.ban_sender_chat(sender_chat_id=-1337)
        assert method.chat_id == chat.id
        assert method.sender_chat_id == -1337

    def test_unban_sender_chat(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.unban_sender_chat(sender_chat_id=-1337)
        assert method.chat_id == chat.id
        assert method.sender_chat_id == -1337

    @mark.parametrize(
        "first,last,title,chat_type,result",
        [
            param("First", None, None, "private", "First", id="private_first_only"),
            param("First", "Last", None, "private", "First Last", id="private_with_last"),
            param(None, None, "Title", "group", "Title", id="group_with_title"),
            param(None, None, "Title", "supergroup", "Title", id="supergroup_with_title"),
            param(None, None, "Title", "channel", "Title", id="channel_with_title"),
        ],
    )
    def test_full_name(
        self,
        first: Optional[str],
        last: Optional[str],
        title: Optional[str],
        chat_type: str,
        result: str,
    ):
        chat = Chat(id=42, first_name=first, last_name=last, title=title, type=chat_type)
        assert chat.full_name == result
