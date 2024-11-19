from datetime import datetime

from aiogram.methods import GetStarTransactions
from aiogram.types import (
    File,
    StarTransaction,
    StarTransactions,
    TransactionPartnerUser,
    User,
)
from tests.mocked_bot import MockedBot


class TestGetStarTransactions:
    async def test_bot_method(self, bot: MockedBot):
        user = User(id=42, is_bot=False, first_name="Test")
        prepare_result = bot.add_result_for(
            GetStarTransactions,
            ok=True,
            result=StarTransactions(
                transactions=[
                    StarTransaction(
                        id="test1",
                        user=user,
                        amount=1,
                        date=datetime.now(),
                        source=TransactionPartnerUser(
                            user=user,
                        ),
                    ),
                    StarTransaction(
                        id="test2",
                        user=user,
                        amount=1,
                        date=datetime.now(),
                        receiver=TransactionPartnerUser(
                            user=user,
                        ),
                    ),
                ]
            ),
        )

        response: File = await bot.get_star_transactions(limit=10, offset=0)
        request = bot.get_request()
        assert response == prepare_result.result
