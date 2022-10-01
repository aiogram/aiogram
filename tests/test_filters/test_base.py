from typing import Awaitable

import pytest

from aiogram.filters import Filter
from aiogram.filters.base import _InvertFilter

try:
    from asynctest import CoroutineMock, patch
except ImportError:
    from unittest.mock import AsyncMock as CoroutineMock  # type: ignore
    from unittest.mock import patch

pytestmark = pytest.mark.asyncio


class MyFilter(Filter):
    async def __call__(self, event: str):
        return


class TestBaseFilter:
    async def test_awaitable(self):
        my_filter = MyFilter()

        assert isinstance(my_filter, Awaitable)

        with patch(
            "tests.test_filters.test_base.MyFilter.__call__",
            new_callable=CoroutineMock,
        ) as mocked_call:
            call = my_filter(event="test")
            await call
            mocked_call.assert_awaited_with(event="test")

    async def test_invert(self):
        my_filter = MyFilter()
        my_inverted_filter = ~my_filter

        assert str(my_inverted_filter) == f"~{str(my_filter)}"

        assert isinstance(my_inverted_filter, _InvertFilter)

        with patch(
            "tests.test_filters.test_base.MyFilter.__call__",
            new_callable=CoroutineMock,
        ) as mocked_call:
            call = my_inverted_filter(event="test")
            result = await call
            mocked_call.assert_awaited_with(event="test")
            assert not result
