from aiogram.methods import AnswerShippingQuery
from aiogram.types import (
    LabeledPrice,
    ShippingAddress,
    ShippingOption,
    ShippingQuery,
    User,
)


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

        shipping_options = [
            ShippingOption(id="id", title="foo", prices=[LabeledPrice(label="foo", amount=123)])
        ]

        kwargs = dict(ok=True, shipping_options=shipping_options, error_message="foo")

        api_method = shipping_query.answer(**kwargs)

        assert isinstance(api_method, AnswerShippingQuery)
        assert api_method.shipping_query_id == shipping_query.id

        for key, value in kwargs.items():
            assert getattr(api_method, key) == value
