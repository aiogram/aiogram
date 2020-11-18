from typing import Any

import pytest

from aiogram.dispatcher.handler import ErrorHandler, PollHandler
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    Poll,
    PollOption,
    ShippingAddress,
    ShippingQuery,
    User,
)


class TestErrorHandler:
    @pytest.mark.asyncio
    async def test_extensions(self):
        event = KeyError("kaboom")

        class MyHandler(ErrorHandler):
            async def handle(self) -> Any:
                assert self.event == event
                assert self.exception_name == event.__class__.__name__
                assert self.exception_message == str(event)
                return True

        assert await MyHandler(event)
