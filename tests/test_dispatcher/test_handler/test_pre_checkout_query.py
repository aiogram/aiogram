from typing import Any

import pytest
from aiogram.api.types import PreCheckoutQuery, User
from aiogram.dispatcher.handler import PreCheckoutQueryHandler


class TestPreCheckoutQueryHandler:
    @pytest.mark.asyncio
    async def test_attributes_aliases(self):
        event = PreCheckoutQuery(
            id="query",
            from_user=User(id=42, is_bot=False, first_name="Test"),
            currency="BTC",
            total_amount=7,
            invoice_payload="payload",
        )

        class MyHandler(PreCheckoutQueryHandler):
            async def handle(self) -> Any:
                assert self.event == event
                assert self.from_user == self.event.from_user
                return True

        assert await MyHandler(event)
