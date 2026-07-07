from aiogram.methods import AnswerChatJoinRequestQuery
from tests.mocked_bot import MockedBot


class TestAnswerChatJoinRequestQuery:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerChatJoinRequestQuery, ok=True, result=True)

        response: bool = await bot.answer_chat_join_request_query(
            chat_join_request_query_id="query_id",
            result="approve",
        )
        bot.get_request()
        assert response == prepare_result.result
