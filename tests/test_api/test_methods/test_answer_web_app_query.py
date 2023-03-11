from aiogram.methods import AnswerWebAppQuery, Request
from aiogram.types import InlineQueryResult, SentWebAppMessage
from tests.mocked_bot import MockedBot


class TestAnswerWebAppQuery:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerWebAppQuery, ok=True, result=SentWebAppMessage())

        response: SentWebAppMessage = await bot.answer_web_app_query(
            web_app_query_id="test",
            result=InlineQueryResult(),
        )
        request = bot.get_request()
        assert response == prepare_result.result
