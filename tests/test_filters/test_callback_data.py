import sys
from decimal import Decimal
from enum import Enum, auto
from fractions import Fraction
from typing import Optional, Union
from uuid import UUID

import pytest
from magic_filter import MagicFilter
from pydantic import ValidationError

from aiogram import F
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, User


class MyIntEnum(Enum):
    FOO = auto()


class MyStringEnum(str, Enum):
    FOO = "FOO"


class MyCallback(CallbackData, prefix="test"):
    foo: str
    bar: int


class TestCallbackData:
    def test_init_subclass_prefix_required(self):
        assert MyCallback.__prefix__ == "test"

        with pytest.raises(ValueError, match="prefix required.+"):

            class MyInvalidCallback(CallbackData):
                pass

    def test_init_subclass_sep_validation(self):
        assert MyCallback.__separator__ == ":"

        class MyCallback2(CallbackData, prefix="test2", sep="@"):
            pass

        assert MyCallback2.__separator__ == "@"

        with pytest.raises(ValueError, match="Separator symbol '@' .+ 'sp@m'"):

            class MyInvalidCallback(CallbackData, prefix="sp@m", sep="@"):
                pass

    @pytest.mark.parametrize(
        "value,expected",
        [
            [None, ""],
            [True, "1"],
            [False, "0"],
            [42, "42"],
            ["test", "test"],
            [9.99, "9.99"],
            [Decimal("9.99"), "9.99"],
            [Fraction("3/2"), "3/2"],
            [UUID("123e4567-e89b-12d3-a456-426655440000"), "123e4567e89b12d3a456426655440000"],
            [MyIntEnum.FOO, "1"],
            [MyStringEnum.FOO, "FOO"],
        ],
    )
    def test_encode_value_positive(self, value, expected):
        callback = MyCallback(foo="test", bar=42)
        assert callback._encode_value("test", value) == expected

    @pytest.mark.parametrize(
        "value",
        [
            ...,
            object,
            object(),
            User(id=42, is_bot=False, first_name="test"),
        ],
    )
    def test_encode_value_negative(self, value):
        callback = MyCallback(foo="test", bar=42)
        with pytest.raises(ValueError):
            callback._encode_value("test", value)

    def test_pack(self):
        with pytest.raises(ValueError, match="Separator symbol .+"):
            assert MyCallback(foo="te:st", bar=42).pack()

        with pytest.raises(ValueError, match=".+is too long.+"):
            assert MyCallback(foo="test" * 32, bar=42).pack()

        assert MyCallback(foo="test", bar=42).pack() == "test:test:42"

    def test_pack_optional(self):
        class MyCallback1(CallbackData, prefix="test1"):
            foo: str
            bar: Optional[int] = None

        assert MyCallback1(foo="spam").pack() == "test1:spam:"
        assert MyCallback1(foo="spam", bar=42).pack() == "test1:spam:42"

        class MyCallback2(CallbackData, prefix="test2"):
            foo: Optional[str] = None
            bar: int

        assert MyCallback2(bar=42).pack() == "test2::42"
        assert MyCallback2(foo="spam", bar=42).pack() == "test2:spam:42"

        class MyCallback3(CallbackData, prefix="test3"):
            foo: Optional[str] = "experiment"
            bar: int

        assert MyCallback3(bar=42).pack() == "test3:experiment:42"
        assert MyCallback3(foo="spam", bar=42).pack() == "test3:spam:42"

    def test_unpack(self):
        with pytest.raises(TypeError, match=".+ takes 2 arguments but 3 were given"):
            MyCallback.unpack("test:test:test:test")

        with pytest.raises(ValueError, match="Bad prefix .+"):
            MyCallback.unpack("spam:test:test")

        assert MyCallback.unpack("test:test:42") == MyCallback(foo="test", bar=42)

    def test_unpack_optional(self):
        with pytest.raises(ValidationError):
            assert MyCallback.unpack("test:test:")

        class MyCallback1(CallbackData, prefix="test1"):
            foo: str
            bar: Optional[int] = None

        assert MyCallback1.unpack("test1:spam:") == MyCallback1(foo="spam")
        assert MyCallback1.unpack("test1:spam:42") == MyCallback1(foo="spam", bar=42)

        class MyCallback2(CallbackData, prefix="test2"):
            foo: Optional[str] = None
            bar: int

        assert MyCallback2.unpack("test2::42") == MyCallback2(bar=42)
        assert MyCallback2.unpack("test2:spam:42") == MyCallback2(foo="spam", bar=42)

        class MyCallback3(CallbackData, prefix="test3"):
            foo: Optional[str] = "experiment"
            bar: int

        assert MyCallback3.unpack("test3:experiment:42") == MyCallback3(bar=42)
        assert MyCallback3.unpack("test3:spam:42") == MyCallback3(foo="spam", bar=42)

    @pytest.mark.parametrize(
        "hint",
        [
            Union[int, None],
            Optional[int],
        ],
    )
    def test_unpack_optional_wo_default(self, hint):
        """Test CallbackData without default optional."""

        class TgData(CallbackData, prefix="tg"):
            chat_id: int
            thread_id: hint

        assert TgData.unpack("tg:123:") == TgData(chat_id=123, thread_id=None)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="UnionType is added in Python 3.10")
    def test_unpack_optional_wo_default_union_type(self):
        """Test CallbackData without default optional."""

        class TgData(CallbackData, prefix="tg"):
            chat_id: int
            thread_id: int | None

        assert TgData.unpack("tg:123:") == TgData(chat_id=123, thread_id=None)

    def test_build_filter(self):
        filter_object = MyCallback.filter(F.foo == "test")
        assert isinstance(filter_object.rule, MagicFilter)
        assert filter_object.callback_data is MyCallback


class TestCallbackDataFilter:
    @pytest.mark.parametrize(
        "query,rule,result",
        [
            ["test", F.foo == "test", False],
            ["test:spam:42", F.foo == "test", False],
            ["test:test:42", F.foo == "test", {"callback_data": MyCallback(foo="test", bar=42)}],
            ["test:test:42", None, {"callback_data": MyCallback(foo="test", bar=42)}],
            ["test:test:777", None, {"callback_data": MyCallback(foo="test", bar=777)}],
            ["spam:test:777", None, False],
            ["test:test:", F.foo == "test", False],
            ["test:test:", None, False],
        ],
    )
    async def test_call(self, query, rule, result):
        callback_query = CallbackQuery(
            id="1",
            from_user=User(id=42, is_bot=False, first_name="test"),
            data=query,
            chat_instance="test",
        )

        filter_object = MyCallback.filter(rule)
        assert await filter_object(callback_query) == result

    async def test_invalid_call(self):
        filter_object = MyCallback.filter(F.test)
        assert not await filter_object(User(id=42, is_bot=False, first_name="test"))

    def test_str(self):
        filter_object = MyCallback.filter(F.test)
        assert str(filter_object).startswith("CallbackQueryFilter(callback_data=")
