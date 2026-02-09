from aiogram.methods import GetUserProfileAudios
from aiogram.types import Audio, UserProfileAudios
from tests.mocked_bot import MockedBot


class TestGetUserProfileAudios:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetUserProfileAudios,
            ok=True,
            result=UserProfileAudios(
                total_count=1,
                audios=[
                    Audio(file_id="file_id", file_unique_id="file_unique_id", duration=120)
                ],
            ),
        )

        response: UserProfileAudios = await bot.get_user_profile_audios(user_id=42)
        bot.get_request()
        assert response == prepare_result.result
