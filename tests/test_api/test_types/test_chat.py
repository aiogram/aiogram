import pytest

from aiogram.api.types import Chat
from typing import Optional


class TestChat:
    @pytest.mark.parametrize(
        "chat_type,title,first_name,last_name,result",
        [
            ["private", None, 'name', None, 'name'],
            ["private", None, 'name', 'surname', 'name surname'],
            ["supergroup", 'Chat title', None, None, 'Chat title']
        ]
    )
    def test_full_name(self, chat_type: Optional[str], title: Optional[str], first_name: Optional[str],
                       last_name: Optional[str], result):
        chat = Chat(id=0, type=chat_type, title=title, first_name=first_name, last_name=last_name)
        assert chat.full_name == result

    @pytest.mark.parametrize(
        "chat_type,title,first_name,last_name,username,result",
        [
            ["private", None, 'name', None, None, 'name'],
            ["supergroup", None, 'name', None, None, None],
            ["private", None, 'name', None, 'user', '@user'],
            ["supergroup", None, 'name', None, 'user', '@user']
        ]
    )
    def test_mention(self, chat_type: Optional[str], title: Optional[str], first_name: Optional[str],
                     last_name: Optional[str], username: Optional[str], result):
        chat = Chat(id=0, type=chat_type, title=title, first_name=first_name, last_name=last_name, username=username)
        assert chat.mention == result

    @pytest.mark.parametrize(
        "chat_type,chat_id,result",
        [
            ["private", 123124123, 'tg://user?id=123124123'],
            ["channel", -10032432324, None]
        ]
    )
    def test_user_url(self, chat_type: Optional[str], chat_id: int, result):
        chat = Chat(type=chat_type, id=chat_id)
        if chat_type != 'private':
            with pytest.raises(TypeError):
                assert chat.user_url
        else:
            assert chat.user_url == result
