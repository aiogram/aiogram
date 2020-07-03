from aiogram.api.methods import AnswerPreCheckoutQuery
from aiogram.api.types import PreCheckoutQuery
from tests.factories.user import UserFactory


class TestPreCheckoutQuery:
    def test_answer_alias(self):
        pre_checkout_query = PreCheckoutQuery(
            id="id",
            from_user=UserFactory(),
            currency="currency",
            total_amount=123,
            invoice_payload="payload",
        )

        kwargs = dict(ok=True, error_message="foo")

        api_method = pre_checkout_query.answer(**kwargs)

        assert isinstance(api_method, AnswerPreCheckoutQuery)
        assert api_method.pre_checkout_query_id == pre_checkout_query.id

        for key, value in kwargs.items():
            assert getattr(api_method, key) == value
