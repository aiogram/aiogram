from aiogram.api.methods import AnswerInlineQuery
from aiogram.api.types import InlineQuery
from tests.factories.user import UserFactory


class TestInlineQuery:
    def test_answer_alias(self):
        inline_query = InlineQuery(id="id", from_user=UserFactory(), query="query", offset="",)

        kwargs = dict(
            results=[],
            cache_time=123,
            next_offset="123",
            switch_pm_text="foo",
            switch_pm_parameter="foo",
        )

        api_method = inline_query.answer(**kwargs)

        assert isinstance(api_method, AnswerInlineQuery)
        assert api_method.inline_query_id == inline_query.id

        for key, value in kwargs.items():
            assert getattr(api_method, key) == value
