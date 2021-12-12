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
