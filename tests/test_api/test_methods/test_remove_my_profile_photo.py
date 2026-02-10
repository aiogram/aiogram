from aiogram.methods import RemoveMyProfilePhoto
from tests.mocked_bot import MockedBot


class TestRemoveMyProfilePhoto:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(RemoveMyProfilePhoto, ok=True, result=True)

        response: bool = await bot.remove_my_profile_photo()
        bot.get_request()
        assert response == prepare_result.result
