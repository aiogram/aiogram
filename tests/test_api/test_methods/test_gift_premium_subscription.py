from aiogram.methods import GiftPremiumSubscription
from tests.mocked_bot import MockedBot


class TestGiftPremiumSubscription:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GiftPremiumSubscription, ok=True, result=True)

        response: bool = await bot.gift_premium_subscription(
            user_id=123456789,
            month_count=3,
            star_count=1000,
            text="Enjoy your premium subscription!",
        )
        bot.get_request()
        assert response == prepare_result.result
