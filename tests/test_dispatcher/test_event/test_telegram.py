import datetime
import functools
from typing import Any, Dict, NoReturn, Optional, Union

import pytest
from pydantic import BaseModel

from aiogram.dispatcher.event.bases import UNHANDLED, SkipHandler
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.dispatcher.event.telegram import TelegramEventObserver
from aiogram.dispatcher.router import Router
from aiogram.exceptions import UnsupportedKeywordArgument
from aiogram.filters import Filter
from aiogram.types import Chat, Message, User

# TODO: Test middlewares in routers tree


async def my_handler(event: Any, index: int = 0) -> Any:
    return event


async def skip_my_handler(event: Any) -> NoReturn:
    raise SkipHandler()


async def pipe_handler(*args, **kwargs):
    return args, kwargs


class MyFilter1(Filter, BaseModel):
    test: str

    async def __call__(self, *args: Any, **kwargs: Any) -> Union[bool, Dict[str, Any]]:
        return True


class MyFilter2(MyFilter1):
    pass


class MyFilter3(MyFilter1):
    pass


class OptionalFilter(Filter, BaseModel):
    optional: Optional[str]

    async def __call__(self, *args: Any, **kwargs: Any) -> Union[bool, Dict[str, Any]]:
        return True


class DefaultFilter(Filter, BaseModel):
    default: str = "Default"

    async def __call__(self, *args: Any, **kwargs: Any) -> Union[bool, Dict[str, Any]]:
        return True


class TestTelegramEventObserver:
    def test_register(self):
        router = Router()
        observer = router.message

        assert observer.register(my_handler) == my_handler
        assert isinstance(observer.handlers[0], HandlerObject)
        assert not observer.handlers[0].filters

        f = MyFilter1(test="ok")
        observer.register(my_handler, f)
        assert isinstance(observer.handlers[1], HandlerObject)
        assert len(observer.handlers[1].filters) == 1
        assert observer.handlers[1].filters[0].callback == f

        observer.register(my_handler, MyFilter1(test="PASS"))
        assert isinstance(observer.handlers[2], HandlerObject)
        assert any(isinstance(item.callback, MyFilter1) for item in observer.handlers[2].filters)

        f2 = MyFilter2(test="ok")
        observer.register(my_handler, f2, MyFilter1(test="PASS"))
        assert isinstance(observer.handlers[3], HandlerObject)
        callbacks = [filter_.callback for filter_ in observer.handlers[3].filters]
        assert f2 in callbacks
        assert MyFilter1(test="PASS") in callbacks

    def test_keyword_filters_is_not_supported(self):
        router = Router()
        with pytest.raises(UnsupportedKeywordArgument):
            router.message.register(lambda e: True, commands=["test"])

    def test_register_decorator(self):
        router = Router()
        observer = router.message

        @observer()
        async def my_handler(event: Any):
            pass

        assert len(observer.handlers) == 1
        assert observer.handlers[0].callback == my_handler

    async def test_trigger(self):
        router = Router()
        observer = router.message
        observer.register(my_handler, MyFilter1(test="ok"))

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
        router = Router()
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
        router = Router()
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

        middlewares = getattr(event_observer, middleware_type)

        @middlewares
        async def my_middleware1(handler, event, data):
            pass

        assert my_middleware1 is not None
        assert my_middleware1.__name__ == "my_middleware1"
        assert my_middleware1 in middlewares

        @middlewares()
        async def my_middleware2(handler, event, data):
            pass

        assert my_middleware2 is not None
        assert my_middleware2.__name__ == "my_middleware2"
        assert my_middleware2 in middlewares

        async def my_middleware3(handler, event, data):
            pass

        middlewares(my_middleware3)

        assert my_middleware3 is not None
        assert my_middleware3.__name__ == "my_middleware3"
        assert my_middleware3 in middlewares

        assert list(middlewares) == [my_middleware1, my_middleware2, my_middleware3]

    def test_register_global_filters(self):
        router = Router()
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

        assert await r1.propagate_event("message", None) is UNHANDLED
        assert await r2.propagate_event("message", None) is None

    async def test_global_filter_in_nested_router(self):
        r1 = Router()
        r2 = Router()

        async def handler(evt):
            return evt

        r1.include_router(r2)
        r1.message.filter(lambda evt: False)
        r2.message.register(handler)

        assert await r1.message.trigger(None) is UNHANDLED
