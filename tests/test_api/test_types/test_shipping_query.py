from aiogram.api.methods import AnswerShippingQuery
from aiogram.api.types import ShippingAddress, ShippingQuery, User


class TestInlineQuery:
    def test_answer_alias(self):
        shipping_query = ShippingQuery(
            id="id",
            from_user=User(id=42, is_bot=False, first_name="name"),
            invoice_payload="payload",
            shipping_address=ShippingAddress(
                country_code="foo",
                state="foo",
                city="foo",
                street_line1="foo",
                street_line2="foo",
                post_code="foo",
            ),
        )

        api_method = shipping_query.answer(True)

        assert isinstance(api_method, AnswerShippingQuery)
        assert api_method.shipping_query_id == shipping_query.id
