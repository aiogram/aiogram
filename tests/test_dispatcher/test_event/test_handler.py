import functools
from typing import Any, Dict, Union

import pytest

from aiogram import F
from aiogram.dispatcher.event.handler import CallableMixin, FilterObject, HandlerObject
from aiogram.dispatcher.filters.base import BaseFilter
from aiogram.dispatcher.handler.base import BaseHandler
from aiogram.types import Update


def callback1(foo: int, bar: int, baz: int):
    return locals()


async def callback2(foo: int, bar: int, baz: int):
    return locals()


async def callback3(foo: int, **kwargs):
    return locals()


class Filter(BaseFilter):
    async def __call__(self, foo: int, bar: int, baz: int) -> Union[bool, Dict[str, Any]]:
        return locals()


class SyncCallable:
    def __call__(self, foo, bar, baz):
        return locals()


class TestCallableMixin:
    @pytest.mark.parametrize("callback", [callback2, Filter()])
    def test_init_awaitable(self, callback):
        obj = CallableMixin(callback)
        assert obj.awaitable
        assert obj.callback == callback

    @pytest.mark.parametrize("callback", [callback1, SyncCallable()])
    def test_init_not_awaitable(self, callback):
        obj = CallableMixin(callback)
        assert not obj.awaitable
        assert obj.callback == callback

    @pytest.mark.parametrize(
        "callback,args",
        [
            pytest.param(callback1, {"foo", "bar", "baz"}),
            pytest.param(callback2, {"foo", "bar", "baz"}),
            pytest.param(callback3, {"foo"}),
            pytest.param(Filter(), {"self", "foo", "bar", "baz"}),
            pytest.param(SyncCallable(), {"self", "foo", "bar", "baz"}),
        ],
    )
    def test_init_args_spec(self, callback, args):
        obj = CallableMixin(callback)
        assert set(obj.spec.args) == args

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

        obj1 = CallableMixin(callback1)
        obj2 = CallableMixin(callback2)

        assert set(obj1.spec.args) == {"foo", "bar", "baz"}
        assert obj1.callback == callback1
        assert set(obj2.spec.args) == {"foo", "bar", "baz"}
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
                callback3,
                {"foo": 42, "spam": True, "baz": "fuz", "bar": "test"},
                {"foo": 42, "spam": True, "baz": "fuz", "bar": "test"},
            ),
            pytest.param(
                Filter(), {"foo": 42, "spam": True, "baz": "fuz"}, {"foo": 42, "baz": "fuz"}
            ),
            pytest.param(
                SyncCallable(), {"foo": 42, "spam": True, "baz": "fuz"}, {"foo": 42, "baz": "fuz"}
            ),
        ],
    )
    def test_prepare_kwargs(self, callback, kwargs, result):
        obj = CallableMixin(callback)
        assert obj._prepare_kwargs(kwargs) == result

    @pytest.mark.asyncio
    async def test_sync_call(self):
        obj = CallableMixin(callback1)

        result = await obj.call(foo=42, bar="test", baz="fuz", spam=True)
        assert result == {"foo": 42, "bar": "test", "baz": "fuz"}

    @pytest.mark.asyncio
    async def test_async_call(self):
        obj = CallableMixin(callback2)

        result = await obj.call(foo=42, bar="test", baz="fuz", spam=True)
        assert result == {"foo": 42, "bar": "test", "baz": "fuz"}


class TestFilterObject:
    def test_post_init(self):
        case = F.test
        filter_obj = FilterObject(callback=case)
        print(filter_obj.callback)
        assert filter_obj.callback == case.resolve


async def simple_handler(*args, **kwargs):
    return args, kwargs


class TestHandlerObject:
    @pytest.mark.asyncio
    async def test_check_with_bool_result(self):
        handler = HandlerObject(simple_handler, [FilterObject(lambda value: True)] * 3)
        result, data = await handler.check(42, foo=True)
        assert result
        assert data == {"foo": True}

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_check_with_combined_result(self):
        handler = HandlerObject(
            simple_handler,
            [FilterObject(lambda value: True), FilterObject(lambda value: {"test": value})],
        )
        result, data = await handler.check(42, foo=True)
        assert result
        assert data == {"foo": True, "test": 42}

    @pytest.mark.asyncio
    async def test_check_rejected(self):
        handler = HandlerObject(simple_handler, [FilterObject(lambda value: False)])
        result, data = await handler.check(42, foo=True)
        assert not result

    @pytest.mark.asyncio
    async def test_check_partial_rejected(self):
        handler = HandlerObject(
            simple_handler, [FilterObject(lambda value: True), FilterObject(lambda value: False)]
        )
        result, data = await handler.check(42, foo=True)
        assert not result

    @pytest.mark.asyncio
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
