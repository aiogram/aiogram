import pytest

from aiogram.methods import GetUserProfilePhotos, Request
from aiogram.types import PhotoSize, UserProfilePhotos
from tests.mocked_bot import MockedBot


class TestGetUserProfilePhotos:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetUserProfilePhotos,
            ok=True,
            result=UserProfilePhotos(
                total_count=1,
                photos=[
                    [PhotoSize(file_id="file_id", width=42, height=42, file_unique_id="file id")]
                ],
            ),
        )

        response: UserProfilePhotos = await GetUserProfilePhotos(user_id=42)
        request: Request = bot.get_request()
        assert request.method == "getUserProfilePhotos"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetUserProfilePhotos,
            ok=True,
            result=UserProfilePhotos(
                total_count=1,
                photos=[
                    [PhotoSize(file_id="file_id", width=42, height=42, file_unique_id="file id")]
                ],
            ),
        )

        response: UserProfilePhotos = await bot.get_user_profile_photos(user_id=42)
        request: Request = bot.get_request()
        assert request.method == "getUserProfilePhotos"
        assert response == prepare_result.result
