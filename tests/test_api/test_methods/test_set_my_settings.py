from aiogram.methods import SetMySettings
from tests.mocked_bot import MockedBot


class TestSetMySettings:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetMySettings, ok=True, result=True)

        response: bool = await bot.set_my_settings(
            has_topic_sidebar=True, callback_query_mode="auto"
        )
        request = bot.get_request()
        assert request.has_topic_sidebar is True
        assert request.callback_query_mode == "auto"
        assert response == prepare_result.result
