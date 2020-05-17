from aiogram.api.methods import AnswerInlineQuery
from aiogram.api.types import InlineQuery, User


class TestInlineQuery:
    def test_answer_alias(self):
        inline_query = InlineQuery(
            id="id",
            from_user=User(id=42, is_bot=False, first_name="name"),
            query="query",
            offset="",
        )

        api_method = inline_query.answer([])

        assert isinstance(api_method, AnswerInlineQuery)
        assert api_method.inline_query_id == inline_query.id
