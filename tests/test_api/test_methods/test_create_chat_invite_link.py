from aiogram.methods import CreateChatInviteLink
from aiogram.types import ChatInviteLink, User
from tests.mocked_bot import MockedBot


class TestCreateChatInviteLink:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            CreateChatInviteLink,
            ok=True,
            result=ChatInviteLink(
                invite_link="https://t.me/username",
                creator=User(id=42, is_bot=False, first_name="User"),
                is_primary=False,
                is_revoked=False,
                creates_join_request=False,
            ),
        )

        response: ChatInviteLink = await bot.create_chat_invite_link(
            chat_id=-42,
        )
        request = bot.get_request()
        assert response == prepare_result.result
