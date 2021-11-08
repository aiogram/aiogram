import datetime
import functools
from typing import Any, Awaitable, Callable, Dict, NoReturn, Optional, Union

import pytest

from aiogram.dispatcher.event.bases import REJECTED, SkipHandler
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.dispatcher.event.telegram import TelegramEventObserver
from aiogram.dispatcher.filters.base import BaseFilter
from aiogram.dispatcher.router import Router
from aiogram.exceptions import FiltersResolveError
from aiogram.types import Chat, Message, User

pytestmark = pytest.mark.asyncio


# TODO: Test middlewares in routers tree


async def my_handler(event: Any, index: int = 0) -> Any:
    return event


async def skip_my_handler(event: Any) -> NoReturn:
    raise SkipHandler()


async def pipe_handler(*args, **kwargs):
    return args, kwargs


class MyFilter1(BaseFilter):
    test: str

    async def __call__(self, *args: Any, **kwargs: Any) -> Union[bool, Dict[str, Any]]:
        return True


class MyFilter2(MyFilter1):
    pass


class MyFilter3(MyFilter1):
    pass


class OptionalFilter(BaseFilter):
    optional: Optional[str]

    async def __call__(self, *args: Any, **kwargs: Any) -> Union[bool, Dict[str, Any]]:
        return True


