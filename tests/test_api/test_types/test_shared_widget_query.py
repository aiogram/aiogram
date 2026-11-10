from aiogram.methods import AnswerWidgetQuery
from aiogram.types import SharedWidgetQuery, User, WidgetQueryTypeData


class TestSharedWidgetQuery:
    def test_answer_alias(self):
        shared_widget_query = SharedWidgetQuery(
            id="id",
            from_user=User(id=42, is_bot=False, first_name="name"),
            type=WidgetQueryTypeData(),
            data="data",
            widget_id="widget",
        )

        api_method = shared_widget_query.answer(data="answer")

        assert isinstance(api_method, AnswerWidgetQuery)
        assert api_method.widget_query_id == shared_widget_query.id
        assert api_method.data == "answer"
