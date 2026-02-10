from aiogram.methods import GetMyStarBalance
from aiogram.types import StarAmount
from tests.mocked_bot import MockedBot


class TestGetMyStarBalance:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetMyStarBalance,
            ok=True,
            result=StarAmount(
                amount=100,
            ),
        )

        response: StarAmount = await bot.get_my_star_balance()
        bot.get_request()
        assert response == prepare_result.result