class DefaultFilter(BaseFilter):
    default: str = "Default"

    async def __call__(self, *args: Any, **kwargs: Any) -> Union[bool, Dict[str, Any]]:
        return True


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
        assert MyFilter in event_observer.filters

    def test_resolve_filters_chain(self):
        router1 = Router(use_builtin_filters=False)
        router2 = Router(use_builtin_filters=False)
        router3 = Router(use_builtin_filters=False)
        router1.include_router(router2)
        router2.include_router(router3)

        router1.message.bind_filter(MyFilter1)
        router1.message.bind_filter(MyFilter2)
        router2.message.bind_filter(MyFilter2)
        router3.message.bind_filter(MyFilter3)

        filters_chain1 = list(router1.message._resolve_filters_chain())
        filters_chain2 = list(router2.message._resolve_filters_chain())
        filters_chain3 = list(router3.message._resolve_filters_chain())

        assert MyFilter1 in filters_chain1
        assert MyFilter1 in filters_chain2
        assert MyFilter1 in filters_chain3
        assert MyFilter2 in filters_chain1
        assert MyFilter2 in filters_chain2
        assert MyFilter2 in filters_chain3
        assert MyFilter3 in filters_chain3

        assert MyFilter3 not in filters_chain1

    async def test_resolve_filters_data_from_parent_router(self):
        class FilterSet(BaseFilter):
            set_filter: bool

            async def __call__(self, message: Message) -> dict:
                return {"test": "hello world"}

        class FilterGet(BaseFilter):
            get_filter: bool

            async def __call__(self, message: Message, **data) -> bool:
                assert "test" in data
                return True

        router1 = Router(use_builtin_filters=False)
        router2 = Router(use_builtin_filters=False)
        router1.include_router(router2)

        router1.message.bind_filter(FilterSet)
        router2.message.bind_filter(FilterGet)

        @router2.message(set_filter=True, get_filter=True)
        def handler_test(msg: Message, test: str):
            assert test == "hello world"

        await router1.propagate_event(
            "message",
            Message(message_id=1, date=datetime.datetime.now(), chat=Chat(id=1, type="private")),
        )

    def test_resolve_filters(self):
        router = Router(use_builtin_filters=False)
        observer = router.message
        observer.bind_filter(MyFilter1)

        resolved = observer.resolve_filters((), {"test": "PASS"})
        assert isinstance(resolved, list)
        assert any(isinstance(item, MyFilter1) for item in resolved)

        # Unknown filter
        with pytest.raises(FiltersResolveError, match="Unknown keyword filters: {'@bad'}"):
            assert observer.resolve_filters((), {"@bad": "very"})

        # Unknown filter
        with pytest.raises(FiltersResolveError, match="Unknown keyword filters: {'@bad'}"):
            assert observer.resolve_filters((), {"test": "ok", "@bad": "very"})

        # Bad argument type
        with pytest.raises(FiltersResolveError, match="Unknown keyword filters: {'test'}"):
            assert observer.resolve_filters((), {"test": ...})

        # Disallow same filter using
        with pytest.raises(FiltersResolveError, match="Unknown keyword filters: {'test'}"):
            observer.resolve_filters((MyFilter1(test="test"),), {"test": ...})

    def test_dont_autoresolve_optional_filters_for_router(self):
        router = Router(use_builtin_filters=False)
        observer = router.message
        observer.bind_filter(MyFilter1)
        observer.bind_filter(OptionalFilter)
        observer.bind_filter(DefaultFilter)

        observer.filter(test="test")
        assert len(observer._handler.filters) == 1

    def test_register_autoresolve_optional_filters(self):
        router = Router(use_builtin_filters=False)
        observer = router.message
        observer.bind_filter(MyFilter1)
        observer.bind_filter(OptionalFilter)
        observer.bind_filter(DefaultFilter)

        assert observer.register(my_handler) == my_handler
        assert isinstance(observer.handlers[0], HandlerObject)
        assert isinstance(observer.handlers[0].filters[0].callback, OptionalFilter)
        assert len(observer.handlers[0].filters) == 2
        assert isinstance(observer.handlers[0].filters[0].callback, OptionalFilter)
        assert isinstance(observer.handlers[0].filters[1].callback, DefaultFilter)

        observer.register(my_handler, test="ok")
        assert isinstance(observer.handlers[1], HandlerObject)
        assert len(observer.handlers[1].filters) == 3
        assert isinstance(observer.handlers[1].filters[0].callback, MyFilter1)
        assert isinstance(observer.handlers[1].filters[1].callback, OptionalFilter)
        assert isinstance(observer.handlers[1].filters[2].callback, DefaultFilter)

        observer.register(my_handler, test="ok", optional="ok")
        assert isinstance(observer.handlers[2], HandlerObject)
        assert len(observer.handlers[2].filters) == 3
        assert isinstance(observer.handlers[2].filters[0].callback, MyFilter1)
        assert isinstance(observer.handlers[2].filters[1].callback, OptionalFilter)
        assert isinstance(observer.handlers[2].filters[2].callback, DefaultFilter)

    def test_register(self):
        router = Router(use_builtin_filters=False)
        observer = router.message
        observer.bind_filter(MyFilter1)

        assert observer.register(my_handler) == my_handler
        assert isinstance(observer.handlers[0], HandlerObject)
        assert not observer.handlers[0].filters

        f = MyFilter1(test="ok")
        observer.register(my_handler, f)
        assert isinstance(observer.handlers[1], HandlerObject)
        assert len(observer.handlers[1].filters) == 1
        assert observer.handlers[1].filters[0].callback == f

        observer.register(my_handler, test="PASS")
        assert isinstance(observer.handlers[2], HandlerObject)
        assert any(isinstance(item.callback, MyFilter1) for item in observer.handlers[2].filters)

        f2 = MyFilter2(test="ok")
        observer.register(my_handler, f2, test="PASS")
        assert isinstance(observer.handlers[3], HandlerObject)
        callbacks = [filter_.callback for filter_ in observer.handlers[3].filters]
        assert f2 in callbacks
        assert MyFilter1(test="PASS") in callbacks

    def test_register_decorator(self):
        router = Router(use_builtin_filters=False)
        observer = router.message

        @observer()
        async def my_handler(event: Any):
            pass

        assert len(observer.handlers) == 1
        assert observer.handlers[0].callback == my_handler

    async def test_trigger(self):
        router = Router(use_builtin_filters=False)
        observer = router.message
        observer.bind_filter(MyFilter1)
        observer.register(my_handler, test="ok")

        message = Message(
            message_id=42,
            date=datetime.datetime.now(),
            text="test",
            chat=Chat(id=42, type="private"),
            from_user=User(id=42, is_bot=False, first_name="Test"),
        )

        results = await observer.trigger(message)
        assert results is message

    @pytest.mark.parametrize(
        "count,handler,filters",
        (
            [5, my_handler, []],
            [3, my_handler, [lambda event: True]],
            [2, my_handler, [lambda event: True, lambda event: False, lambda event: {"ok": True}]],
        ),
    )
    def test_register_filters_via_decorator(self, count, handler, filters):
        router = Router(use_builtin_filters=False)
        observer = router.message

        for index in range(count):
            wrapped_handler = functools.partial(handler, index=index)
            observer(*filters)(wrapped_handler)
            registered_handler = observer.handlers[index]

            assert len(observer.handlers) == index + 1
            assert isinstance(registered_handler, HandlerObject)
            assert registered_handler.callback == wrapped_handler
            assert len(registered_handler.filters) == len(filters)

    async def test_trigger_right_context_in_handlers(self):
        router = Router(use_builtin_filters=False)
        observer = router.message

        async def mix_unnecessary_data(event):
            return {"a": 1}

        async def mix_data(event):
            return {"b": 2}

        async def handler(event, **kwargs):
            return False

        observer.register(
            pipe_handler, mix_unnecessary_data, handler
        )  # {"a": 1} should not be in result
        observer.register(pipe_handler, mix_data)

        results = await observer.trigger(42)
        assert len(results) == 2
        assert results[1].pop("handler")
        assert results == ((42,), {"b": 2})

    @pytest.mark.parametrize("middleware_type", ("middleware", "outer_middleware"))
    def test_register_middleware(self, middleware_type):
        event_observer = TelegramEventObserver(Router(), "test")

        middlewares = getattr(event_observer, f"{middleware_type}s")
        decorator = getattr(event_observer, middleware_type)

        @decorator
        async def my_middleware1(handler, event, data):
            pass

        assert my_middleware1 is not None
        assert my_middleware1.__name__ == "my_middleware1"
        assert my_middleware1 in middlewares

        @decorator()
        async def my_middleware2(handler, event, data):
            pass

        assert my_middleware2 is not None
        assert my_middleware2.__name__ == "my_middleware2"
        assert my_middleware2 in middlewares

        async def my_middleware3(handler, event, data):
            pass

        decorator(my_middleware3)

        assert my_middleware3 is not None
        assert my_middleware3.__name__ == "my_middleware3"
        assert my_middleware3 in middlewares

        assert middlewares == [my_middleware1, my_middleware2, my_middleware3]

    def test_register_global_filters(self):
        router = Router(use_builtin_filters=False)
        assert isinstance(router.message._handler.filters, list)
        assert not router.message._handler.filters

        my_filter = MyFilter1(test="pass")
        router.message.filter(my_filter)

        assert len(router.message._handler.filters) == 1
        assert router.message._handler.filters[0].callback is my_filter

        router.message._handler.filters = None
        router.message.filter(my_filter)
        assert len(router.message._handler.filters) == 1
        assert router.message._handler.filters[0].callback is my_filter

    async def test_global_filter(self):
        r1 = Router()
        r2 = Router()

        async def handler(evt):
            return evt

        r1.message.filter(lambda evt: False)
        r1.message.register(handler)
        r2.message.register(handler)

        assert await r1.message.trigger(None) is REJECTED
        assert await r2.message.trigger(None) is None

    async def test_global_filter_in_nested_router(self):
        r1 = Router()
        r2 = Router()

        async def handler(evt):
            return evt

        r1.include_router(r2)
        r1.message.filter(lambda evt: False)
        r2.message.register(handler)

        assert await r1.message.trigger(None) is REJECTED
