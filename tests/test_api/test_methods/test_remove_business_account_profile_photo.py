from aiogram.methods import RemoveBusinessAccountProfilePhoto
from tests.mocked_bot import MockedBot


class TestRemoveBusinessAccountProfilePhoto:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            RemoveBusinessAccountProfilePhoto, ok=True, result=True
        )

        response: bool = await bot.remove_business_account_profile_photo(
            business_connection_id="test_connection_id", is_public=True
        )
        bot.get_request()
        assert response == prepare_result.result
