from typing import Awaitable
from unittest.mock import patch

import pytest
from asynctest import CoroutineMock

from aiogram.dispatcher.filters.base import BaseFilter


class MyFilter(BaseFilter):
    foo: str

    async def __call__(self, event: str):
        return


class TestBaseFilter:
    @pytest.mark.asyncio
    async def test_awaitable(self):
        my_filter = MyFilter(foo="bar")

        assert isinstance(my_filter, Awaitable)

        with patch(
            "tests.test_dispatcher.test_filters.test_base.MyFilter.__call__",
            new_callable=CoroutineMock,
        ) as mocked_call:
            call = my_filter(event="test")
            await call
            mocked_call.assert_awaited_with(event="test")
