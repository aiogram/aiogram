import pytest

from aiogram.methods import EditChatInviteLink, Request
from aiogram.types import ChatInviteLink, User
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestEditChatInviteLink:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            EditChatInviteLink,
            ok=True,
            result=ChatInviteLink(
                invite_link="https://t.me/username2",
                creator=User(id=42, is_bot=False, first_name="User"),
                is_primary=False,
                is_revoked=False,
            ),
        )

        response: ChatInviteLink = await EditChatInviteLink(
            chat_id=-42, invite_link="https://t.me/username", member_limit=1
        )
        request: Request = bot.get_request()
        assert request.method == "editChatInviteLink"
        # assert request.data == {}
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            EditChatInviteLink,
            ok=True,
            result=ChatInviteLink(
                invite_link="https://t.me/username2",
                creator=User(id=42, is_bot=False, first_name="User"),
                is_primary=False,
                is_revoked=False,
            ),
        )

        response: ChatInviteLink = await bot.edit_chat_invite_link(
            chat_id=-42, invite_link="https://t.me/username", member_limit=1
        )
        request: Request = bot.get_request()
        assert request.method == "editChatInviteLink"
        # assert request.data == {}
        assert response == prepare_result.result
