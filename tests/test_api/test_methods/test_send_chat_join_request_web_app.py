from aiogram.methods import SendChatJoinRequestWebApp
from tests.mocked_bot import MockedBot


class TestSendChatJoinRequestWebApp:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendChatJoinRequestWebApp, ok=True, result=True)

        response: bool = await bot.send_chat_join_request_web_app(
            chat_join_request_query_id="query_id",
            web_app_url="https://example.com/app",
        )
        bot.get_request()
        assert response == prepare_result.result
