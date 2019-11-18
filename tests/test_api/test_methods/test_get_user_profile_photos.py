import pytest
from aiogram.api.methods import GetUserProfilePhotos, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestGetUserProfilePhotos:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetUserProfilePhotos, ok=True, result=None)

        response: UserProfilePhotos = await GetUserProfilePhotos(user_id=...,)
        request: Request = bot.get_request()
        assert request.method == "getUserProfilePhotos"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetUserProfilePhotos, ok=True, result=None)

        response: UserProfilePhotos = await bot.get_user_profile_photos(user_id=...,)
        request: Request = bot.get_request()
        assert request.method == "getUserProfilePhotos"
        # assert request.data == {}
        assert response == prepare_result.result
