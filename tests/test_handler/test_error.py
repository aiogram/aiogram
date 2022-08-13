from typing import Any

import pytest

from aiogram.handlers import ErrorHandler

pytestmark = pytest.mark.asyncio


class TestErrorHandler:
    async def test_extensions(self):
        event = KeyError("kaboom")

        class MyHandler(ErrorHandler):
            async def handle(self) -> Any:
                assert self.event == event
                assert self.exception_name == event.__class__.__name__
                assert self.exception_message == str(event)
                return True

        assert await MyHandler(event)
