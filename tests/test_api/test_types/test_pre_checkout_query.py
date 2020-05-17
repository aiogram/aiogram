from aiogram.api.methods import AnswerPreCheckoutQuery
from aiogram.api.types import PreCheckoutQuery, User


class TestPreCheckoutQuery:
    def test_answer_alias(self):
        pre_checkout_query = PreCheckoutQuery(
            id="id",
            from_user=User(id=42, is_bot=False, first_name="name"),
            currency="currency",
            total_amount=123,
            invoice_payload="payload",
        )

        api_method = pre_checkout_query.answer(True)

        assert isinstance(api_method, AnswerPreCheckoutQuery)
        assert api_method.pre_checkout_query_id == pre_checkout_query.id
