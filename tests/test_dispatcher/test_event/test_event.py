import functools
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from aiogram.dispatcher.event.event import EventObserver
from aiogram.dispatcher.event.handler import HandlerObject


async def my_handler(value: str, index: int = 0) -> Any:
    return value


class TestEventObserver:
    @pytest.mark.parametrize("via_decorator", [True, False])
    @pytest.mark.parametrize("count,handler", ([5, my_handler], [3, my_handler], [2, my_handler]))
    def test_register_filters(self, via_decorator, count, handler):
        observer = EventObserver()

        for index in range(count):
            wrapped_handler = functools.partial(handler, index=index)
            if via_decorator:
                register_result = observer()(wrapped_handler)
                assert register_result == wrapped_handler
            else:
                register_result = observer.register(wrapped_handler)
                assert register_result is None

            registered_handler = observer.handlers[index]

            assert len(observer.handlers) == index + 1
            assert isinstance(registered_handler, HandlerObject)
            assert registered_handler.callback == wrapped_handler
            assert not registered_handler.filters

    async def test_trigger(self):
        observer = EventObserver()

        observer.register(my_handler)
        observer.register(lambda e: True)
        observer.register(my_handler)

        assert observer.handlers[0].awaitable
        assert not observer.handlers[1].awaitable
        assert observer.handlers[2].awaitable

        with patch(
            "aiogram.dispatcher.event.handler.CallableObject.call",
            new_callable=AsyncMock,
        ) as mocked_my_handler:
            results = await observer.trigger("test")
            assert results is None
            mocked_my_handler.assert_awaited_with("test")
            assert mocked_my_handler.call_count == 3
