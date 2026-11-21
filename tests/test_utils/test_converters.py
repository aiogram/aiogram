"""Converter-core contract suite (F-08 spec-10): every kind x codec, errors, unions, converters.

Models, keys, forward references and the PEP 681 runtime are in ``test_converters_models.py``.
The kinds are exercised through ``json_codec`` (any annotation) and through a one-field model.
"""

import dataclasses
import enum
import json
import math
import pickle
from collections.abc import Mapping
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from types import MappingProxyType
from typing import (
    Annotated,
    Any,
    Literal,
    NamedTuple,
    NewType,
    NotRequired,
    Optional,
    Required,
    TypedDict,
    Union,
)
from uuid import UUID, SafeUUID

import pytest

from aiogram.utils._converters import ModelBase, json_codec, json_schema
from aiogram.utils.converters import (
    MISSING,
    ConversionError,
    Converter,
    DecimalAsNumber,
    Discriminator,
    EnumByName,
    EpochDatetime,
    ErrorDetail,
    IsoDatetime,
    IsoTime,
    Key,
    UuidHex,
    render_loc,
)

UTC = timezone.utc
PLUS_0530 = timezone(timedelta(hours=5, minutes=30))
UID = UUID("12345678-1234-5678-1234-567812345678")
WHEN = datetime(2024, 5, 6, 7, 8, 9, 123456, tzinfo=UTC)
TODAY = date(2024, 5, 6)
NOT_FLAT = object()


def jdump(value: Any) -> bytes:
    """What ``dump_json`` must write for a JSON-shaped value."""
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode()


def errors_of(call: Any, *args: Any, **kwargs: Any) -> list[tuple[Any, ...]]:
    with pytest.raises(ConversionError) as exc_info:
        call(*args, **kwargs)
    return [tuple(error) for error in exc_info.value.errors]


class Color(enum.Enum):
    RED = "r"
    GREEN = "g"


class Num(enum.IntEnum):
    ONE = 1
    TWO = 2


class Shade(enum.StrEnum):
    DARK = "dark"


class Status(enum.StrEnum):
    """A tolerant enum: unknown values load as ``UNKNOWN``."""

    ACTIVE = "active"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> "Status | None":
        return cls.UNKNOWN if isinstance(value, str) and value != "boom" else None


class Grade(enum.IntEnum):
    A = 1
    UNKNOWN = -1

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if value == 13:
            msg = "unlucky"
            raise ValueError(msg)
        if value == 14:
            return Color.RED  # not a member of Grade: a miss
        return cls.UNKNOWN if type(value) is int else None


@dataclasses.dataclass
class DC:
    a: int
    b: str = "x"


class Pair(NamedTuple):
    x: int
    label: str = "-"


class Movie(TypedDict, total=False):
    title: Required[str]
    year: int
    tags: NotRequired[list[str]]


class Address(ModelBase):
    city: str
    zip: int | None = None


class Temp:
    def __init__(self, c: float) -> None:
        self.c = c

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Temp) and other.c == self.c

    def __hash__(self) -> int:
        return hash(self.c)

    def __repr__(self) -> str:
        return f"Temp({self.c})"


class Celsius(Converter):
    """A user converter with a flat form."""

    def to_json(self, value: Any) -> Any:
        if value == Temp(-1):
            msg = "too cold"
            raise ValueError(msg)
        if value == Temp(-2):
            return object()
        if value == Temp(-3):
            return {"nested": [1, (2, {"k": None})], "bad": {1: 2}}
        if value == Temp(-4):
            return {"ok": [1, (2.5, True, None, "s")]}
        return value.c

    def from_json(self, value: Any) -> Any:
        if value == "type":
            msg = "fatal"
            raise TypeError(msg)
        if not isinstance(value, (int, float)):
            msg = "not a temperature"
            raise ValueError(msg)
        return Temp(value)

    def to_str(self, value: Any) -> str:
        if value == Temp(-5):
            return 5  # type: ignore[return-value]
        return f"{value.c}C"

    def from_str(self, value: str) -> Any:
        return Temp(float(value.removesuffix("C")))


class JsonOnly(Converter):
    def to_json(self, value: Any) -> Any:
        return value.c

    def from_json(self, value: Any) -> Any:
        return Temp(value)


UserId = NewType("UserId", int)
UserIds = NewType("UserIds", list[UserId])

# annotation, Python value, dump (JSON-shaped), flat text (NOT_FLAT: no flat form)
VALID: list[tuple[Any, Any, Any, Any]] = [
    (str, "héllo ☃", "héllo ☃", "héllo ☃"),
    (str, "", "", ""),
    (str, 'q"\\\n\t\x01é😀', 'q"\\\n\t\x01é😀', 'q"\\\n\t\x01é😀'),
    (int, 5, 5, "5"),
    (int, -7, -7, "-7"),
    (int, -(10**30), -(10**30), str(-(10**30))),
    (float, 1.5, 1.5, "1.5"),
    (float, 1e300, 1e300, "1e+300"),
    (float, -0.0, -0.0, "-0.0"),
    (float, 1e16, 1e16, "1e+16"),
    (bool, True, True, "1"),
    (bool, False, False, "0"),
    (UUID, UID, str(UID), UID.hex),
    (Annotated[UUID, UuidHex()], UID, UID.hex, UID.hex),
    (datetime, WHEN, "2024-05-06T07:08:09.123456+00:00", "20240506T070809.123456Z"),
    (datetime, WHEN.replace(tzinfo=None), "2024-05-06T07:08:09.123456", "20240506T070809.123456"),
    (
        datetime,
        WHEN.replace(tzinfo=PLUS_0530),
        "2024-05-06T07:08:09.123456+05:30",
        "20240506T070809.123456+0530",
    ),
    (datetime, WHEN.replace(microsecond=0), "2024-05-06T07:08:09+00:00", "20240506T070809Z"),
    (
        Annotated[datetime, IsoDatetime(timespec="seconds", sep=" ")],
        WHEN.replace(microsecond=0),
        "2024-05-06 07:08:09+00:00",
        "20240506T070809Z",
    ),
    (
        Annotated[datetime, IsoDatetime(timespec="microseconds")],
        WHEN.replace(microsecond=0),
        "2024-05-06T07:08:09.000000+00:00",
        "20240506T070809.000000Z",
    ),
    (Annotated[datetime, EpochDatetime()], datetime(1970, 1, 1, 0, 0, 2, tzinfo=UTC), 2, "2"),
    (
        Annotated[datetime, EpochDatetime()],
        datetime(1970, 1, 1, 0, 0, 2, 500000, tzinfo=UTC),
        2.5,
        "2.5",
    ),
    (
        Annotated[datetime, EpochDatetime(unit="ms")],
        datetime(1970, 1, 1, 0, 0, 1, 500000, tzinfo=UTC),
        1500,
        "1500",
    ),
    (
        Annotated[datetime, EpochDatetime(unit="ms")],
        datetime(1970, 1, 1, 0, 0, 0, 1500, tzinfo=UTC),
        1.5,
        "1.5",
    ),
    (date, TODAY, "2024-05-06", "20240506"),
    (time, time(7, 8, 9, 120000), "07:08:09.120000", "070809.120000"),
    (time, time(7, 8, tzinfo=UTC), "07:08:00+00:00", "070800Z"),
    (Annotated[time, IsoTime(timespec="minutes")], time(7, 8), "07:08", "0708"),
    (Annotated[time, IsoTime()], time(7, 8, 9, tzinfo=PLUS_0530), "07:08:09+05:30", "070809+0530"),
    (timedelta, timedelta(days=1, seconds=5), 86405, "86405"),
    (timedelta, timedelta(seconds=-1.5), -1.5, "-1.5"),
    (timedelta, timedelta(0), 0, "0"),
    (Decimal, Decimal("1.50"), "1.50", "1.50"),
    (Decimal, Decimal("-1E+3"), "-1E+3", "-1E+3"),
    (Annotated[Decimal, DecimalAsNumber()], Decimal("1.5"), 1.5, "1.5"),
    (bytes, b"\x00\xffhi", "AP9oaQ==", "AP9oaQ"),
    (bytes, b"", "", ""),
    (bytes, b"\xfb\xff", "+/8=", "-_8"),
    (Fraction, Fraction(1, 3), "1/3", "1/3"),
    (Color, Color.RED, "r", "r"),
    (Num, Num.TWO, 2, "2"),
    (Shade, Shade.DARK, "dark", "dark"),
    (Annotated[Color, EnumByName()], Color.GREEN, "GREEN", "GREEN"),
    (Annotated[Num, EnumByName()], Num.ONE, "ONE", "ONE"),
    (Literal["a", 1], "a", "a", "a"),
    (Literal["a", 1], 1, 1, "1"),
    (Literal[True, "x"], True, True, "1"),
    (Literal[False, "x"], False, False, "0"),
    (Literal["a", None], None, None, ""),
    (int | None, None, None, ""),
    (int | None, 5, 5, "5"),
    (Optional[Color], Color.GREEN, "g", "g"),  # noqa: UP045
    (Union[str, None], "x", "x", "x"),  # noqa: UP007
    (Annotated[int, "metadata"], 3, 3, "3"),
    (UserId, UserId(5), 5, "5"),
    (UserIds, [UserId(1)], [1], NOT_FLAT),
    (list[int], [1, 2], [1, 2], NOT_FLAT),
    (list[int], [], [], NOT_FLAT),
    (list[Color | None], [Color.RED, None], ["r", None], NOT_FLAT),
    (tuple[int, ...], (1, 2), [1, 2], NOT_FLAT),
    (set[int], {1}, [1], NOT_FLAT),
    (frozenset[str], frozenset({"a"}), ["a"], NOT_FLAT),
    (set[Pair], {Pair(1)}, [{"x": 1, "label": "-"}], NOT_FLAT),
    (tuple[frozenset[int], ...], (frozenset({3}),), [[3]], NOT_FLAT),
    (tuple[int, str], (1, "a"), [1, "a"], NOT_FLAT),
    (dict[str, int], {"a": 1, "b": 2}, {"a": 1, "b": 2}, NOT_FLAT),
    (dict[str, list[UUID]], {"k": [UID]}, {"k": [str(UID)]}, NOT_FLAT),
    (DC, DC(1, "y"), {"a": 1, "b": "y"}, NOT_FLAT),
    (Pair, Pair(1, "a"), {"x": 1, "label": "a"}, NOT_FLAT),
    (Movie, {"title": "x"}, {"title": "x"}, NOT_FLAT),
    (
        Movie,
        {"title": "x", "year": 1, "tags": []},
        {"title": "x", "year": 1, "tags": []},
        NOT_FLAT,
    ),
    (Address, Address(city="x"), {"city": "x", "zip": None}, NOT_FLAT),
    (int | str, 1, 1, NOT_FLAT),
    (int | str, "1", "1", NOT_FLAT),
    (str | int | None, None, None, NOT_FLAT),
    (float | int, 1, 1, NOT_FLAT),
    (float | int, 1.5, 1.5, NOT_FLAT),
    (int | float, 1.0, 1.0, NOT_FLAT),
    (int | bool, True, True, NOT_FLAT),
    (int | bool, 1, 1, NOT_FLAT),
    (UUID | str, UID, str(UID), NOT_FLAT),
    (UUID | str, "x", "x", NOT_FLAT),
    (str | UUID, str(UID), str(UID), NOT_FLAT),
    (Color | Num, Num.TWO, 2, NOT_FLAT),
    (list[int] | dict[str, int], {"a": 1}, {"a": 1}, NOT_FLAT),
    (Pair | int, Pair(1), {"x": 1, "label": "-"}, NOT_FLAT),
    (Annotated[Temp, Celsius()], Temp(1.5), 1.5, "1.5C"),
    (Annotated[Temp, JsonOnly()], Temp(2), 2, NOT_FLAT),
    (list[Annotated[Temp, Celsius()]], [Temp(1)], [1], NOT_FLAT),
]


