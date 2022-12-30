from typing import Awaitable
from unittest.mock import AsyncMock, patch

from aiogram.filters import Filter


class MyFilter(Filter):
    async def __call__(self, event: str):
        return


class TestBaseFilter:
    async def test_awaitable(self):
        my_filter = MyFilter()

        assert isinstance(my_filter, Awaitable)

        with patch(
            "tests.test_filters.test_base.MyFilter.__call__",
            new_callable=AsyncMock,
        ) as mocked_call:
            call = my_filter(event="test")
            await call
            mocked_call.assert_awaited_with(event="test")
