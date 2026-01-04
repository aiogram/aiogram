from aiogram.methods import SetBusinessAccountProfilePhoto
from aiogram.types import InputProfilePhotoStatic
from tests.mocked_bot import MockedBot


class TestSetBusinessAccountProfilePhoto:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetBusinessAccountProfilePhoto, ok=True, result=True)

        response: bool = await bot.set_business_account_profile_photo(
            business_connection_id="test_connection_id",
            photo=InputProfilePhotoStatic(photo="test_photo_file_id"),
            is_public=True,
        )
        bot.get_request()
        assert response == prepare_result.result