def _id(row: tuple[Any, ...]) -> str:
    return f"{row[0]!r}-{row[1]!r}"[:80]


VALID_IDS = [_id(row) for row in VALID]
FLAT_ROWS = [row for row in VALID if row[3] is not NOT_FLAT]
NOT_FLAT_ROWS = [row for row in VALID if row[3] is NOT_FLAT]


def same(actual: Any, expected: Any) -> None:
    """Equal, of the same type, and (datetime / time) with the same offset."""
    assert actual == expected
    assert type(actual) is type(expected)
    if isinstance(expected, (datetime, time)):
        assert actual.utcoffset() == expected.utcoffset()
    if isinstance(expected, list | tuple | set | frozenset) and expected:
        assert {type(item) for item in actual} == {type(item) for item in expected}


class TestKinds:
    @pytest.mark.parametrize(("tp", "value", "dumped", "flat"), VALID, ids=VALID_IDS)
    def test_load(self, tp, value, dumped, flat):
        same(json_codec(tp).load(dumped), value)

    @pytest.mark.parametrize(("tp", "value", "dumped", "flat"), VALID, ids=VALID_IDS)
    @pytest.mark.parametrize("encode", [bytes, bytearray, bytes.decode], ids=["b", "ba", "s"])
    def test_load_json(self, tp, value, dumped, flat, encode):
        same(json_codec(tp).load_json(encode(json.dumps(dumped).encode())), value)

    @pytest.mark.parametrize(("tp", "value", "dumped", "flat"), VALID, ids=VALID_IDS)
    def test_dump(self, tp, value, dumped, flat):
        result = json_codec(tp).dump(value)
        assert result == dumped
        assert type(result) is type(dumped)
        assert json.loads(json.dumps(result)) == result  # JSON-shaped

    @pytest.mark.parametrize(("tp", "value", "dumped", "flat"), VALID, ids=VALID_IDS)
    def test_dump_json(self, tp, value, dumped, flat):
        codec = json_codec(tp)
        written = codec.dump_json(value)
        assert written == jdump(codec.dump(value))
        same(codec.load(json.loads(written)), value)
        same(codec.load_json(written), value)

    @pytest.mark.parametrize(("tp", "value", "dumped", "flat"), FLAT_ROWS, ids=map(_id, FLAT_ROWS))
    def test_flat(self, tp, value, dumped, flat):
        codec = json_codec(tp)
        assert codec.kind.flat
        text = codec.dump_flat(value)
        assert text == flat
        assert type(text) is str
        same(codec.load_flat(flat), value)

    @pytest.mark.parametrize(
        ("tp", "value", "dumped", "flat"), NOT_FLAT_ROWS, ids=map(_id, NOT_FLAT_ROWS)
    )
    def test_not_flat(self, tp, value, dumped, flat):
        codec = json_codec(tp)
        assert not codec.kind.flat
        with pytest.raises(TypeError, match="has no flat-string form"):
            codec.dump_flat(value)
        with pytest.raises(TypeError, match="has no flat-string form"):
            codec.load_flat("x")

    @pytest.mark.parametrize(("tp", "value", "dumped", "flat"), VALID, ids=VALID_IDS)
    def test_model_field(self, tp, value, dumped, flat):
        class One(ModelBase):
            v: tp

        schema = json_schema(One)
        obj = One(v=value)  # the constructor accepts what dump accepts
        assert schema.dump(obj) == {"v": dumped}
        assert schema.dump_json(obj) == jdump({"v": dumped})
        same(schema.load({"v": dumped}).v, value)
        same(schema.load_json(jdump({"v": dumped})).v, value)


