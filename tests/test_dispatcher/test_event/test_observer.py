import functools
from typing import Any, Awaitable, Callable, Dict, NoReturn, Union

import pytest

from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.dispatcher.event.observer import EventObserver, SkipHandler, TelegramEventObserver
from aiogram.dispatcher.filters.base import BaseFilter
from aiogram.dispatcher.router import Router


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


class TestTelegramEventObserver:
    def test_bind_filter(self):
        event_observer = TelegramEventObserver(Router(), "test")
        with pytest.raises(TypeError):
            event_observer.bind_filter(object)  # type: ignore

        class MyFilter(BaseFilter):
            async def __call__(
                self, *args: Any, **kwargs: Any
            ) -> Callable[[Any], Awaitable[Union[bool, Dict[str, Any]]]]:
                pass

        event_observer.bind_filter(MyFilter)
        assert event_observer.filters
        assert event_observer.filters[0] == MyFilter

    def test_resolve_filters_chain(self):
        router1 = Router()
        router2 = Router()
        router3 = Router()
        router1.include_router(router2)
        router2.include_router(router3)

        class MyFilter1(BaseFilter):
            test: str

            async def __call__(self, *args: Any, **kwargs: Any) -> Union[bool, Dict[str, Any]]:
                return True

        class MyFilter2(MyFilter1):
            pass

        class MyFilter3(MyFilter1):
            pass

        router1.message_handler.bind_filter(MyFilter1)
        router1.message_handler.bind_filter(MyFilter2)
        router2.message_handler.bind_filter(MyFilter2)
        router3.message_handler.bind_filter(MyFilter3)

        filters_chain1 = list(router1.message_handler._resolve_filters_chain())
        filters_chain2 = list(router2.message_handler._resolve_filters_chain())
        filters_chain3 = list(router3.message_handler._resolve_filters_chain())

        assert filters_chain1 == [MyFilter1, MyFilter2]
        assert filters_chain2 == [MyFilter2, MyFilter1]
        assert filters_chain3 == [MyFilter3, MyFilter2, MyFilter1]

    def test_resolve_filters(self):
        pass

    def test_register(self):
        pass

    def test_register_decorator(self):
        pass

    @pytest.mark.asyncio
    async def test_trigger(self):
        pass
