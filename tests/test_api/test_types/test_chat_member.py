import pytest

from tests.factories.chat_member import ChatMemberFactory


class TestChatMember:
    @pytest.mark.parametrize(
        "status,result", [["administrator", True], ["creator", True], ["member", False]]
    )
    def test_is_chat_admin(self, status: str, result: bool):
        chat_member = ChatMemberFactory(status=status)
        assert chat_member.is_chat_admin == result

    @pytest.mark.parametrize(
        "status,result",
        [
            ["administrator", True],
            ["creator", True],
            ["member", True],
            ["restricted", True],
            ["kicked", False],
            ["left", False],
        ],
    )
    def test_is_chat_member(self, status: str, result: bool):
        chat_member = ChatMemberFactory(status=status)
        assert chat_member.is_chat_member == result
