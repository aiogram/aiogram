from typing import Optional

from pytest import mark, param

from aiogram.enums import ChatAction
from aiogram.types import BufferedInputFile, Chat, ChatPermissions


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

    def test_get_administrators(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.get_administrators()
        assert method.chat_id == chat.id

    def test_delete_message(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.delete_message(message_id=1)
        assert method.chat_id == chat.id

    def test_revoke_invite_link(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.revoke_invite_link(invite_link="test")
        assert method.chat_id == chat.id

    def test_edit_invite_link(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.edit_invite_link(invite_link="test", name="test")
        assert method.chat_id == chat.id

    def test_create_invite_link(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.create_invite_link(name="test")
        assert method.chat_id == chat.id

    def test_export_invite_link(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.export_invite_link()
        assert method.chat_id == chat.id

    def test_do(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.do(ChatAction.TYPING)
        assert method.chat_id == chat.id

    def test_delete_sticker_set(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.delete_sticker_set()
        assert method.chat_id == chat.id

    def test_set_sticker_set(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.set_sticker_set(sticker_set_name="test")
        assert method.chat_id == chat.id

    def test_get_member(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.get_member(user_id=42)
        assert method.chat_id == chat.id

    def test_get_member_count(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.get_member_count()
        assert method.chat_id == chat.id

    def test_leave(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.leave()
        assert method.chat_id == chat.id

    def test_unpin_all_messages(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.unpin_all_messages()
        assert method.chat_id == chat.id

    def test_unpin_message(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.unpin_message()
        assert method.chat_id == chat.id

    def test_pin_message(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.pin_message(message_id=1)
        assert method.chat_id == chat.id

    def test_set_administrator_custom_title(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.set_administrator_custom_title(user_id=1, custom_title="test")
        assert method.chat_id == chat.id

    def test_set_permissions(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.set_permissions(
            permissions=ChatPermissions(
                can_send_messages=True,
            )
        )
        assert method.chat_id == chat.id

    def test_promote(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.promote(
            user_id=42,
            can_manage_chat=True,
        )
        assert method.chat_id == chat.id

    def test_restrict(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.restrict(
            user_id=42,
            permissions=ChatPermissions(
                can_send_messages=True,
            ),
        )
        assert method.chat_id == chat.id

    def test_unban(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.unban(
            user_id=42,
        )
        assert method.chat_id == chat.id

    def test_ban(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.ban(
            user_id=42,
        )
        assert method.chat_id == chat.id

    def test_set_description(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.set_description(description="test")
        assert method.chat_id == chat.id

    def test_set_title(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.set_title(title="test")
        assert method.chat_id == chat.id

    def test_delete_photo(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.delete_photo(description="test")
        assert method.chat_id == chat.id

    def test_set_photo(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.set_photo(photo=BufferedInputFile(b"PNG", filename="photo.png"))
        assert method.chat_id == chat.id

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

    def test_unpin_all_general_forum_topic_messages(self):
        chat = Chat(id=-42, type="supergroup")

        method = chat.unpin_all_general_forum_topic_messages()
        assert method.chat_id == chat.id