class TestScalarDetails:
    def test_str_subclass_kept_on_dump(self):
        class Text(str):
            pass

        assert type(json_codec(str).dump(Text("x"))) is Text
        assert json_codec(str).dump_json(Text("x")) == b'"x"'

    def test_int_subclass(self):
        class Big(int):
            pass

        codec = json_codec(int)
        assert type(codec.load(Big(3))) is int
        assert type(codec.dump(Big(3))) is int
        assert type(codec.dump(Num.TWO)) is int
        assert codec.dump_json(Num.TWO) == b"2"

    def test_big_int(self):
        big = 123456789012345678901234567890
        assert json_codec(int).load_json(str(big).encode()) == big
        assert json_codec(int).dump_json(big) == str(big).encode()

    @pytest.mark.parametrize(("text", "value"), [(" 12 ", 12), ("1_000", 1000), ("+5", 5)])
    def test_int_flat_fallback(self, text, value):
        assert json_codec(int).load_flat(text) == value

    def test_float_from_int(self):
        codec = json_codec(float)
        for result in (codec.load(2), codec.load_json(b"2")):
            assert result == 2.0
            assert type(result) is float
        assert type(codec.dump(2)) is float
        assert codec.dump_json(2) == b"2.0"

    def test_float_overflow(self):
        codec = json_codec(float)
        assert errors_of(codec.load, 10**400) == [((), "expected float", 10**400)]
        assert errors_of(codec.load_json, b"1" + b"0" * 400) == [((), "expected float", 10**400)]
        assert errors_of(codec.dump, 10**400) == [((), "expected float", 10**400)]

    def test_float_nan_and_infinity(self):
        codec = json_codec(float)
        assert math.isnan(codec.load(math.nan))
        assert math.isnan(codec.load_json(b"NaN"))
        assert codec.load_json(b"-Infinity") == -math.inf
        assert codec.dump_json(math.nan) == b"NaN"
        assert codec.dump_json(math.inf) == b"Infinity"
        assert codec.dump_json(-math.inf) == b"-Infinity"
        assert json.loads(codec.dump_json(math.inf)) == math.inf
        assert codec.dump_flat(math.inf) == "inf"
        assert codec.load_flat("inf") == math.inf
        assert codec.load_flat(" 2.5 ") == 2.5

    @pytest.mark.parametrize("value", [0.1, 1e-5, 1e-7, 123456789.125, 1e22, 5e-324, 2.0**60])
    def test_float_text_is_repr(self, value):
        codec = json_codec(float)
        assert codec.dump_json(value) == repr(value).encode()
        assert codec.dump_flat(value) == repr(value)
        assert codec.load_json(codec.dump_json(value)) == value

    @pytest.mark.parametrize(
        ("text", "value"),
        [
            ("1", True),
            ("0", False),
            *((text, True) for text in ["true", "True", "T", "t", "yes", "Y", "y", "ON", "on"]),
            *((text, False) for text in ["false", "F", "f", "No", "n", "OFF", "off"]),
        ],
    )
    def test_bool_lax_flat(self, text, value):
        assert json_codec(bool).load_flat(text) is value

    def test_uuid_forms(self):
        codec = json_codec(UUID)
        for text in [str(UID).upper(), "{" + str(UID) + "}", "urn:uuid:" + str(UID), UID.hex]:
            loaded = codec.load(text)
            assert loaded == UID
            assert loaded.is_safe is SafeUUID.unknown
            assert hash(loaded) == hash(UID)
        assert codec.load_flat(str(UID)) == UID

    def test_uuid_pickles(self):
        loaded = json_codec(UUID).load(str(UID))
        assert pickle.loads(pickle.dumps(loaded)) == UID

    @pytest.mark.parametrize(
        ("text", "value"),
        [
            ("2024-05-06T07:08:09Z", datetime(2024, 5, 6, 7, 8, 9, tzinfo=UTC)),
            ("2024-05-06", datetime(2024, 5, 6)),  # noqa: DTZ001
            ("20240506T070809", datetime(2024, 5, 6, 7, 8, 9)),  # noqa: DTZ001
            (
                "2024-05-06 07:08:09-03:00",
                datetime(2024, 5, 6, 7, 8, 9, tzinfo=timezone(-timedelta(hours=3))),
            ),
        ],
    )
    def test_datetime_fromisoformat_forms(self, text, value):
        loaded = json_codec(datetime).load(text)
        assert loaded == value
        assert loaded.utcoffset() == value.utcoffset()

    def test_datetime_utc_singleton(self):
        assert json_codec(datetime).load("2024-05-06T07:08:09+00:00").tzinfo is UTC

    @pytest.mark.parametrize(
        "timespec", ["auto", "hours", "minutes", "seconds", "milliseconds", "microseconds"]
    )
    @pytest.mark.parametrize(
        "value",
        [WHEN, WHEN.replace(microsecond=0), WHEN.replace(tzinfo=None, microsecond=5000)],
        ids=["aware", "whole", "naive"],
    )
    def test_iso_timespec(self, timespec, value):
        codec = json_codec(Annotated[datetime, IsoDatetime(timespec=timespec)])
        assert codec.dump(value) == value.isoformat(timespec=timespec)
        time_codec = json_codec(time)
        assert time_codec.dump(value.timetz()) == value.timetz().isoformat()

    def test_epoch_load(self):
        codec = json_codec(Annotated[datetime, EpochDatetime()])
        for value in [0, 1.5, -1.5, 1715000000.123456, 0.0000005, 1e10]:
            loaded = codec.load(value)
            assert loaded == datetime.fromtimestamp(value, UTC)
            assert loaded.tzinfo is UTC
        assert codec.load_json(b"1.5") == codec.load(1.5)

    def test_epoch_dump_naive_is_local_time(self):
        codec = json_codec(Annotated[datetime, EpochDatetime()])
        naive = datetime(2024, 5, 6, 7, 8, 9)  # noqa: DTZ001
        assert codec.dump(naive) == int(naive.timestamp())
        assert type(codec.dump(naive)) is int
        fraction = naive.replace(microsecond=250000)
        assert codec.dump(fraction) == fraction.timestamp()
        assert codec.dump(WHEN) == WHEN.timestamp()
        assert codec.dump_json(WHEN) == repr(WHEN.timestamp()).encode()

    def test_date_fallback(self):
        assert json_codec(date).load("20240506") == TODAY

    def test_time_forms(self):
        assert json_codec(time).load("07:08") == time(7, 8)
        codec = json_codec(time)
        assert codec.load_json(b'"07:08:09.120"') == time(7, 8, 9, 120000)

    def test_timedelta(self):
        codec = json_codec(timedelta)
        assert codec.load(1.0000005) == timedelta(seconds=1.0000005)
        huge = timedelta(days=999999999, microseconds=1)
        assert codec.dump(huge) == huge.total_seconds()
        assert codec.load_flat("2.5") == timedelta(seconds=2.5)
        assert codec.load_json(b"86405") == timedelta(days=1, seconds=5)

    def test_decimal_as_number_is_exact_on_bytes(self):
        codec = json_codec(Annotated[Decimal, DecimalAsNumber()])
        assert codec.dump(Decimal("1.50")) == 1.5  # the dict path is a lossy float (plan-10 Q9)
        assert codec.dump_json(Decimal("1.50")) == b"1.50"
        assert codec.dump_json(Decimal("1E+2")) == b"1E+2"
        assert codec.dump_json(Decimal("-0.00")) == b"-0.00"
        assert json.loads(codec.dump_json(Decimal("1E+2"))) == 100
        text = "1.10000000000000000001"
        assert str(codec.load_json(text.encode())) == text
        assert codec.load_json(codec.dump_json(Decimal(text))) == Decimal(text)
        assert codec.load(1.1) == Decimal("1.1")
        assert codec.load(5) == Decimal(5)
        assert codec.dump_flat(Decimal("1.5")) == "1.5"
        assert codec.load_flat("1.5") == Decimal("1.5")

    @pytest.mark.parametrize("value", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
    def test_decimal_as_number_must_be_finite(self, value):
        codec = json_codec(Annotated[Decimal, DecimalAsNumber()])
        assert errors_of(codec.dump, value) == [((), "expected Decimal", value)]
        errors = errors_of(codec.dump_json, value)
        assert [error[:2] for error in errors] == [((), "expected Decimal")]

    @pytest.mark.parametrize("text", ["NaN", "Infinity", "-Infinity"])
    def test_decimal_as_number_loads_finite_only(self, text):
        # dump writes finite numbers only, so loading NaN / Infinity would not round-trip
        codec = json_codec(Annotated[Decimal, DecimalAsNumber()])
        assert [error[:2] for error in errors_of(codec.load, float(text))] == [
            ((), "expected Decimal")
        ]
        assert [error[:2] for error in errors_of(codec.load_json, text.encode())] == [
            ((), "expected Decimal")
        ]

    def test_fraction_errors(self):
        codec = json_codec(Fraction)
        # a ZeroDivisionError (ArithmeticError) is the kind's "expected" line
        assert errors_of(codec.load, "1/0") == [((), "expected Fraction", "1/0")]
        with pytest.raises(ConversionError) as exc_info:
            codec.load("x")
        assert exc_info.value.errors == [
            ErrorDetail((), "Invalid literal for Fraction: 'x'", "x"),
        ]
        assert isinstance(exc_info.value.__cause__, ValueError)

    def test_enum_by_type_and_value(self):
        codec = json_codec(Num)
        for value in (True, 2.0, "2", [1]):
            assert errors_of(codec.load, value) == [((), "expected Num", value)]
        assert codec.load(2) is Num.TWO
        assert codec.load_flat("2") is Num.TWO

    def test_tolerant_enum(self):
        codec = json_codec(Status)
        assert codec.load("new-value") is Status.UNKNOWN
        assert codec.load_json(b'"new-value"') is Status.UNKNOWN
        assert codec.load_flat("new-value") is Status.UNKNOWN
        assert errors_of(codec.load, 1) == [((), "expected Status", 1)]
        assert errors_of(codec.load, "boom") == [((), "expected Status", "boom")]

    def test_tolerant_int_enum(self):
        codec = json_codec(Grade)
        assert codec.load(99) is Grade.UNKNOWN
        # the flat codec passes the converted value, not the text
        assert codec.load_flat("99") is Grade.UNKNOWN
        assert errors_of(codec.load, 13) == [((), "expected Grade", 13)]  # ValueError: a miss
        assert errors_of(codec.load, 14) == [((), "expected Grade", 14)]  # not a member
        assert errors_of(codec.load_flat, "x") == [((), "expected Grade", "x")]
        for value in (True, 1.0):
            assert errors_of(codec.load, value) == [((), "expected Grade", value)]

    def test_enum_without_missing_hook_never_calls_it(self):
        assert errors_of(json_codec(Num).load, 99) == [((), "expected Num", 99)]

    def test_enum_by_name(self):
        codec = json_codec(Annotated[Color, EnumByName()])
        assert errors_of(codec.load, "r") == [((), "expected Color", "r")]
        assert errors_of(codec.load, 1) == [((), "expected Color", 1)]
        assert errors_of(codec.dump, "RED") == [((), "expected Color", "RED")]

    def test_mixed_enum_values(self):
        class Mixed(enum.Enum):
            ONE = 1
            TEXT = "1"

        codec = json_codec(Mixed)
        assert codec.load(1) is Mixed.ONE
        assert codec.load("1") is Mixed.TEXT
        assert not codec.kind.flat

    def test_literal(self):
        codec = json_codec(Literal["a", 1, True, None])
        assert codec.kind.label == "one of ['a', 1, True, None]"
        for value in ["a", 1, True, None]:
            assert codec.load(value) == value
            assert codec.load_json(codec.dump_json(value)) == value
        for value in (1.0, False, [1], {"a": 1}):
            assert errors_of(codec.load, value) == [
                ((), "expected one of ['a', 1, True, None]", value)
            ]

    @pytest.mark.parametrize(
        "tp",
        [Literal["a", 1, True], Literal[1, "1"], Literal["", "a"] | None],
        ids=["1-True", "1-'1'", "empty-optional"],
    )
    def test_ambiguous_flat_text_has_no_flat_form(self, tp):
        assert not json_codec(tp).kind.flat

    def test_optional_over_empty_text_has_no_flat_form(self):
        class Blank(enum.Enum):
            EMPTY = ""
            A = "a"

        assert not json_codec(Blank | None).kind.flat
        assert json_codec(Literal["a"] | None).kind.flat
        # str | None keeps its flat form (callback data): "" is None
        assert json_codec(str | None).load_flat("") is None
        assert json_codec(str | None).dump_flat("") == ""

    def test_flat_literal(self):
        codec = json_codec(Literal["a", 2, True])
        assert [codec.dump_flat(value) for value in ["a", 2, True]] == ["a", "2", "1"]
        assert codec.load_flat("1") is True
        assert codec.load_flat("2") == 2

    def test_sequence_input_types(self):
        assert json_codec(list[int]).load((1, 2)) == [1, 2]
        assert json_codec(tuple[int, ...]).load([1, 2]) == (1, 2)
        assert json_codec(set[int]).load_json(b"[1, 2, 2]") == {1, 2}
        assert sorted(json_codec(set[int]).dump({2, 1})) == [1, 2]
        assert json_codec(tuple[int, str]).load((1, "a")) == (1, "a")

    def test_dict_subclass_input(self):
        class Sub(dict):
            pass

        loaded = json_codec(dict[str, int]).load(Sub(a=1))
        assert loaded == {"a": 1}
        assert type(loaded) is dict
        assert json_codec(dict[str, int]).dump(Sub(a=1)) == {"a": 1}

    def test_strings_with_lone_surrogates(self):
        codec = json_codec(str)
        assert codec.dump_json("a\ud800b") == b'"a\\ud800b"'
        for text in ["a\ud800b", "\udfff", "x\ud83d"]:
            assert json.loads(codec.dump_json(text)) == text
            assert codec.load_json(codec.dump_json(text)) == text
        assert json_codec(list[str]).load_json(b'["\\ud800", "x"]') == ["\ud800", "x"]


INVALID_LOAD: list[tuple[Any, Any, list[tuple[Any, str, Any]]]] = [
    (str, 1, [((), "expected str", 1)]),
    (str, None, [((), "expected str", None)]),
    (int, "1", [((), "expected int", "1")]),
    (int, True, [((), "expected int", True)]),
    (int, 1.0, [((), "expected int", 1.0)]),
    (int, None, [((), "expected int", None)]),
    (float, "1.5", [((), "expected float", "1.5")]),
    (float, True, [((), "expected float", True)]),
    (bool, 1, [((), "expected bool", 1)]),
    (bool, "true", [((), "expected bool", "true")]),
    (UUID, "nope", [((), "expected UUID", "nope")]),
    (UUID, 5, [((), "expected UUID", 5)]),
    (datetime, "yesterday", [((), "expected datetime", "yesterday")]),
    (datetime, "2024-02-30T00:00", [((), "expected datetime", "2024-02-30T00:00")]),
    (datetime, 5, [((), "expected datetime", 5)]),
    (Annotated[datetime, EpochDatetime()], True, [((), "expected datetime", True)]),
    (Annotated[datetime, EpochDatetime()], "1", [((), "expected datetime", "1")]),
    (Annotated[datetime, EpochDatetime()], 10**20, [((), "expected datetime", 10**20)]),
    (date, "2024-13-01", [((), "expected date", "2024-13-01")]),
    (date, 5, [((), "expected date", 5)]),
    (time, "25:00", [((), "expected time", "25:00")]),
    (time, 5, [((), "expected time", 5)]),
    (timedelta, True, [((), "expected timedelta", True)]),
    (timedelta, "5", [((), "expected timedelta", "5")]),
    (timedelta, 10**30, [((), "expected timedelta", 10**30)]),
    (Decimal, "abc", [((), "expected Decimal", "abc")]),
    (Decimal, 1.5, [((), "expected Decimal", 1.5)]),
    (Annotated[Decimal, DecimalAsNumber()], True, [((), "expected Decimal", True)]),
    (Annotated[Decimal, DecimalAsNumber()], "1.5", [((), "expected Decimal", "1.5")]),
    (bytes, "!!", [((), "expected bytes", "!!")]),
    (bytes, "AP9oaQ", [((), "expected bytes", "AP9oaQ")]),  # JSON base64 is padded
    (bytes, 5, [((), "expected bytes", 5)]),
    (Fraction, 5, [((), "expected Fraction", 5)]),
    (Color, "x", [((), "expected Color", "x")]),
    (Color, "RED", [((), "expected Color", "RED")]),
    (Num, 3, [((), "expected Num", 3)]),
    (Literal["a"], "b", [((), "expected one of ['a']", "b")]),
    (int | None, "x", [((), "expected int", "x")]),
    (list[int], {"a": 1}, [((), "expected list", {"a": 1})]),
    (list[int], "ab", [((), "expected list", "ab")]),
    (list[int], [1, "a", "b"], [((1,), "expected int", "a"), ((2,), "expected int", "b")]),
    (set[int], ["a"], [((0,), "expected int", "a")]),
    (tuple[int, str], [1], [((), "expected 2 items", [1])]),
    (tuple[int, str], [1, "a", 3], [((), "expected 2 items", [1, "a", 3])]),
    (tuple[int, str], ["a", 1], [((0,), "expected int", "a"), ((1,), "expected str", 1)]),
    (tuple[int, str], "ab", [((), "expected tuple", "ab")]),
    (dict[str, int], [1], [((), "expected dict", [1])]),
    (dict[str, int], {"a": "x", "b": 1}, [(("a",), "expected int", "x")]),
    (DC, [1], [((), "expected DC", [1])]),
    (DC, {"b": 1}, [(("a",), "field required", MISSING), (("b",), "expected str", 1)]),
    (Pair, {"label": "a"}, [(("x",), "field required", MISSING)]),
    (Movie, {"year": 1}, [(("title",), "field required", MISSING)]),
    (Movie, {"title": "x", "year": "1999"}, [(("year",), "expected int", "1999")]),
    (Movie, ["x"], [((), "expected Movie", ["x"])]),
    (
        Address,
        {"zip": "x"},
        [(("city",), "field required", MISSING), (("zip",), "expected int", "x")],
    ),
    (Address, "x", [((), "expected Address", "x")]),
    (int | str, 1.5, [((), "expected int | str", 1.5)]),
    (int | str, None, [((), "expected int | str", None)]),
    (int | str, True, [((), "expected int | str", True)]),
    (Annotated[Temp, Celsius()], "x", [((), "not a temperature", "x")]),
]
INVALID_DUMP: list[tuple[Any, Any, list[tuple[Any, str, Any]]]] = [
    (str, 1, [((), "expected str", 1)]),
    (int, "1", [((), "expected int", "1")]),
    (int, True, [((), "expected int", True)]),
    (int, 1.0, [((), "expected int", 1.0)]),
    (float, "1.5", [((), "expected float", "1.5")]),
    (float, True, [((), "expected float", True)]),
    (bool, 1, [((), "expected bool", 1)]),
    (UUID, str(UID), [((), "expected UUID", str(UID))]),
    (datetime, TODAY, [((), "expected datetime", TODAY)]),
    (Annotated[datetime, EpochDatetime()], 5, [((), "expected datetime", 5)]),
    (date, WHEN, [((), "expected date", WHEN)]),
    (time, "07:00", [((), "expected time", "07:00")]),
    (timedelta, 5, [((), "expected timedelta", 5)]),
    (Decimal, 1, [((), "expected Decimal", 1)]),
    (Decimal, "1.10", [((), "expected Decimal", "1.10")]),
    (bytes, bytearray(b"x"), [((), "expected bytes", bytearray(b"x"))]),
    (bytes, "x", [((), "expected bytes", "x")]),
    (Fraction, 0.5, [((), "expected Fraction", 0.5)]),
    (Color, "r", [((), "expected Color", "r")]),
    (Num, 2, [((), "expected Num", 2)]),
    (Literal["a", 1], "b", [((), "expected one of ['a', 1]", "b")]),
    (Literal["a", 1], True, [((), "expected one of ['a', 1]", True)]),
    (int | None, "x", [((), "expected int", "x")]),
    (list[int], (1, 2), [((), "expected list", (1, 2))]),
    (list[int], [1, "a"], [((1,), "expected int", "a")]),
    (tuple[int, ...], [1, 2], [((), "expected tuple", [1, 2])]),
    (set[int], [1], [((), "expected set", [1])]),
    (set[int], {"a"}, [((0,), "expected int", "a")]),
    (frozenset[int], {1}, [((), "expected frozenset", {1})]),
    (tuple[int, str], (1,), [((), "expected 2 items", (1,))]),
    (tuple[int, str], [1, "a"], [((), "expected tuple", [1, "a"])]),
    (dict[str, int], {"a": "1"}, [(("a",), "expected int", "1")]),
    (dict[str, int], {1: 1}, [(("1",), "expected str key", 1)]),
    (dict[str, int], [("a", 1)], [((), "expected dict", [("a", 1)])]),
    (DC, {"a": 1}, [((), "expected DC", {"a": 1})]),
    (Pair, (1, "a"), [((), "expected Pair", (1, "a"))]),
    (Movie, {"year": 1}, [(("title",), "field required", MISSING)]),
    (Movie, {"title": 1}, [(("title",), "expected str", 1)]),
    (Movie, [("title", "x")], [((), "expected Movie", [("title", "x")])]),
    (Address, {"city": "x"}, [((), "expected Address", {"city": "x"})]),
    (int | str, 1.5, [((), "expected int | str", 1.5)]),
    (int | str, None, [((), "expected int | str", None)]),
    (Annotated[Temp, Celsius()], Temp(-1), [((), "too cold", Temp(-1))]),
]
INVALID_FLAT: list[tuple[Any, str, str]] = [
    (int, "x", "expected int"),
    (int, "", "expected int"),
    (float, "x", "expected float"),
    (bool, "maybe", "expected bool"),
    (bool, "", "expected bool"),
    (UUID, "nope", "expected UUID"),
    (timedelta, "x", "expected timedelta"),
    (Decimal, "1.1.1", "expected Decimal"),
    (bytes, "AP9oaQ==", "expected bytes"),  # the flat form is unpadded base64url
    (bytes, "+/8", "expected bytes"),
    (Color, "x", "expected Color"),
    (Num, "3", "expected Num"),
    (Annotated[Color, EnumByName()], "r", "expected Color"),
    (Literal["a"], "b", "expected one of ['a']"),
    (int | None, "x", "expected int"),
]


def _bad_id(row: tuple[Any, ...]) -> str:
    return f"{row[0]!r}-{row[1]!r}"[:80]


class TestInvalid:
    @pytest.mark.parametrize(
        ("tp", "value", "errors"), INVALID_LOAD, ids=map(_bad_id, INVALID_LOAD)
    )
    def test_load(self, tp, value, errors):
        assert errors_of(json_codec(tp).load, value) == errors

    @pytest.mark.parametrize(
        ("tp", "value", "errors"), INVALID_LOAD, ids=map(_bad_id, INVALID_LOAD)
    )
    def test_load_json(self, tp, value, errors):
        assert errors_of(json_codec(tp).load_json, json.dumps(value).encode()) == errors

    @pytest.mark.parametrize(
        ("tp", "value", "errors"), INVALID_LOAD, ids=map(_bad_id, INVALID_LOAD)
    )
    def test_load_in_a_model(self, tp, value, errors):
        class One(ModelBase):
            v: tp

        expected = [(("v", *loc), message, bad) for loc, message, bad in errors]
        assert errors_of(json_schema(One).load, {"v": value}) == expected
        assert errors_of(json_schema(One).load_json, jdump({"v": value})) == expected

    @pytest.mark.parametrize(
        ("tp", "value", "errors"), INVALID_DUMP, ids=map(_bad_id, INVALID_DUMP)
    )
    def test_dump(self, tp, value, errors):
        assert errors_of(json_codec(tp).dump, value) == errors

    @pytest.mark.parametrize(
        ("tp", "value", "errors"), INVALID_DUMP, ids=map(_bad_id, INVALID_DUMP)
    )
    def test_dump_json(self, tp, value, errors):
        assert errors_of(json_codec(tp).dump_json, value) == errors

    @pytest.mark.parametrize(
        ("tp", "value", "errors"), INVALID_DUMP, ids=map(_bad_id, INVALID_DUMP)
    )
    def test_constructor_checks_like_dump(self, tp, value, errors):
        class One(ModelBase):
            v: tp

        with pytest.raises(ConversionError) as exc_info:
            One(v=value)
        assert exc_info.value.title == f"constructing {One.__qualname__}"
        assert [tuple(e) for e in exc_info.value.errors] == [
            (("v", *loc), message, bad) for loc, message, bad in errors
        ]

    @pytest.mark.parametrize(
        ("tp", "text", "message"), INVALID_FLAT, ids=map(_bad_id, INVALID_FLAT)
    )
    def test_load_flat(self, tp, text, message):
        assert errors_of(json_codec(tp).load_flat, text) == [((), message, text)]

    @pytest.mark.parametrize(
        ("tp", "value"), [(int, "5"), (Color, "r"), (Decimal, 1), (bool, 1), (int | None, "x")]
    )
    def test_dump_flat(self, tp, value):
        codec = json_codec(tp)
        with pytest.raises(ConversionError) as exc_info:
            codec.dump_flat(value)
        assert exc_info.value.errors[0].value == value
        assert exc_info.value.title == f"dumping {codec.kind.label}"

    def test_dump_of_a_huge_timedelta_falls_back_to_python(self):
        codec = json_codec(timedelta)
        value = timedelta(days=10**8, microseconds=1)
        assert codec.dump(value) == value.total_seconds()
        assert codec.dump_flat(value) == repr(value.total_seconds())


class TestUnsupportedAnnotations:
    @pytest.mark.parametrize(
        ("tp", "message"),
        [
            (complex, "unsupported annotation complex"),
            (Any, "unsupported annotation Any"),
            (list, "unsupported annotation list"),
            (dict, "unsupported annotation dict"),
            (tuple[()], r"unsupported annotation tuple\[\(\)\]"),
            (dict[int, str], "dict keys must be str, not int"),
            (dict[UUID, str], "dict keys must be str, not UUID"),
            (set[list[int]], r"unhashable set item list\[int\]"),
            (frozenset[dict[str, int]], "unhashable set item"),
            (set[set[int]], "unhashable set item"),
            (set[Movie], "unhashable set item Movie"),
            (set[list[int] | None], "unhashable set item"),
            (set[DC], "unhashable set item DC"),
            (set[Address], "unhashable set item Address"),
            (set[tuple[list[int], ...]], "unhashable set item"),
            (int | complex, "unsupported annotation complex"),
            (Literal[1.5], "unsupported Literal value 1.5"),
            (Annotated[int, Discriminator("kind")], "Discriminator needs a union of models"),
            (Annotated[int, Key("x")], "Key applies to a field"),
            (Annotated[int, EnumByName()], r"EnumByName\(\) applies to Enum, not int"),
            (Annotated[str, UuidHex()], "applies to UUID, not str"),
            (Annotated[date, IsoDatetime()], "applies to datetime, not date"),
            (Annotated[float, DecimalAsNumber()], "applies to Decimal, not float"),
            (Annotated[int, UuidHex(), Celsius()], "more than one converter or Discriminator"),
        ],
    )
    def test_rejected(self, tp, message):
        with pytest.raises(TypeError, match=message):
            json_codec(tp)

    def test_flag_enum(self):
        class Permission(enum.IntFlag):
            READ = 1

        with pytest.raises(TypeError, match="Permission is a Flag enum"):
            json_codec(Permission)

    @pytest.mark.parametrize("value", [(0, 0), Decimal("0.5"), b"x"])
    def test_enum_values_must_be_json_scalars(self, value):
        Bad = enum.Enum("Bad", {"A": value})  # noqa: N806
        with pytest.raises(TypeError, match=r"Bad\.A value .* is not a JSON scalar"):
            json_codec(Bad)
        # by name, any value works
        assert json_codec(Annotated[Bad, EnumByName()]).load("A") is Bad.A

    def test_untyped_namedtuple(self):
        from collections import namedtuple  # noqa: PLC0415

        with pytest.raises(TypeError, match=r"Plain\.a: the field has no annotation"):
            json_codec(namedtuple("Plain", ["a"]))  # noqa: PYI024

    def test_required_initvar(self):
        @dataclasses.dataclass
        class NeedsSeed:
            value: int
            seed: dataclasses.InitVar[int]

        with pytest.raises(TypeError, match=r"NeedsSeed\.seed: required InitVar"):
            json_codec(NeedsSeed)

    def test_bad_foreign_field_names_class_and_field(self):
        @dataclasses.dataclass
        class BadPoint:
            z: complex

        with pytest.raises(TypeError, match=r"BadPoint\.z: unsupported annotation complex"):
            json_codec(BadPoint)
        with pytest.raises(TypeError, match=r"Holder\.point: .*BadPoint\.z: unsupported"):

            class Holder(ModelBase):
                point: BadPoint

    def test_hook_must_return_a_converter(self):
        class Weird:
            @classmethod
            def __aiogram_converter__(cls) -> Any:
                return 5

        with pytest.raises(TypeError, match=r"Weird\.__aiogram_converter__\(\) returned 5"):
            json_codec(Weird)


class TestDataclassesAndFriends:
    def test_dataclass_options(self):
        @dataclasses.dataclass(slots=True, frozen=True)
        class Frozen:
            a: int
            b: list[int] = dataclasses.field(default_factory=list)

        @dataclasses.dataclass(kw_only=True)
        class KwOnly:
            a: int
            b: int = 2

        @dataclasses.dataclass
        class Seeded:
            value: int
            seed: dataclasses.InitVar[int] = 3
            hidden: int = dataclasses.field(default=0, init=False)

            def __post_init__(self, seed: int) -> None:
                self.hidden = self.value * seed

        assert json_codec(Frozen).load({"a": 1}) == Frozen(1, [])
        assert json_codec(Frozen).load_json(b'{"a": 1, "b": [2]}') == Frozen(1, [2])
        assert json_codec(Frozen).dump(Frozen(1)) == {"a": 1, "b": []}
        assert json_codec(KwOnly).load({"a": 1}) == KwOnly(a=1)
        seeded = json_codec(Seeded).load({"value": 2, "seed": 100, "hidden": 5})
        assert seeded.hidden == 6  # the InitVar default; init=False fields are not loaded
        assert json_codec(Seeded).dump(seeded) == {"value": 2}

    @pytest.mark.parametrize("method", ["load", "load_json"])
    def test_dataclass_post_init_value_error(self, method):
        @dataclasses.dataclass
        class Positive:
            x: int

            def __post_init__(self) -> None:
                if self.x < 0:
                    msg = "x must be >= 0"
                    raise ValueError(msg)

        @dataclasses.dataclass
        class Holder:
            point: Positive

        codec = json_codec(Holder)
        data = {"point": {"x": -1}}
        arg = data if method == "load" else jdump(data)
        with pytest.raises(ConversionError) as exc_info:
            getattr(codec, method)(arg)
        assert [tuple(e) for e in exc_info.value.errors] == [
            (("point",), "x must be >= 0", {"x": -1})
        ]
        assert isinstance(exc_info.value.__cause__, ValueError)

    def test_dataclass_post_init_other_errors_propagate(self):
        @dataclasses.dataclass
        class Strict:
            x: int

            def __post_init__(self) -> None:
                raise KeyError(self.x)

        with pytest.raises(KeyError):
            json_codec(Strict).load({"x": 1})

    def test_namedtuple_default(self):
        assert json_codec(Pair).load({"x": 1}) == Pair(1)
        assert json_codec(Pair).dump(Pair(1)) == {"x": 1, "label": "-"}

    def test_typeddict_required_inside_annotated(self):
        class Total(TypedDict):
            always: int
            maybe: Annotated[NotRequired[int], "meta"]

        class Partial(TypedDict, total=False):
            sometimes: int
            must: Annotated[Required[int], "meta"]

        assert json_codec(Total).load({"always": 1}) == {"always": 1}
        assert errors_of(json_codec(Total).load, {"maybe": 1}) == [
            (("always",), "field required", MISSING)
        ]
        assert json_codec(Partial).load({"must": 1}) == {"must": 1}
        assert errors_of(json_codec(Partial).load, {"sometimes": 1}) == [
            (("must",), "field required", MISSING)
        ]
        assert errors_of(json_codec(Partial).dump, {"sometimes": 1}) == [
            (("must",), "field required", MISSING)
        ]

    def test_typeddict_drops_unknown_keys(self):
        loaded = json_codec(Movie).load({"title": "x", "extra": 1})
        assert loaded == {"title": "x"}
        assert type(loaded) is dict

    def test_key_in_typeddict_rejected(self):
        class Keyed(TypedDict):
            a: Annotated[int, Key("b")]

        with pytest.raises(TypeError, match=r"Keyed\.a: Key applies to a field"):
            json_codec(Keyed)

    def test_recursive_dataclass_and_typeddict(self):
        @dataclasses.dataclass
        class Tree:
            kids: "list[Tree]" = dataclasses.field(default_factory=list)

        assert json_codec(Tree).load({"kids": [{"kids": [{}]}]}) == Tree([Tree([Tree()])])

        class Branch(TypedDict):
            name: str
            children: "NotRequired[list[Branch]]"

        deep = {"name": "a", "children": [{"name": "b", "children": [{"name": "c"}]}]}
        assert json_codec(Branch).load(deep) == deep

    def test_class_body_names_in_string_annotations(self):
        @dataclasses.dataclass
        class WithNested:
            class Kind(enum.Enum):
                X = "x"

            kind: "Kind"

        assert json_codec(WithNested).load({"kind": "x"}).kind is WithNested.Kind.X

    def test_hashable_set_items(self):
        @dataclasses.dataclass(frozen=True)
        class Tagged:
            tags: list[str]

        @dataclasses.dataclass(frozen=True)
        class Labelled:
            name: str
            tags: list[str] = dataclasses.field(default_factory=list, compare=False)

        @dataclasses.dataclass(frozen=True)
        class FrozenTree:
            children: "tuple[FrozenTree, ...]" = ()

        @dataclasses.dataclass(eq=False)
        class Identity:
            x: list[int]

        with pytest.raises(TypeError, match="unhashable set item"):
            json_codec(set[Tagged])
        assert json_codec(set[Labelled]).load([{"name": "a"}]) == {Labelled("a")}
        assert json_codec(set[FrozenTree]).load([{"children": [{}]}]) == {
            FrozenTree((FrozenTree(),))
        }
        assert len(json_codec(set[Identity]).load([{"x": [1]}])) == 1
        assert json_codec(frozenset[Pair]).load([{"x": 1}]) == frozenset({Pair(1)})
        assert json_codec(set[Color | None]).load(["r", None]) == {Color.RED, None}
        assert json_codec(set[Annotated[Temp, Celsius()]]).load([1]) == {Temp(1)}

    def test_hand_written_dataclass_hash(self):
        # plan-10: a frozen (or unsafe_hash) dataclass is taken as hashing its fields; a
        # hand-written __hash__ cannot be told apart after decoration, so the list field rejects it
        @dataclasses.dataclass(frozen=True)
        class Keyed:
            key: int
            tags: list[str] = dataclasses.field(default_factory=list)

            def __hash__(self) -> int:
                return hash(self.key)

        with pytest.raises(TypeError, match="unhashable set item"):
            json_codec(set[Keyed])


class Cat(ModelBase):
    kind: Literal["cat"]
    lives: int = 9


class Dog(ModelBase):
    kind: Literal["dog", "puppy"]
    good: bool = True


class FishDict(TypedDict):
    kind: Literal["fish"]
    fins: int


Pet = Annotated[Cat | Dog, Discriminator("kind")]


class TestUnions:
    @pytest.mark.parametrize(
        ("tp", "value", "expected"),
        [
            (float | int, 1, int),
            (int | float, 1.0, float),
            (int | float, 1, int),
            (str | UUID, str(UID), str),
            (UUID | str, str(UID), UUID),
            (Literal["x"] | int, "x", str),
            (list[int] | dict[str, int], {"a": 1}, dict),
            (Pair | int, {"x": 1}, Pair),
            (Annotated[Temp, Celsius()] | str, 50, Temp),
            (Movie | int, {"title": "t"}, dict),
            (Color | Literal[5], 5, int),
            (DC | Address, {"city": "c"}, Address),
            (int | bool, True, bool),
            (bool | int, 1, int),
            (int | str | None, None, type(None)),
        ],
    )
    def test_smart_load(self, tp, value, expected):
        codec = json_codec(tp)
        assert type(codec.load(value)) is expected
        assert type(codec.load_json(jdump(value))) is expected

    @pytest.mark.parametrize(
        ("tp", "value", "expected"),
        [
            (int | str, Num.TWO, 2),
            (UUID | str, UID, str(UID)),
            (Decimal | float, Decimal("1.5"), "1.5"),
            (Pair | DC, DC(3), {"a": 3, "b": "x"}),
            (Color | int, Color.RED, "r"),
            (Literal["x"] | int, "x", "x"),
            (set[int] | int, {1}, [1]),
            (dict[str, int] | int, {"a": 1}, {"a": 1}),
            (Annotated[Temp, Celsius()] | str, Temp(5), 5),
            (float | bool, True, True),
            (Cat | Dog | None, None, None),
        ],
    )
    def test_smart_dump(self, tp, value, expected):
        codec = json_codec(tp)
        assert codec.dump(value) == expected
        assert codec.dump_json(value) == jdump(expected)

    def test_list_of_uuid_or_str(self):
        codec = json_codec(list[UUID | str])
        assert codec.load([str(UID), "x"]) == [UID, "x"]
        assert codec.dump([UID, "x"]) == [str(UID), "x"]
        assert codec.dump_json([UID, "x"]) == jdump([str(UID), "x"])

    def test_miss_has_member_notes(self):
        codec = json_codec(int | str | Cat)
        with pytest.raises(ConversionError) as exc_info:
            codec.load(1.5)
        assert [tuple(e) for e in exc_info.value.errors] == [((), "expected int | str | Cat", 1.5)]
        assert exc_info.value.__notes__ == [
            "as int: expected int, got 1.5",
            "as str: expected str, got 1.5",
            "as Cat: expected Cat, got 1.5",
        ]
        with pytest.raises(ConversionError) as exc_info:
            codec.load({"kind": "cat", "lives": "x"})
        assert exc_info.value.__notes__[0] == "as Cat: lives: expected int, got 'x'"

    def test_miss_inside_a_model_notes_carry_the_path(self):
        class Owner(ModelBase):
            pet: Cat | Dog

        with pytest.raises(ConversionError) as exc_info:
            json_schema(Owner).load({"pet": {"kind": "cat", "lives": "nine"}})
        assert [tuple(e) for e in exc_info.value.errors] == [
            (("pet",), "expected Cat | Dog", {"kind": "cat", "lives": "nine"})
        ]
        assert exc_info.value.__notes__ == [
            "pet: as Cat: lives: expected int, got 'nine'",
            "pet: as Dog: kind: expected one of ['dog', 'puppy'], got 'cat'",
        ]

    def test_dump_miss(self):
        codec = json_codec(int | str)
        with pytest.raises(ConversionError) as exc_info:
            codec.dump_json(1.5)
        assert exc_info.value.errors[0].message == "expected int | str"
        assert exc_info.value.__notes__

    @pytest.mark.parametrize(("tag", "cls"), [("cat", Cat), ("dog", Dog), ("puppy", Dog)])
    def test_discriminated(self, tag, cls):
        codec = json_codec(Pet)
        assert type(codec.load({"kind": tag})) is cls
        assert type(codec.load_json(jdump({"kind": tag}))) is cls
        dumped = codec.dump(codec.load({"kind": tag}))
        assert dumped["kind"] == tag

    @pytest.mark.parametrize(
        ("value", "errors"),
        [
            ({"lives": 1}, [(("kind",), "field required", MISSING)]),
            ({"kind": "cow"}, [(("kind",), "expected one of ['cat', 'dog', 'puppy']", "cow")]),
            ({"kind": ["cat"]}, [(("kind",), "expected one of ['cat', 'dog', 'puppy']", ["cat"])]),
            # the chosen member collects every error
            (
                {"kind": "cat", "lives": "x"},
                [(("lives",), "expected int", "x")],
            ),
            ("cat", [((), "expected Cat | Dog", "cat")]),
            (None, [((), "expected Cat | Dog", None)]),
        ],
    )
    def test_discriminated_errors(self, value, errors):
        codec = json_codec(Pet)
        assert errors_of(codec.load, value) == errors
        assert errors_of(codec.load_json, jdump(value)) == errors

    def test_discriminated_member_collects(self):
        class Wide(ModelBase):
            kind: Literal["w"]
            a: int
            b: int

        codec = json_codec(Annotated[Wide | Cat, Discriminator("kind")])
        assert errors_of(codec.load, {"kind": "w", "a": "x", "b": "y"}) == [
            (("a",), "expected int", "x"),
            (("b",), "expected int", "y"),
        ]

    def test_nullable_discriminated(self):
        for tp in (Annotated[Cat | Dog | None, Discriminator("kind")], Pet | None):
            codec = json_codec(tp)
            assert codec.load(None) is None
            assert codec.load_json(b"null") is None
            assert codec.dump(None) is None
            assert type(codec.load({"kind": "cat"})) is Cat

    def test_discriminated_mapping_input(self):
        codec = json_codec(Pet)
        assert type(codec.load(MappingProxyType({"kind": "dog"}))) is Dog

    def test_discriminator_over_foreign_classes(self):
        codec = json_codec(Annotated[FishDict | Cat, Discriminator("kind")])
        assert codec.load({"kind": "fish", "fins": 2, "x": 0}) == {"kind": "fish", "fins": 2}
        assert type(codec.load({"kind": "cat"})) is Cat

    def test_recursive_discriminated(self):
        class Leaf(ModelBase):
            kind: Literal["leaf"]

        class Trunk(ModelBase):
            kind: Literal["trunk"]
            children: "list[Annotated[Leaf | Trunk, Discriminator('kind')]]" = []  # noqa: RUF012

        trunk = json_schema(Trunk).load(
            {"kind": "trunk", "children": [{"kind": "leaf"}, {"kind": "trunk", "children": []}]}
        )
        assert [type(child) for child in trunk.children] == [Leaf, Trunk]

    @pytest.mark.parametrize(
        ("tp", "message"),
        [
            (
                Annotated[Cat | Address, Discriminator("kind")],
                "every member needs a Literal 'kind' field",
            ),
            (
                Annotated[Cat | int, Discriminator("kind")],
                "a Discriminator needs a union of models",
            ),
            (
                Annotated[Cat | None, Discriminator("kind")],
                "Discriminator needs a union of models",
            ),
        ],
    )
    def test_bad_discriminator(self, tp, message):
        with pytest.raises(TypeError, match=message):
            codec = json_codec(tp)
            codec.load({"kind": "cat"})

    def test_duplicate_tag(self):
        class Kitten(ModelBase):
            kind: Literal["cat"]

        with pytest.raises(TypeError, match="tag 'cat' is used by more than one member"):
            json_codec(Annotated[Cat | Kitten, Discriminator("kind")]).load({"kind": "cat"})

    def test_tags_under_different_keys(self):
        class Renamed(ModelBase):
            kind: Annotated[Literal["r"], Key("type")]

        with pytest.raises(TypeError, match="store the tag 'kind' under different keys"):
            json_codec(Annotated[Cat | Renamed, Discriminator("kind")]).load({"kind": "cat"})


class TestUserConverters:
    def test_value_error_gets_the_path(self):
        class Weather(ModelBase):
            temps: list[Annotated[Temp, Celsius()]]

        with pytest.raises(ConversionError) as exc_info:
            json_schema(Weather).load({"temps": [1, "x", "y"]})
        assert [tuple(e) for e in exc_info.value.errors] == [
            (("temps", 1), "not a temperature", "x"),
            (("temps", 2), "not a temperature", "y"),
        ]
        cause = exc_info.value.__cause__
        assert isinstance(cause, ValueError)
        assert str(cause) == "not a temperature"

    def test_type_error_propagates(self):
        with pytest.raises(TypeError, match="fatal"):
            json_codec(Annotated[Temp, Celsius()]).load("type")

    def test_a_converter_as_annotation(self):
        codec = json_codec(Annotated[Temp, Celsius()])
        assert codec.load(2) == Temp(2)

    def test_non_json_output_rejected(self):
        codec = json_codec(Annotated[Temp, Celsius()])
        for call in (codec.dump, codec.dump_json):
            errors = errors_of(call, Temp(-2))
            assert len(errors) == 1
            assert errors[0][:2] == ((), "Celsius.to_json returned a non-JSON value")
        for call in (codec.dump, codec.dump_json):
            assert [error[1] for error in errors_of(call, Temp(-3))] == [
                "Celsius.to_json returned a non-JSON value"
            ]

    def test_json_shaped_output_accepted(self):
        codec = json_codec(Annotated[Temp, Celsius()])
        assert codec.dump(Temp(-4)) == {"ok": [1, (2.5, True, None, "s")]}
        assert codec.dump_json(Temp(-4)) == b'{"ok":[1,[2.5,true,null,"s"]]}'

    def test_flat(self):
        codec = json_codec(Annotated[Temp, Celsius()])
        assert codec.dump_flat(Temp(3)) == "3C"
        assert codec.load_flat("3C") == Temp(3.0)
        errors = errors_of(codec.load_flat, "x")
        assert errors[0][0] == ()
        assert errors[0][2] == "x"
        with pytest.raises(TypeError, match=r"to_str returned int, not str"):
            codec.dump_flat(Temp(-5))

    def test_json_only_converter_has_no_flat_form(self):
        assert not json_codec(Annotated[Temp, JsonOnly()]).kind.flat

    def test_base_converter_methods(self):
        converter = Converter()
        with pytest.raises(NotImplementedError):
            converter.to_json(1)
        with pytest.raises(NotImplementedError):
            converter.from_json(1)
        with pytest.raises(TypeError, match=r"Converter\(\) has no flat-string form"):
            converter.to_str(1)
        with pytest.raises(TypeError, match="has no flat-string form"):
            converter.from_str("1")
        assert repr(JsonOnly()) == "JsonOnly()"

    @pytest.mark.parametrize(
        "converter", [IsoDatetime(), EpochDatetime(), DecimalAsNumber(), EnumByName(), UuidHex()]
    )
    def test_native_converters_are_not_callable(self, converter):
        with pytest.raises(TypeError, match="converts only through a schema"):
            converter.to_json(1)
        with pytest.raises(TypeError, match="converts only through a schema"):
            converter.from_json(1)

    def test_converter_set_items(self):
        # a converter decides its values, so the hashability check trusts it
        assert json_codec(frozenset[Annotated[Temp, Celsius()]]).dump(frozenset({Temp(1)})) == [1]


class TestNestedStringAnnotations:
    """Strings inside containers (``list["Node"]``) are evaluated in the model's namespace."""

    def test_nested_strings(self):
        class Tree(ModelBase):
            kids: list["Tree"] = []  # noqa: RUF012, UP037
            parent: Optional["Tree"] = None  # noqa: UP037, UP045
            at: Annotated["datetime", EpochDatetime()] = WHEN  # noqa: UP037
            pairs: set["Pair"] = set()  # noqa: RUF012, UP037

        tree = json_schema(Tree).load({"kids": [{"at": 2}], "pairs": [{"x": 1}]})
        assert tree.kids[0].at == datetime(1970, 1, 1, 0, 0, 2, tzinfo=UTC)
        assert tree.pairs == {Pair(1)}

    def test_set_items_through_markers(self):
        assert json_codec(set[Annotated[int, "meta"]]).load([1]) == {1}
        assert json_codec(frozenset[UserId]).load([1]) == frozenset({1})
        with pytest.raises(TypeError, match="unhashable"):
            json_codec(set[Annotated[list[int], "meta"]])
        with pytest.raises(TypeError, match="unhashable"):
            json_codec(set[UserIds])


class TestAliases:
    def test_newtype_chain(self):
        Inner = NewType("Inner", int)  # noqa: N806
        Outer = NewType("Outer", Inner)  # noqa: N806
        assert json_codec(Outer).load(3) == 3
        assert json_codec(list[Outer]).dump([Outer(Inner(1))]) == [1]

    def test_newtype_class_map(self):
        Stamp = NewType("Stamp", datetime)  # noqa: N806
        codec = json_codec(Stamp, converters={datetime: EpochDatetime()})
        assert codec.dump(datetime(1970, 1, 1, 0, 0, 3, tzinfo=UTC)) == 3

    def test_native_converter_through_newtype(self):
        Stamp = NewType("Stamp", datetime)  # noqa: N806
        codec = json_codec(Annotated[Stamp, EpochDatetime()])
        assert codec.dump(datetime(1970, 1, 1, 0, 0, 3, tzinfo=UTC)) == 3

    @pytest.fixture
    def pep695(self) -> dict[str, Any]:
        if not hasattr(__import__("typing"), "TypeAliasType"):  # pragma: no cover
            pytest.skip("PEP 695 aliases need Python 3.12")
        namespace: dict[str, Any] = {}
        exec(  # noqa: S102
            "type Ids = list[int]\n"
            "type Pair[T] = tuple[T, T]\n"
            "type J = dict[str, J] | list[J] | int | str | None\n"
            "type Chain = Ids\n"
            "type Bad[T] = list[T]\n",
            namespace,
        )
        return namespace

    def test_pep695_simple(self, pep695):
        assert json_codec(pep695["Ids"]).load([1]) == [1]
        assert json_codec(pep695["Chain"]).load([2]) == [2]
        assert errors_of(json_codec(pep695["Ids"]).load, ["x"]) == [((0,), "expected int", "x")]

    def test_pep695_generic(self, pep695):
        codec = json_codec(pep695["Pair"][int])
        assert codec.load([1, 2]) == (1, 2)
        assert errors_of(codec.load, [1, "x"]) == [((1,), "expected int", "x")]
        with pytest.raises(TypeError, match="Bad takes 1 type arguments, got 2"):
            json_codec(pep695["Bad"][int, str])

    def test_pep695_recursive(self, pep695):
        codec = json_codec(pep695["J"])
        data = {"a": [1, {"b": None}, "x"]}
        assert codec.load(data) == data
        assert codec.load_json(jdump(data)) == data
        assert codec.dump_json(data) == jdump(data)
        with pytest.raises(ConversionError) as exc_info:
            codec.load({"a": 1.5})
        assert exc_info.value.errors[0].message.startswith("expected dict | list")

    def test_pep695_in_a_set_and_with_a_converter(self, pep695):
        namespace = dict(pep695)
        namespace["datetime"] = datetime
        exec(  # noqa: S102
            "type Loop = list[Loop] | int\n"
            "type Nest = tuple[Nest, ...] | int\n"
            "type Stamp = datetime\n",
            namespace,
        )
        assert json_codec(set[namespace["Nest"]]).load([[1, [2]]]) == {(1, (2,))}
        stamp = json_codec(Annotated[namespace["Stamp"], EpochDatetime()])
        assert stamp.dump(datetime(1970, 1, 1, 0, 0, 3, tzinfo=UTC)) == 3
        assert json_codec(tuple[namespace["Ids"], namespace["Ids"]]).load([[1], [2]]) == ([1], [2])
        assert json_codec(set[namespace["Pair"][int]]).load([[1, 1]]) == {(1, 1)}
        with pytest.raises(TypeError, match="unhashable"):
            json_codec(set[namespace["Ids"]])
        with pytest.raises(TypeError, match="unhashable"):
            json_codec(set[namespace["Loop"]])
        assert json_codec(Annotated[namespace["Ids"], Celsius()]).load(1) == Temp(1)


class TestJsonBytes:
    @pytest.mark.parametrize(
        ("data", "message"),
        [
            (b"[1,", "invalid JSON: EOF while parsing a value at line 1 column 3"),
            (b'[1, "a"] x', "invalid JSON: trailing characters at line 1 column 10"),
            (b"[1,\n 2,]", "invalid JSON: trailing comma at line 2 column 4"),
            (b'[1, "\xff"]', "invalid JSON: invalid UTF-8 at line 1 column 6"),
            (b"", "invalid JSON: EOF while parsing a value at line 1 column 0"),
            ("[\ud800]", "invalid JSON: the str contains a lone surrogate"),
            ("﻿[1]", None),  # a BOM in a str is invalid, as json.loads says
            (b'["\\ud800\\x"]', None),
            (b'["a", "b"] x', None),  # a later syntax error wins over value errors
        ],
    )
    def test_invalid(self, data, message):
        with pytest.raises(ConversionError) as exc_info:
            json_codec(list[int]).load_json(data)
        (error,) = exc_info.value.errors
        assert error.loc == ()
        assert error.value is MISSING
        assert error.message.startswith("invalid JSON: ")
        if message is not None:
            assert error.message == message

    def test_invalid_utf8_in_a_skipped_string(self):
        with pytest.raises(ConversionError, match="invalid JSON"):
            json_schema(Address).load_json(b'{"city": "a", "other": "\xff"}')

    def test_invalid_json_anywhere_is_fatal_for_the_document(self):
        with pytest.raises(ConversionError) as exc_info:
            json_schema(Address).load_json(b'{"city": 1, "zzz": [1,}')
        assert len(exc_info.value.errors) == 1
        assert exc_info.value.errors[0].message.startswith("invalid JSON")

    @pytest.mark.parametrize("make", [bytes, bytearray], ids=["bytes", "bytearray"])
    def test_bom_skipped_for_bytes(self, make):
        assert json_codec(list[int]).load_json(make(b"\xef\xbb\xbf[1]")) == [1]

    def test_not_text(self):
        with pytest.raises(TypeError, match="must be str, bytes or bytearray, not int"):
            json_codec(int).load_json(5)
        with pytest.raises(TypeError, match="not memoryview"):
            json_codec(int).load_json(memoryview(b"1"))

    def test_text_subclasses(self):
        class Raw(bytes):
            pass

        class Text(str):
            pass

        assert json_schema(Address).load_json(Raw(b'{"city": "a"}')).city == "a"
        assert json_schema(Address).load_json(Text('{"city": "b"}')).city == "b"

    def test_repeated_keys_last_wins(self):
        codec = json_codec(dict[str, int])
        assert codec.load_json(b'{"a": "x", "a": 1}') == {"a": 1}
        assert errors_of(codec.load_json, b'{"a": 1, "a": "x"}') == [(("a",), "expected int", "x")]
        assert json_schema(Address).load_json(b'{"city": 1, "city": "a"}').city == "a"
        movie = json_codec(Movie).load_json(b'{"title": 1, "title": "t"}')
        assert movie == {"title": "t"}

    def test_repeated_key_runs_the_user_converter_twice(self):
        calls = []

        class Counting(Converter):
            def to_json(self, value: Any) -> Any:
                return value

            def from_json(self, value: Any) -> Any:
                calls.append(value)
                return value

        class Holder(ModelBase):
            v: Annotated[int, Counting()]

        assert json_schema(Holder).load_json(b'{"v": 1, "v": 2}').v == 2
        assert calls == [1, 2]

    def test_error_order_is_field_order(self):
        class Two(ModelBase):
            a: int
            b: int

        assert errors_of(json_schema(Two).load_json, b'{"b": "y", "a": "x"}') == [
            (("a",), "expected int", "x"),
            (("b",), "expected int", "y"),
        ]

    def test_unknown_values_are_skipped(self):
        data = b'{"city": "a", "unknown": [{"deep": [1, 2.5, null, "x", true]}], "z": NaN}'
        assert json_schema(Address).load_json(data).city == "a"

    def test_union_inside_bytes(self):
        codec = json_codec(list[int | str | Cat])
        assert codec.load_json(b'[1, "a", {"kind": "cat"}]')[:2] == [1, "a"]
        assert errors_of(codec.load_json, b"[1, 2.5]") == [((1,), "expected int | str | Cat", 2.5)]

    def test_deep_nesting_raises_recursion_error(self):
        class Node(ModelBase):
            value: int
            children: "list[Node]" = []  # noqa: RUF012

        depth = 100_000
        text = '{"value": 0, "children": [' * depth + "]}" * depth
        with pytest.raises(RecursionError):
            json_schema(Node).load_json(text.encode())
        nested: dict[str, Any] = {"value": 0}
        nested["children"] = [nested]
        with pytest.raises(RecursionError):
            json_schema(Node).load(nested)
        node = Node(value=0)
        node.children.append(node)
        for call in (json_schema(Node).dump, json_schema(Node).dump_json):
            with pytest.raises(RecursionError):
                call(node)

    def test_depth_512(self):
        class Node(ModelBase):
            children: "list[Node]" = []  # noqa: RUF012

        def nested(depth: int) -> str:
            return '{"children": [' * depth + "]}" * depth

        node = json_schema(Node).load_json(nested(200).encode())
        assert json.loads(json_schema(Node).dump_json(node)) == json.loads(nested(200))
        with pytest.raises(RecursionError):
            json_schema(Node).load_json(nested(600).encode())


class TestErrors:
    def test_str_and_repr(self):
        error = ConversionError(
            "loading Form",
            [
                ErrorDetail(("address", "zip"), "expected int", "abc"),
                ErrorDetail(("tags", 2), "expected str", 5),
                ErrorDetail(("name",), "field required"),
                ErrorDetail((), "invalid JSON: x"),
            ],
        )
        assert str(error) == (
            "4 errors loading Form\n"
            "  address.zip: expected int, got 'abc'\n"
            "  tags[2]: expected str, got 5\n"
            "  name: field required\n"
            "  invalid JSON: x"
        )
        assert repr(error).startswith(
            "ConversionError('loading Form', errors=["
            "ErrorDetail(loc=('address', 'zip'), message='expected int', value='abc'), "
            "ErrorDetail(loc=('tags', 2), message='expected str', value=5), "
            "ErrorDetail(loc=('name',), message='field required', value="
        )
        assert error.title == "loading Form"
        assert isinstance(error, ValueError)

    def test_header_for_one_error(self):
        with pytest.raises(ConversionError) as exc_info:
            json_schema(Address).load({"city": 1})
        assert str(exc_info.value) == "1 error loading Address\n  city: expected str, got 1"

    def test_long_values_are_shortened(self):
        error = ConversionError("x", [ErrorDetail(("a",), "bad", "y" * 500)])
        assert len(str(error)) < 150

    @pytest.mark.parametrize(
        ("loc", "text"),
        [
            ((), ""),
            (("a",), "a"),
            (("address", "zip"), "address.zip"),
            (("tags", 2), "tags[2]"),
            ((2, "a"), "[2].a"),
            (("m", "k", 0, 1), "m.k[0][1]"),
        ],
    )
    def test_render_loc(self, loc, text):
        assert render_loc(loc) == text

    def test_cap(self):
        codec = json_codec(list[int])
        for call, arg in [
            (codec.load, ["x"] * 500),
            (codec.load_json, jdump(["x"] * 500)),
            (codec.dump, ["x"] * 500),
            (codec.dump_json, ["x"] * 500),
            (json_codec(dict[str, int]).load, {str(i): "x" for i in range(500)}),
        ]:
            with pytest.raises(ConversionError) as exc_info:
                call(arg)
            assert len(exc_info.value.errors) == 100
        with pytest.raises(ConversionError) as exc_info:
            codec.load(["x"] * 500)
        assert exc_info.value.errors[-1].loc == (99,)
        assert str(exc_info.value).startswith("100 errors loading list\n")

    def test_pickle(self):
        with pytest.raises(ConversionError) as exc_info:
            json_schema(Address).load({"city": 1, "zip": "x"})
        error = exc_info.value
        clone = pickle.loads(pickle.dumps(error))
        assert type(clone) is ConversionError
        assert clone.title == error.title
        assert clone.errors == error.errors
        assert str(clone) == str(error)

    def test_error_detail(self):
        detail = ErrorDetail(("a",), "field required")
        assert detail.value is MISSING
        assert detail == (("a",), "field required", MISSING)


def test_mapping_input():
    class Model(ModelBase):
        a: int
        b: dict[str, int] = {}  # noqa: RUF012

    class Lazy(Mapping):
        def __init__(self, data: dict[str, Any]) -> None:
            self.data = data

        def __getitem__(self, key: str) -> Any:
            return self.data[key]

        def __iter__(self) -> Any:
            return iter(self.data)

        def __len__(self) -> int:
            return len(self.data)

    assert json_schema(Model).load(Lazy({"a": 1})).a == 1
    assert json_schema(Model).load(MappingProxyType({"a": 2})).a == 2
    assert errors_of(json_schema(Model).load, Lazy({"a": "x"})) == [(("a",), "expected int", "x")]
