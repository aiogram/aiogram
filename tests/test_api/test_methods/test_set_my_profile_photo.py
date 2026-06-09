from aiogram.methods import SetMyProfilePhoto
from aiogram.types import InputProfilePhotoStatic
from tests.mocked_bot import MockedBot


class TestSetMyProfilePhoto:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetMyProfilePhoto, ok=True, result=True)

        response: bool = await bot.set_my_profile_photo(
            photo=InputProfilePhotoStatic(photo="file_id")
        )
        bot.get_request()
        assert response == prepare_result.result
