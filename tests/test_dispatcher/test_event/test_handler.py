import asyncio
import functools
import inspect
from collections.abc import Callable
from typing import Any

import pytest
from magic_filter import F as A

from aiogram import F
from aiogram.dispatcher.event.handler import CallableObject, FilterObject, HandlerObject
from aiogram.filters import Filter, invert_f
from aiogram.types import Update


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


class AsyncCallable:
    async def __call__(self, foo, bar, baz):
        return locals()


class TestCallableObject:
    @pytest.mark.parametrize("callback", [callback2, TestFilter(), AsyncCallable()])
    def test_init_awaitable(self, callback):
        obj = CallableObject(callback)
        assert obj.awaitable
        assert obj.callback == callback

    @pytest.mark.asyncio
    async def test_call_async_callable_object(self):
        obj = CallableObject(AsyncCallable())
        assert await obj.call(foo=1, bar=2, baz=3) == {
            "self": obj.callback,
            "foo": 1,
            "bar": 2,
            "baz": 3,
        }

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


async def _reject(value) -> bool:
    return False


def _async_wraps(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


class FlagFilter(Filter):
    async def __call__(self, value, flag: bool) -> bool:  # pragma: no cover
        return flag


class TestCoroutineFilters:
    @pytest.mark.parametrize(
        "callback,result",
        [
            [_reject, False],
            [functools.partial(_reject), False],
            [lambda value: value == 42, True],
            [lambda value: {"value": value}, {"value": 42}],
        ],
    )
    async def test_valid_filter(self, callback, result):
        assert await FilterObject(callback).call(42) == result

    @pytest.mark.parametrize(
        "callback",
        [
            lambda value: _reject(value),
            _async_wraps(lambda value: False),
            functools.partial(FlagFilter(), flag=False),
            F.func(_reject),
        ],
    )
    async def test_filter_returning_coroutine_fails_closed(self, callback):
        handler = HandlerObject(simple_handler, [FilterObject(callback)])
        with pytest.raises(TypeError, match="returned an awaitable"):
            await handler.check(42)

    async def test_coroutine_is_closed_and_not_awaited(self):
        coroutines = []

        def callback(value):
            coroutines.append(_reject(value))
            return coroutines[-1]

        with pytest.raises(TypeError, match="returned an awaitable"):
            await FilterObject(callback).call(42)
        assert inspect.getcoroutinestate(coroutines[0]) == inspect.CORO_CLOSED

    async def test_filter_returning_future_fails_closed(self):
        future = asyncio.get_running_loop().create_future()
        with pytest.raises(TypeError, match="returned an awaitable"):
            await FilterObject(lambda value: future).call(42)
        assert not future.done()

    async def test_filter_returning_custom_awaitable_fails_closed(self):
        class Awaitable:
            def __await__(self):  # pragma: no cover
                yield

        with pytest.raises(TypeError, match="returned an awaitable"):
            await FilterObject(lambda value: Awaitable()).call(42)

    async def test_inverted_filter_returning_coroutine_fails_closed(self):
        with pytest.raises(TypeError, match="returned an awaitable"):
            await FilterObject(invert_f(lambda value: _reject(value))).call(42)


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

    def test_plain_magic_filter_is_accepted_silently(self):
        # No Recommendation warning any more; filterwarnings=error fails on any warning
        magic = A.test.is_(True)
        assert FilterObject(callback=magic).magic is magic

    async def test_check_without_filters(self):
        handler = HandlerObject(simple_handler)
        assert await handler.check(42, foo=True) == (True, {"foo": True})
