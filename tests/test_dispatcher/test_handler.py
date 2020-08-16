import functools

import pytest

from aiogram.dispatcher.handler import Handler, _check_spec, _get_spec


def callback1(foo: int, bar: int, baz: int):
    return locals()


async def callback2(foo: int, bar: int, baz: int):
    return locals()


async def callback3(foo: int, **kwargs):
    return locals()


class TestHandlerObj:
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

        obj1 = Handler.HandlerObj(callback1, _get_spec(callback1))
        obj2 = Handler.HandlerObj(callback2, _get_spec(callback2))

        assert set(obj1.spec.args) == {"foo", "bar", "baz"}
        assert obj1.handler == callback1
        assert set(obj2.spec.args) == {"foo", "bar", "baz"}
        assert obj2.handler == callback2

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
        ],
    )
    def test__check_spec(self, callback, kwargs, result):
        spec = _get_spec(callback)
        assert _check_spec(spec, kwargs) == result
