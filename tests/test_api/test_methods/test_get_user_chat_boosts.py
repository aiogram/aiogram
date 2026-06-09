from datetime import datetime, timedelta
from random import randint

from aiogram.methods import GetUserChatBoosts
from aiogram.types import (
    ChatBoost,
    ChatBoostSourceGiveaway,
    ChatBoostSourcePremium,
    User,
    UserChatBoosts,
)
from tests.mocked_bot import MockedBot


class TestGetUserChatBoosts:
    async def test_bot_method(self, bot: MockedBot):
        now = datetime.now()
        user = User(
            id=randint(200, 500),
            is_bot=False,
            first_name="name",
        )
        prepare_result = bot.add_result_for(
            GetUserChatBoosts,
            ok=True,
            result=UserChatBoosts(
                boosts=[
                    ChatBoost(
                        boost_id="eggs",
                        add_date=now - timedelta(days=7),
                        expiration_date=now + timedelta(days=14),
                        source=ChatBoostSourceGiveaway(
                            giveaway_message_id=randint(100, 300),
                        ),
                    ),
                    ChatBoost(
                        boost_id="spam",
                        add_date=now - timedelta(days=3),
                        expiration_date=now + timedelta(days=21),
                        source=ChatBoostSourcePremium(user=user),
                    ),
                ]
            ),
        )

        response: UserChatBoosts = await bot.get_user_chat_boosts(
            chat_id=randint(100, 200),
            user_id=user.id,
        )
        request = bot.get_request()
        assert request
        assert response == prepare_result.result
