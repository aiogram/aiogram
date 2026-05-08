from aiogram.methods import AnswerGuestQuery
from aiogram.types import InlineQueryResultPhoto, SentGuestMessage
from tests.mocked_bot import MockedBot


class TestAnswerGuestQuery:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            AnswerGuestQuery,
            ok=True,
            result=SentGuestMessage(inline_message_id="test"),
        )

        response: SentGuestMessage = await bot.answer_guest_query(
            guest_query_id="test",
            result=InlineQueryResultPhoto(
                id="test",
                photo_url="https://example.com/photo.jpg",
                thumbnail_url="https://example.com/thumb.jpg",
            ),
        )
        bot.get_request()
        assert response == prepare_result.result
