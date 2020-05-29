import datetime
import functools
from typing import Any, Awaitable, Callable, Dict, NoReturn, Union

import pytest

from aiogram.api.types import Chat, Message, User
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.dispatcher.event.telegram import TelegramEventObserver
from aiogram.dispatcher.filters.base import BaseFilter
from aiogram.dispatcher.router import Router

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

    def test_resolve_filters(self):
        router = Router(use_builtin_filters=False)
        observer = router.message
        observer.bind_filter(MyFilter1)

        resolved = observer.resolve_filters({"test": "PASS"})
        assert isinstance(resolved, list)
        assert any(isinstance(item, MyFilter1) for item in resolved)

        # Unknown filter
        with pytest.raises(ValueError, match="Unknown keyword filters: {'@bad'}"):
            assert observer.resolve_filters({"@bad": "very"})

        # Unknown filter
        with pytest.raises(ValueError, match="Unknown keyword filters: {'@bad'}"):
            assert observer.resolve_filters({"test": "ok", "@bad": "very"})

        # Bad argument type
        with pytest.raises(ValueError, match="Unknown keyword filters: {'test'}"):
            assert observer.resolve_filters({"test": ...})

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

        observer.register(my_handler, f, test="PASS")
        assert isinstance(observer.handlers[3], HandlerObject)
        callbacks = [filter_.callback for filter_ in observer.handlers[3].filters]
        assert f in callbacks
        assert MyFilter1(test="PASS") in callbacks

    def test_register_decorator(self):
        router = Router(use_builtin_filters=False)
        observer = router.message

        @observer()
        async def my_handler(event: Any):
            pass

        assert len(observer.handlers) == 1
        assert observer.handlers[0].callback == my_handler

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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
