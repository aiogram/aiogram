import datetime

from aiogram.methods import ApproveChatJoinRequest, DeclineChatJoinRequest
from aiogram.types import Chat, ChatJoinRequest, User


class TestChatJoinRequest:
    def test_approve_alias(self):
        chat_join_request = ChatJoinRequest(
            chat=Chat(id=-42, type="supergroup"),
            from_user=User(id=42, is_bot=False, first_name="Test"),
            date=datetime.datetime.now(),
        )

        api_method = chat_join_request.approve()

        assert isinstance(api_method, ApproveChatJoinRequest)
        assert api_method.chat_id == chat_join_request.chat.id
        assert api_method.user_id == chat_join_request.from_user.id

    def test_decline_alias(self):
        chat_join_request = ChatJoinRequest(
            chat=Chat(id=-42, type="supergroup"),
            from_user=User(id=42, is_bot=False, first_name="Test"),
            date=datetime.datetime.now(),
        )

        api_method = chat_join_request.decline()

        assert isinstance(api_method, DeclineChatJoinRequest)
        assert api_method.chat_id == chat_join_request.chat.id
        assert api_method.user_id == chat_join_request.from_user.id
