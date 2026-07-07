import functools
from collections.abc import Callable
from typing import Any

import pytest
from magic_filter import F as A

from aiogram import F
from aiogram.dispatcher.event.handler import CallableObject, FilterObject, HandlerObject
from aiogram.filters import Filter
from aiogram.handlers import BaseHandler
from aiogram.types import Update
from aiogram.utils.warnings import Recommendation


def callback1(foo: int, bar: int, baz: int):
    return locals()


async def callback2(foo: int, bar: int, baz: int):
    return locals()


async def callback3(foo: int, **kwargs):
    return locals()


async def callback4(foo: int, *, bar: int, baz: int):
    return locals()


class TestFilter(Filter):
    async def __call__(self, foo: int, bar: int, baz: int) -> bool | dict[str, Any]:
        return locals()


class SyncCallable:
    def __call__(self, foo, bar, baz):
        return locals()


class TestCallableObject:
    @pytest.mark.parametrize("callback", [callback2, TestFilter()])
    def test_init_awaitable(self, callback):
        obj = CallableObject(callback)
        assert obj.awaitable
        assert obj.callback == callback

    @pytest.mark.parametrize("callback", [callback1, SyncCallable()])
    def test_init_not_awaitable(self, callback):
        obj = CallableObject(callback)
        assert not obj.awaitable
        assert obj.callback == callback

    @pytest.mark.parametrize(
        "callback,args",
        [
            pytest.param(callback1, {"foo", "bar", "baz"}),
            pytest.param(callback2, {"foo", "bar", "baz"}),
            pytest.param(callback3, {"foo"}),
            pytest.param(TestFilter(), {"foo", "bar", "baz"}),
            pytest.param(SyncCallable(), {"foo", "bar", "baz"}),
        ],
    )
    def test_init_args_spec(self, callback: Callable, args: set[str]):
        obj = CallableObject(callback)
        assert set(obj.params) == args

    def test_init_decorated(self):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        @decorator
        def callback1(foo, bar, baz):
            pass

        @decorator
        @decorator
        def callback2(foo, bar, baz):
            pass

        obj1 = CallableObject(callback1)
        obj2 = CallableObject(callback2)

        assert set(obj1.params) == {"foo", "bar", "baz"}
        assert obj1.callback == callback1
        assert set(obj2.params) == {"foo", "bar", "baz"}
        assert obj2.callback == callback2

    @pytest.mark.parametrize(
        "callback,kwargs,result",
        [
            pytest.param(
                callback1, {"foo": 42, "spam": True, "baz": "fuz"}, {"foo": 42, "baz": "fuz"}
            ),
            pytest.param(
                callback2,
                {"foo": 42, "spam": True, "baz": "fuz", "bar": "test"},
                {"foo": 42, "baz": "fuz", "bar": "test"},
            ),
            pytest.param(
                functools.partial(callback2, bar="test"),
                {"foo": 42, "spam": True, "baz": "fuz"},
                {"foo": 42, "baz": "fuz"},
            ),
            pytest.param(
                callback3,
                {"foo": 42, "spam": True, "baz": "fuz", "bar": "test"},
                {"foo": 42, "spam": True, "baz": "fuz", "bar": "test"},
            ),
            pytest.param(
                callback4,
                {"foo": 42, "spam": True, "baz": "fuz", "bar": "test"},
                {"foo": 42, "baz": "fuz", "bar": "test"},
            ),
            pytest.param(
                TestFilter(), {"foo": 42, "spam": True, "baz": "fuz"}, {"foo": 42, "baz": "fuz"}
            ),
            pytest.param(
                SyncCallable(), {"foo": 42, "spam": True, "baz": "fuz"}, {"foo": 42, "baz": "fuz"}
            ),
        ],
    )
    def test_prepare_kwargs(
        self, callback: Callable, kwargs: dict[str, Any], result: dict[str, Any]
    ):
        obj = CallableObject(callback)
        assert obj._prepare_kwargs(kwargs) == result

    async def test_sync_call(self):
        obj = CallableObject(callback1)

        result = await obj.call(foo=42, bar="test", baz="fuz", spam=True)
        assert result == {"foo": 42, "bar": "test", "baz": "fuz"}

    async def test_async_call(self):
        obj = CallableObject(callback2)

        result = await obj.call(foo=42, bar="test", baz="fuz", spam=True)
        assert result == {"foo": 42, "bar": "test", "baz": "fuz"}


class TestFilterObject:
    def test_post_init(self):
        case = F.test
        filter_obj = FilterObject(callback=case)
        assert filter_obj.callback == case.resolve


async def simple_handler(*args, **kwargs):
    return args, kwargs


class TestHandlerObject:
    async def test_check_with_bool_result(self):
        handler = HandlerObject(simple_handler, [FilterObject(lambda value: True)] * 3)
        result, data = await handler.check(42, foo=True)
        assert result
        assert data == {"foo": True}

    async def test_check_with_dict_result(self):
        handler = HandlerObject(
            simple_handler,
            [
                FilterObject(
                    functools.partial(lambda value, index: {f"test{index}": "ok"}, index=item)
                )
                for item in range(3)
            ],
        )
        result, data = await handler.check(42, foo=True)
        assert result
        assert data == {"foo": True, "test0": "ok", "test1": "ok", "test2": "ok"}

    async def test_check_with_combined_result(self):
        handler = HandlerObject(
            simple_handler,
            [FilterObject(lambda value: True), FilterObject(lambda value: {"test": value})],
        )
        result, data = await handler.check(42, foo=True)
        assert result
        assert data == {"foo": True, "test": 42}

    async def test_check_rejected(self):
        handler = HandlerObject(simple_handler, [FilterObject(lambda value: False)])
        result, data = await handler.check(42, foo=True)
        assert not result

    async def test_check_partial_rejected(self):
        handler = HandlerObject(
            simple_handler, [FilterObject(lambda value: True), FilterObject(lambda value: False)]
        )
        result, data = await handler.check(42, foo=True)
        assert not result

    async def test_class_based_handler(self):
        class MyHandler(BaseHandler):
            event: Update

            async def handle(self) -> Any:
                return self.event.update_id

        handler = HandlerObject(MyHandler, filters=[FilterObject(lambda event: True)])

        assert handler.awaitable
        assert handler.callback == MyHandler
        assert len(handler.filters) == 1
        result = await handler.call(Update(update_id=42))
        assert result == 42

    def test_warn_another_magic(self):
        with pytest.warns(Recommendation):
            FilterObject(callback=A.test.is_(True))
