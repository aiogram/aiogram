from aiogram.methods import AnswerWidgetQuery
from tests.mocked_bot import MockedBot


class TestAnswerWidgetQuery:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerWidgetQuery, ok=True, result=True)

        response: bool = await bot.answer_widget_query(widget_query_id="id", data="data")
        bot.get_request()
        assert response == prepare_result.result
