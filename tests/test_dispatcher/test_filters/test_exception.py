import re

import pytest

from aiogram import Dispatcher
from aiogram.dispatcher.filters import ExceptionMessageFilter, ExceptionTypeFilter
from aiogram.types import Update

pytestmark = pytest.mark.asyncio


class TestExceptionMessageFilter:
    @pytest.mark.parametrize("value", ["value", re.compile("value")])
    def test_converter(self, value):
        obj = ExceptionMessageFilter(pattern=value)
        assert isinstance(obj.pattern, re.Pattern)

    async def test_match(self):
        obj = ExceptionMessageFilter(pattern="KABOOM")

        result = await obj(Update(update_id=0), exception=Exception())
        assert not result

        result = await obj(Update(update_id=0), exception=Exception("KABOOM"))
        assert isinstance(result, dict)
        assert "match_exception" in result


class MyException(Exception):
    pass


class MyAnotherException(MyException):
    pass


class TestExceptionTypeFilter:
    @pytest.mark.parametrize(
        "exception,value",
        [
            [Exception(), False],
            [ValueError(), False],
            [TypeError(), False],
            [MyException(), True],
            [MyAnotherException(), True],
        ],
    )
    async def test_check(self, exception: Exception, value: bool):
        obj = ExceptionTypeFilter(exception=MyException)

        result = await obj(Update(update_id=0), exception=exception)

        assert result == value


class TestDispatchException:
    async def test_handle_exception(self, bot):
        dp = Dispatcher()

        @dp.update()
        async def update_handler(update):
            raise ValueError("KABOOM")

        @dp.errors(ExceptionMessageFilter(pattern="KABOOM"))
        async def handler0(update, exception):
            return "Handled"

        assert await dp.feed_update(bot, Update(update_id=0)) == "Handled"
