from decimal import Decimal
from enum import Enum, auto
from fractions import Fraction
from uuid import UUID

import pytest
from pydantic import BaseModel

from aiogram.filters.command.data.codecs import (
    Base64Codec,
    NamedCodec,
    PositionalCodec,
    _encode_value,
)


class MyStrEnum(str, Enum):
    FOO = "foo"


class MyIntEnum(Enum):
    BAR = auto()


class MyModel(BaseModel):
    name: str
    count: int


class MyModelOpt(BaseModel):
    name: str
    count: int | None = None


class MyB64(BaseModel):
    text: str
    num: int


class TestEncodeValue:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (None, ""),
            (True, "1"),
            (False, "0"),
            (MyIntEnum.BAR, "1"),
            (MyStrEnum.FOO, "foo"),
            ("hello", "hello"),
            (42, "42"),
            (3.14, "3.14"),
            (UUID("123e4567-e89b-12d3-a456-426655440000"), "123e4567e89b12d3a456426655440000"),
            (Decimal("9.99"), "9.99"),
            (Fraction("3/2"), "3/2"),
        ],
    )
    def test_positive(self, value, expected):
        assert _encode_value("field", value) == expected

    def test_unsupported_type_raises(self):
        with pytest.raises(ValueError, match="can not be packed"):
            _encode_value("field", object())


class TestPositionalCodec:
    @pytest.mark.parametrize(
        "model,expected",
        [
            (MyModel(name="alice", count=5), "alice 5"),
            (MyModelOpt(name="alice"), "alice"),
        ],
    )
    def test_encode(self, model, expected):
        assert PositionalCodec(sep=" ").encode(model) == expected

    def test_encode_sep_in_value_raises(self):
        with pytest.raises(ValueError, match="Separator"):
            PositionalCodec(sep=" ").encode(MyModel(name="a b", count=1))

    @pytest.mark.parametrize(
        "args,model_cls,expected",
        [
            ("alice 5", MyModel, MyModel(name="alice", count=5)),
            ("alice", MyModelOpt, MyModelOpt(name="alice", count=None)),
        ],
    )
    def test_decode(self, args, model_cls, expected):
        assert PositionalCodec(sep=" ").decode(args, model_cls) == expected

    def test_decode_too_many_segments_raises(self):
        with pytest.raises(ValueError, match="segments"):
            PositionalCodec(sep=" ").decode("a b c", MyModel)


class TestNamedCodec:
    @pytest.mark.parametrize(
        "args,expected",
        [
            ("name=alice count=5", MyModel(name="alice", count=5)),
            ("count=5 name=alice", MyModel(name="alice", count=5)),
            ("name=alice", MyModelOpt(name="alice", count=None)),
        ],
    )
    def test_decode(self, args, expected):
        assert NamedCodec().decode(args, type(expected)) == expected

    def test_decode_malformed_token_raises(self):
        with pytest.raises(ValueError, match="key=value"):
            NamedCodec().decode("namealice", MyModel)

    def test_decode_value_contains_kv_sep(self):
        assert NamedCodec(kv_sep="=").decode("name=a=b count=5", MyModel) == MyModel(name="a=b", count=5)

    @pytest.mark.parametrize("model", [
        MyModel(name="bob", count=99),
        MyModelOpt(name="alice"),
    ])
    def test_roundtrip(self, model):
        codec = NamedCodec()
        assert codec.decode(codec.encode(model), type(model)) == model


class TestBase64Codec:
    @pytest.mark.parametrize(
        "model",
        [
            MyB64(text="hello", num=42),
            MyB64(text="path/value", num=0),
        ],
    )
    def test_roundtrip(self, model):
        assert Base64Codec().decode(Base64Codec().encode(model), MyB64) == model

    def test_decode_empty_uses_defaults(self):
        class WithDefault(BaseModel):
            page: int = 1

        assert Base64Codec().decode("", WithDefault) == WithDefault(page=1)
