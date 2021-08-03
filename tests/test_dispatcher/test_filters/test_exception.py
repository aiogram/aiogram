import re

import pytest

from aiogram.dispatcher.filters import ExceptionMessageFilter, ExceptionTypeFilter

pytestmark = pytest.mark.asyncio


class TestExceptionMessageFilter:
    @pytest.mark.parametrize("value", ["value", re.compile("value")])
    def test_converter(self, value):
        obj = ExceptionMessageFilter(pattern=value)
        assert isinstance(obj.pattern, re.Pattern)

    async def test_match(self):
        obj = ExceptionMessageFilter(pattern="KABOOM")

        result = await obj(Exception())
        assert not result

        result = await obj(Exception("KABOOM"))
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

        result = await obj(exception)

        assert result == value
