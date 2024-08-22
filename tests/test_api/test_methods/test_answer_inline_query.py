from aiogram.methods import AnswerInlineQuery
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from tests.mocked_bot import MockedBot


class TestAnswerInlineQuery:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerInlineQuery, ok=True, result=True)

        response: bool = await bot.answer_inline_query(
            inline_query_id="query id",
            results=[
                InlineQueryResultArticle(
                    id="1",
                    title="title",
                    input_message_content=InputTextMessageContent(message_text="text"),
                )
            ],
        )
        request = bot.get_request()
        assert response == prepare_result.result
