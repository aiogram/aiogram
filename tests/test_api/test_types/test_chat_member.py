import pytest

from aiogram.api.types import ChatMember, User


class TestChatMember:
    def setup(self):
        self.__user = User(id=42, is_bot=False, first_name="User", last_name=None)

    @pytest.mark.parametrize(
        "status, expected_status",
        [
            ["administrator", True],
            ["creator", True],
            ["member", False],
            ["restricted", False],
            ["kicked", False],
            ["left", False],
            ["durov", False],  # not a valid status value, method should return False
        ],
    )
    def test_is_chat_admin(self, status: str, expected_status: bool):
        chat_member = ChatMember(user=self.__user, status=status)
        assert chat_member.is_chat_admin == expected_status

    @pytest.mark.parametrize(
        "status, expected_status",
        [
            ["administrator", True],
            ["creator", True],
            ["member", True],
            ["restricted", True],
            ["kicked", False],
            ["left", False],
            ["onotole", False],  # not a valid status value, method should return False
        ],
    )
    def test_is_chat_member(self, status: str, expected_status: bool):
        chat_member = ChatMember(user=self.__user, status=status)
        assert chat_member.is_chat_member == expected_status
