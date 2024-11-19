from datetime import timedelta

from aiogram.methods import CreateChatSubscriptionInviteLink
from aiogram.types import ChatInviteLink, User
from tests.mocked_bot import MockedBot


class TestCreateChatSubscriptionInviteLink:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            CreateChatSubscriptionInviteLink,
            ok=True,
            result=ChatInviteLink(
                invite_link="https://t.me/username",
                creator=User(id=42, is_bot=False, first_name="User"),
                is_primary=False,
                is_revoked=False,
                creates_join_request=False,
            ),
        )

        response: ChatInviteLink = await bot.create_chat_subscription_invite_link(
            chat_id=-42,
            subscription_period=timedelta(days=30),
            subscription_price=42,
        )
        request = bot.get_request()
        assert response == prepare_result.result
