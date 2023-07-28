from aiogram.methods import AnswerWebAppQuery
from aiogram.types import InlineQueryResultPhoto, SentWebAppMessage
from tests.mocked_bot import MockedBot


class TestAnswerWebAppQuery:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerWebAppQuery, ok=True, result=SentWebAppMessage())

        response: SentWebAppMessage = await bot.answer_web_app_query(
            web_app_query_id="test",
            result=InlineQueryResultPhoto(
                id="test",
                photo_url="test",
                thumbnail_url="test",
            ),
        )
        request = bot.get_request()
        assert response == prepare_result.result
