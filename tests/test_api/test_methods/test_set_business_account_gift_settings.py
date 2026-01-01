from aiogram.methods import SetBusinessAccountGiftSettings
from aiogram.types import AcceptedGiftTypes
from tests.mocked_bot import MockedBot


class TestSetBusinessAccountGiftSettings:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetBusinessAccountGiftSettings, ok=True, result=True)

        response: bool = await bot.set_business_account_gift_settings(
            business_connection_id="test_connection_id",
            show_gift_button=True,
            accepted_gift_types=AcceptedGiftTypes(
                gifts_from_channels=True,
                unlimited_gifts=True,
                limited_gifts=True,
                unique_gifts=True,
                premium_subscription=True,
            ),
        )
        request = bot.get_request()
        assert response == prepare_result.result
