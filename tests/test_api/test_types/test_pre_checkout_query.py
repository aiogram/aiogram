from aiogram.methods import AnswerPreCheckoutQuery
from aiogram.types import PreCheckoutQuery, User


class TestPreCheckoutQuery:
    def test_answer_alias(self):
        pre_checkout_query = PreCheckoutQuery(
            id="id",
            from_user=User(id=42, is_bot=False, first_name="name"),
            currency="currency",
            total_amount=123,
            invoice_payload="payload",
        )

        kwargs = {"ok": True, "error_message": "foo"}

        api_method = pre_checkout_query.answer(**kwargs)

        assert isinstance(api_method, AnswerPreCheckoutQuery)
        assert api_method.pre_checkout_query_id == pre_checkout_query.id

        for key, value in kwargs.items():
            assert getattr(api_method, key) == value
