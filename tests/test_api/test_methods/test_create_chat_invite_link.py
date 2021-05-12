import pytest

from aiogram.methods import CreateChatInviteLink, Request
from aiogram.types import ChatInviteLink, User
from tests.mocked_bot import MockedBot


class TestCreateChatInviteLink:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            CreateChatInviteLink,
            ok=True,
            result=ChatInviteLink(
                invite_link="https://t.me/username",
                creator=User(id=42, is_bot=False, first_name="User"),
                is_primary=False,
                is_revoked=False,
            ),
        )

        response: ChatInviteLink = await CreateChatInviteLink(
            chat_id=-42,
        )
        request: Request = bot.get_request()
        assert request.method == "createChatInviteLink"
        # assert request.data == {"chat_id": -42}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            CreateChatInviteLink,
            ok=True,
            result=ChatInviteLink(
                invite_link="https://t.me/username",
                creator=User(id=42, is_bot=False, first_name="User"),
                is_primary=False,
                is_revoked=False,
            ),
        )

        response: ChatInviteLink = await bot.create_chat_invite_link(
            chat_id=-42,
        )
        request: Request = bot.get_request()
        assert request.method == "createChatInviteLink"
        # assert request.data == {"chat_id": -42}
        assert response == prepare_result.result
