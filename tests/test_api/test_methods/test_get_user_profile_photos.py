from aiogram.methods import GetUserProfilePhotos
from aiogram.types import PhotoSize, UserProfilePhotos
from tests.mocked_bot import MockedBot


class TestGetUserProfilePhotos:
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
        bot.get_request()
        assert response == prepare_result.result
