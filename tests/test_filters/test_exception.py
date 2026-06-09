import re

import pytest

from aiogram import Dispatcher
from aiogram.filters import ExceptionMessageFilter, ExceptionTypeFilter
from aiogram.types import Update
from aiogram.types.error_event import ErrorEvent


class TestExceptionMessageFilter:
    @pytest.mark.parametrize("value", ["value", re.compile("value")])
    def test_converter(self, value):
        obj = ExceptionMessageFilter(pattern=value)
        assert isinstance(obj.pattern, re.Pattern)

    async def test_match(self):
        obj = ExceptionMessageFilter(pattern="KABOOM")

        result = await obj(ErrorEvent(update=Update(update_id=0), exception=Exception()))
        assert not result

        result = await obj(ErrorEvent(update=Update(update_id=0), exception=Exception("KABOOM")))
        assert isinstance(result, dict)
        assert "match_exception" in result

    async def test_str(self):
        obj = ExceptionMessageFilter(pattern="KABOOM")
        assert str(obj) == "ExceptionMessageFilter(pattern=re.compile('KABOOM'))"


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
        obj = ExceptionTypeFilter(MyException)

        result = await obj(ErrorEvent(update=Update(update_id=0), exception=exception))

        assert result == value

    def test_without_arguments(self):
        with pytest.raises(ValueError):
            ExceptionTypeFilter()


class TestDispatchException:
    async def test_handle_exception(self, bot):
        dp = Dispatcher()

        @dp.update()
        async def update_handler(update):
            raise ValueError("KABOOM")

        @dp.errors(ExceptionMessageFilter(pattern="KABOOM"))
        async def handler0(event):
            return "Handled"

        with pytest.warns(RuntimeWarning, match="Detected unknown update type"):
            assert await dp.feed_update(bot, Update(update_id=0)) == "Handled"
