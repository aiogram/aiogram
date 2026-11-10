from aiogram.methods import AnswerWidgetQuery
from aiogram.types import User, WidgetQuery, WidgetQueryTypeData


class TestWidgetQuery:
    def test_answer_alias(self):
        widget_query = WidgetQuery(
            id="id",
            from_user=User(id=42, is_bot=False, first_name="name"),
            chat_instance="chat",
            type=WidgetQueryTypeData(),
            data="data",
        )

        api_method = widget_query.answer(data="answer")

        assert isinstance(api_method, AnswerWidgetQuery)
        assert api_method.widget_query_id == widget_query.id
        assert api_method.data == "answer"
