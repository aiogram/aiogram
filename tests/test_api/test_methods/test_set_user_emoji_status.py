from datetime import datetime, timedelta

from aiogram.methods import SetUserEmojiStatus
from tests.mocked_bot import MockedBot


class TestSetUserEmojiStatus:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetUserEmojiStatus, ok=True, result=True)

        response: bool = await bot.set_user_emoji_status(
            user_id=42,
            emoji_status_custom_emoji_id="emoji_status_custom_emoji_id",
            emoji_status_expiration_date=datetime.now() + timedelta(days=1),
        )
        bot.get_request()
        assert response == prepare_result.result
