import functools
from typing import Any, NoReturn

import pytest

from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.dispatcher.event.observer import EventObserver, SkipHandler


async def my_handler(event: Any, index: int = 0) -> Any:
    return event


async def skip_my_handler(event: Any) -> NoReturn:
    raise SkipHandler()


async def pipe_handler(*args, **kwargs):
    return args, kwargs


class TestEventObserver:
    @pytest.mark.parametrize(
        "count,handler,filters",
        (
            pytest.param(5, my_handler, []),
            pytest.param(3, my_handler, [lambda event: True]),
            pytest.param(
                2,
                my_handler,
                [lambda event: True, lambda event: False, lambda event: {"ok": True}],
            ),
        ),
    )
    def test_register_filters(self, count, handler, filters):
        observer = EventObserver()

        for index in range(count):
            wrapped_handler = functools.partial(handler, index=index)
            observer.register(wrapped_handler, *filters)
            registered_handler = observer.handlers[index]

            assert len(observer.handlers) == index + 1
            assert isinstance(registered_handler, HandlerObject)
            assert registered_handler.callback == wrapped_handler
            assert len(registered_handler.filters) == len(filters)

    @pytest.mark.parametrize(
        "count,handler,filters",
        (
            pytest.param(5, my_handler, []),
            pytest.param(3, my_handler, [lambda event: True]),
            pytest.param(
                2,
                my_handler,
                [lambda event: True, lambda event: False, lambda event: {"ok": True}],
            ),
        ),
    )
    def test_register_filters_via_decorator(self, count, handler, filters):
        observer = EventObserver()

        for index in range(count):
            wrapped_handler = functools.partial(handler, index=index)
            observer(*filters)(wrapped_handler)
            registered_handler = observer.handlers[index]

            assert len(observer.handlers) == index + 1
            assert isinstance(registered_handler, HandlerObject)
            assert registered_handler.callback == wrapped_handler
            assert len(registered_handler.filters) == len(filters)

    @pytest.mark.asyncio
    async def test_trigger_rejected(self):
        observer = EventObserver()
        observer.register(my_handler, lambda event: False)

        results = [result async for result in observer.trigger(42)]
        assert results == []

    @pytest.mark.asyncio
    async def test_trigger_accepted_bool(self):
        observer = EventObserver()
        observer.register(my_handler, lambda event: True)

        results = [result async for result in observer.trigger(42)]
        assert results == [42]

    @pytest.mark.asyncio
    async def test_trigger_with_skip(self):
        observer = EventObserver()
        observer.register(skip_my_handler, lambda event: True)
        observer.register(my_handler, lambda event: False)
        observer.register(my_handler, lambda event: True)

        results = [result async for result in observer.trigger(42)]
        assert results == [42]

    @pytest.mark.asyncio
    async def test_trigger_right_context_in_handlers(self):
        observer = EventObserver()
        observer.register(
            pipe_handler, lambda event: {"a": 1}, lambda event: False
        )  # {"a": 1} should not be in result
        observer.register(pipe_handler, lambda event: {"b": 2})

        results = [result async for result in observer.trigger(42)]
        assert results == [((42,), {"b": 2})]
