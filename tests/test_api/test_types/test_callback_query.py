from aiogram.api.methods import AnswerCallbackQuery
from aiogram.api.types import CallbackQuery, User


class TestCallbackQuery:
    def test_answer_alias(self):
        callback_query = CallbackQuery(
            id="id", from_user=User(id=42, is_bot=False, first_name="name"), chat_instance="chat"
        )

        api_method = callback_query.answer()

        assert isinstance(api_method, AnswerCallbackQuery)
        assert api_method.callback_query_id == callback_query.id
