from aiogram.methods import AnswerCallbackQuery
from aiogram.types import CallbackQuery, InaccessibleMessage, Message, User


class TestCallbackQuery:
    def test_answer_alias(self):
        callback_query = CallbackQuery(
            id="id", from_user=User(id=42, is_bot=False, first_name="name"), chat_instance="chat"
        )

        kwargs = {"text": "foo", "show_alert": True, "url": "https://foo.bar/", "cache_time": 123}

        api_method = callback_query.answer(**kwargs)

        assert isinstance(api_method, AnswerCallbackQuery)
        assert api_method.callback_query_id == callback_query.id

        for key, value in kwargs.items():
            assert getattr(api_method, key) == value

    def test_parse_message(self):
        data = {
            "id": "id",
            "from": {"id": 42, "is_bot": False, "first_name": "name"},
            "message": {
                "message_id": 123,
                "date": 1234567890,
                "chat": {"id": 42, "type": "private"},
            },
            "chat_instance": "chat",
            "data": "data",
        }
        callback_query = CallbackQuery.model_validate(data)
        assert isinstance(callback_query.message, Message)

    def test_parse_inaccessible_message(self):
        data = {
            "id": "id",
            "from": {"id": 42, "is_bot": False, "first_name": "name"},
            "message": {
                "message_id": 123,
                "date": 0,
                "chat": {"id": 42, "type": "private"},
            },
            "chat_instance": "chat",
            "data": "data",
        }
        callback_query = CallbackQuery.model_validate(data)

        assert isinstance(callback_query.message, InaccessibleMessage)
