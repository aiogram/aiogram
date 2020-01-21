from typing import Any

import pytest
from aiogram.api.types import CallbackQuery, InlineQuery, ShippingAddress, ShippingQuery, User
from aiogram.dispatcher.handler import ShippingQueryHandler


class TestShippingQueryHandler:
    @pytest.mark.asyncio
    async def test_attributes_aliases(self):
        event = ShippingQuery(
            id="query",
            from_user=User(id=42, is_bot=False, first_name="Test"),
            invoice_payload="payload",
            shipping_address=ShippingAddress(
                country_code="country_code",
                state="state",
                city="city",
                street_line1="street_line1",
                street_line2="street_line2",
                post_code="post_code",
            ),
        )

        class MyHandler(ShippingQueryHandler):
            async def handle(self) -> Any:
                assert self.event == event
                assert self.from_user == self.event.from_user
                return True

        assert await MyHandler(event)
