"""Contract suite for the shared converter core (F-08, R16): the Python layer over the Rust core."""

from __future__ import annotations

import dataclasses
import gc
import json
import math
import subprocess
import sys
import textwrap
import types
import weakref
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum, IntEnum, IntFlag, StrEnum
from fractions import Fraction
from pathlib import Path
from collections import namedtuple
from typing import (
    Annotated,
    Any,
    ClassVar,
    Literal,
    NamedTuple,
    NotRequired,
    Optional,
    Required,
    TypedDict,
    Union,
)
from uuid import UUID

import pytest

from aiogram.utils import _converters
from aiogram.utils._converters import (
    FIELDS_SET,
    ConversionError,
    Converter,
    Discriminator,
    ModelConverter,
    converter_for,
    model_converter,
    register_converter,
    register_model,
)


class Model:
    """The minimal base F-09 (FSMData) / F-11 (CallbackData) build on."""

    __converter__: ClassVar[ModelConverter]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.__converter__ = register_model(cls)

    def __init__(self, **kwargs: Any) -> None:
        self.__converter__.init(self, kwargs)


class Kind(Enum):
    A = "a"
    B = "b"


class Level(IntEnum):
    LOW = 1
    HIGH = 2


class Color(StrEnum):
    RED = "red"


class Address(Model):
    city: str
    zip: str | None = None


@dataclasses.dataclass
class Point:
    x: int
    y: int = 0

    def __post_init__(self) -> None:
        if self.x < 0:
            msg = "x must be >= 0"
            raise ValueError(msg)


class OrderForm(Model):
    item_id: int
    qty: int = 1
    address: Address | None = None
    tags: list[str] = []  # noqa: RUF012
    meta: dict[str, int] = dataclasses.field(default_factory=dict)
    point: Point | None = None
    created: datetime | None = None


class Flat(Model):
    id: int
    name: str
    kind: Kind
    page: int | None = None
    active: bool = False


class Node(Model):
    value: int
    children: list[Node] = []  # noqa: RUF012


class Forward(Model):  # refers to a class defined below: compiled on first use
    later: Later | None = None


class Later(Model):
    back: Forward | None = None


class Dangling(Model):
    missing: NeverDefined  # type: ignore[name-defined]  # noqa: F821


@dataclasses.dataclass
class Tree:
    kids: list[Tree] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class BadPoint:  # its Holder (in a test) must fail at class creation
    z: complex


class Skips(Model):
    LIMIT: ClassVar[int] = 3
    _private: int = 0
    value: int = 0


class Pair(NamedTuple):
    x: int
    label: str = "-"


class Movie(TypedDict, total=False):
    title: Required[str]
    year: int
    tags: NotRequired[list[str]]


class TimesTen(Converter):
    """A per-field converter (``Annotated[int, TimesTen()]``)."""

    def to_json(self, value):
        return value * 10

    def from_json(self, value):
        return value // 10


UID = UUID("12345678-1234-5678-1234-567812345678")
NOW = datetime(2026, 11, 18, 12, 30, tzinfo=timezone.utc)
TODAY = date(2026, 11, 18)
NOT_FLAT = object()

# annotation, python value, JSON value, flat string (NOT_FLAT: no string codec)
VALID = [
    (str, "x", "x", "x"),
    (str, "", "", ""),
    (int, 5, 5, "5"),
    (int, -7, -7, "-7"),
    (float, 1.5, 1.5, "1.5"),
    (bool, True, True, "1"),
    (bool, False, False, "0"),
    (Decimal, Decimal("1.10"), "1.10", "1.10"),
    (Fraction, Fraction(1, 3), "1/3", "1/3"),
    (UUID, UID, str(UID), UID.hex),
    (datetime, NOW, NOW.isoformat(), NOT_FLAT),
    (date, TODAY, "2026-11-18", NOT_FLAT),
    (Kind, Kind.A, "a", "a"),
    (Level, Level.HIGH, 2, "2"),
    (Color, Color.RED, "red", "red"),
    (Literal["a", 1], "a", "a", "a"),
    (Literal["a", 1], 1, 1, "1"),
    (Literal[True, "x"], True, True, "1"),
    (Literal["a", None], None, None, ""),
    (int | None, None, None, ""),
    (int | None, 5, 5, "5"),
    (Optional[Kind], Kind.B, "b", "b"),  # noqa: UP045
    (Union[str, None], "x", "x", "x"),  # noqa: UP007
    (Annotated[int, "meta"], 3, 3, "3"),
    (list[int], [1, 2], [1, 2], NOT_FLAT),
    (list[int], [], [], NOT_FLAT),
    (tuple[int, ...], (1, 2), [1, 2], NOT_FLAT),
    (dict[str, int], {"a": 1}, {"a": 1}, NOT_FLAT),
    (list[Kind | None], [Kind.A, None], ["a", None], NOT_FLAT),
    (dict[str, list[UUID]], {"k": [UID]}, {"k": [str(UID)]}, NOT_FLAT),
    (Point, Point(1, 2), {"x": 1, "y": 2}, NOT_FLAT),
    (datetime | None, None, None, NOT_FLAT),
    (set[int], {1, 2}, [1, 2], NOT_FLAT),
    (frozenset[str], frozenset({"a"}), ["a"], NOT_FLAT),
    (tuple[frozenset[int], ...], (frozenset({3}),), [[3]], NOT_FLAT),
    (int | str, 1, 1, NOT_FLAT),
    (int | str, "1", "1", NOT_FLAT),
    (str | int | None, None, None, NOT_FLAT),
    (float | int, 1, 1, NOT_FLAT),
    (float | int, 1.5, 1.5, NOT_FLAT),
    (str | UUID, str(UID), str(UID), NOT_FLAT),
    (UUID | str, UID, str(UID), NOT_FLAT),
    (Kind | Level, Level.HIGH, 2, NOT_FLAT),
    (Pair, Pair(1, "a"), {"x": 1, "label": "a"}, NOT_FLAT),
    (Pair, Pair(1), {"x": 1, "label": "-"}, NOT_FLAT),
    (Movie, {"title": "x"}, {"title": "x"}, NOT_FLAT),
    (
        Movie,
        {"title": "x", "year": 1, "tags": []},
        {"title": "x", "year": 1, "tags": []},
        NOT_FLAT,
    ),
    (Annotated[int, TimesTen()], 3, 30, NOT_FLAT),
]
VALID_FLAT = [row for row in VALID if row[3] is not NOT_FLAT]
VALID_NOT_FLAT = [row for row in VALID if row[3] is NOT_FLAT]

INVALID_DUMP = [  # python value rejected by to_json
    (str, 1),
    (int, "1"),
    (int, True),
    (int, 1.0),
    (float, "1.5"),
    (float, True),
    (bool, 1),
    (Decimal, 1),
    (Decimal, "1.10"),
    (Fraction, 0.5),
    (UUID, str(UID)),
    (datetime, TODAY),
    (date, NOW),
    (Kind, "a"),
    (Level, 2),
    (Literal["a", 1], "b"),
    (Literal["a", 1], True),
    (Literal["a", 1], ["a"]),
    (int | None, "x"),
    (list[int], (1, 2)),
    (list[int], [1, "2"]),
    (tuple[int, ...], [1, 2]),
    (dict[str, int], {"a": "1"}),
    (dict[str, int], {1: 1}),
    (dict[str, int], [("a", 1)]),
    (Point, {"x": 1}),
    (set[int], [1]),
    (set[int], {"a"}),
    (int | str, 1.5),
    (int | str, None),
    (int | str, True),
    (Pair, (1, "a")),
    (Movie, {"year": 1}),
    (Movie, {"title": 1}),
    (Movie, [("title", "x")]),
]
INVALID_LOAD = [  # JSON value rejected by from_json
    (str, 1),
    (int, "1"),
    (int, False),
    (float, "1.5"),
    (bool, "true"),
    (Decimal, 1.5),
    (Decimal, "abc"),
    (Fraction, "1/0"),
    (UUID, "not-a-uuid"),
    (UUID, 1),
    (datetime, "yesterday"),
    (date, "2026-13-01"),
    (Kind, "c"),
    (Level, 3),
    (Literal["a"], "b"),
    (int | None, "x"),
    (list[int], {"a": 1}),
    (list[int], [1, None]),
    (dict[str, int], {"a": None}),
    (Point, [1, 2]),
    (Point, {"y": 1}),
    (set[int], ["a"]),
    (set[int], {"a": 1}),
    (int | str, 1.5),
    (int | str, None),
    (int | str, False),
    (Pair, {"label": "a"}),
    (Pair, [1, "a"]),
    (Movie, {"year": 1}),
    (Movie, {"title": "x", "year": "1999"}),
    (Movie, ["x"]),
]
INVALID_STR = [  # text rejected by from_str
    (int, "x"),
    (int, ""),
    (float, "x"),
    (bool, "maybe"),
    (Decimal, "1.1.1"),
    (Fraction, "x"),
    (UUID, "xyz"),
    (Kind, "c"),
    (Level, "3"),
    (Literal["a"], "b"),
    (int | None, "x"),
]


def _ids(rows: list[tuple[Any, ...]]) -> list[str]:
    return [f"{getattr(row[0], '__name__', row[0])!s}-{row[1]!r}" for row in rows]


class TestScalarContract:
    @pytest.mark.parametrize(("tp", "py", "js", "_text"), VALID, ids=_ids(VALID))
    def test_to_json(self, tp, py, js, _text):
        result = converter_for(tp).to_json(py)
        assert result == js
        assert type(result) is type(js)

    @pytest.mark.parametrize(("tp", "py", "js", "_text"), VALID, ids=_ids(VALID))
    def test_from_json(self, tp, py, js, _text):
        result = converter_for(tp).from_json(js)
        assert result == py
        assert type(result) is type(py)

    @pytest.mark.parametrize(("tp", "py", "_js", "_text"), VALID, ids=_ids(VALID))
    def test_json_round_trip(self, tp, py, _js, _text):
        converter = converter_for(tp)
        assert converter.from_json(converter.to_json(py)) == py

    @pytest.mark.parametrize(("tp", "py", "_js", "text"), VALID_FLAT, ids=_ids(VALID_FLAT))
    def test_str_codec(self, tp, py, _js, text):
        converter = converter_for(tp)
        assert converter.flat
        assert converter.to_str(py) == text
        result = converter.from_str(text)
        assert result == py
        assert type(result) is type(py)

    @pytest.mark.parametrize(("tp", "py", "_js", "_t"), VALID_NOT_FLAT, ids=_ids(VALID_NOT_FLAT))
    def test_not_flat(self, tp, py, _js, _t):
        converter = converter_for(tp)
        assert not converter.flat
        with pytest.raises(TypeError, match="no flat-string form"):
            converter.to_str(py)
        with pytest.raises(TypeError, match="no flat-string form"):
            converter.from_str("x")

    @pytest.mark.parametrize(("tp", "value"), INVALID_DUMP, ids=_ids(INVALID_DUMP))
    def test_to_json_rejects(self, tp, value):
        with pytest.raises(ConversionError):
            converter_for(tp).to_json(value)

    @pytest.mark.parametrize(("tp", "value"), INVALID_LOAD, ids=_ids(INVALID_LOAD))
    def test_from_json_rejects(self, tp, value):
        with pytest.raises(ConversionError):
            converter_for(tp).from_json(value)

    @pytest.mark.parametrize(("tp", "value"), INVALID_STR, ids=_ids(INVALID_STR))
    def test_from_str_rejects(self, tp, value):
        with pytest.raises(ConversionError):
            converter_for(tp).from_str(value)

    @pytest.mark.parametrize(("tp", "value"), [(int, "x"), (Kind, "a"), (Decimal, 1)])
    def test_to_str_rejects(self, tp, value):
        with pytest.raises(ConversionError):
            converter_for(tp).to_str(value)

    def test_coercions(self):
        assert converter_for(int).to_json(Level.HIGH) == 2
        assert type(converter_for(int).to_json(Level.HIGH)) is int
        assert converter_for(float).from_json(2) == 2.0
        assert type(converter_for(float).from_json(2)) is float
        assert converter_for(tuple[int, ...]).from_json((1, 2)) == (1, 2)
        assert converter_for(list[int]).from_json((1, 2)) == [1, 2]
        assert converter_for(UUID).from_str(str(UID)) == UID

    @pytest.mark.parametrize(
        ("text", "value"),
        [("true", True), ("FALSE", False), ("yes", True), ("off", False), ("t", True)],
    )
    def test_bool_lax_text(self, text, value):
        assert converter_for(bool).from_str(text) is value


class TestUnsupported:
    @pytest.mark.parametrize(
        "tp",
        [
            complex,
            bytes,
            list,
            dict,
            set[list[int]],
            frozenset[dict[str, int]],
            set[set[int]],
            set[Movie],
            dict[int, str],
            tuple[int, str],
            int | complex,
            Annotated[int, Discriminator("kind")],
            Literal[1.5],
            Any,
            list[[1]],  # type: ignore[misc]  # unhashable annotation
        ],
    )
    def test_converter_for(self, tp):
        with pytest.raises(TypeError):
            converter_for(tp)

    def test_class_creation_names_class_and_field(self):
        with pytest.raises(TypeError, match=r"Bad\.value: unsupported annotation"):

            class Bad(Model):
                ok: int
                value: complex

        assert not any(cls.__name__ == "Bad" for cls in _converters._models)

    def test_nested_dataclass_error_at_class_creation(self):
        with pytest.raises(TypeError, match=r"Holder\.point: BadPoint\.z"):

            class Holder(Model):
                point: BadPoint

        assert BadPoint not in _converters._models
        with pytest.raises(TypeError):  # not cached: fails again
            converter_for(BadPoint)

    def test_model_converter_rejects_plain_types(self):
        with pytest.raises(TypeError, match="neither a registered model nor a dataclass"):
            model_converter(int)

    def test_unresolved_forward_ref_fails_on_first_use(self):
        with pytest.raises(NameError):
            Dangling.__converter__.from_json({"missing": 1})


class Mixed(Enum):
    ONE = 1
    TEXT = "1"


class DecimalValued(Enum):
    HALF = Decimal("0.5")


class TupleValued(Enum):
    ORIGIN = (0, 0)


@dataclasses.dataclass
class NeedsSeed:
    value: int
    seed: dataclasses.InitVar[int]


@dataclasses.dataclass
class OptionalSeed:
    value: int
    seed: dataclasses.InitVar[int] = 0


class TestCodexFindings:
    @pytest.mark.parametrize(
        ("tp", "values"),
        [(Literal[1, "1"], [1, "1"]), (Literal[True, 1], [True, 1]), (Mixed, list(Mixed))],
    )
    def test_ambiguous_flat_text_has_no_flat_form(self, tp, values):
        converter = converter_for(tp)
        assert not converter.flat
        for value in values:
            assert converter.from_json(converter.to_json(value)) == value
            with pytest.raises(TypeError, match="no flat-string form"):
                converter.to_str(value)
        with pytest.raises(TypeError, match="no flat-string form"):
            converter.from_str("1")

    @pytest.mark.parametrize("tp", [DecimalValued, TupleValued])
    def test_enum_values_must_be_json_scalars(self, tp):
        with pytest.raises(TypeError, match="JSON"):
            converter_for(tp)

    def test_required_initvar_rejected(self):
        with pytest.raises(TypeError, match=r"NeedsSeed\.seed: required InitVar"):
            converter_for(NeedsSeed)
        assert model_converter(OptionalSeed).from_json({"value": 1}) == OptionalSeed(1)

    def test_register_converter_for_annotated(self, monkeypatch):
        monkeypatch.setattr(_converters, "_extra", {})
        custom = CelsiusConverter()
        register_converter(Annotated[float, "celsius"], custom)
        assert converter_for(Annotated[float, "celsius"]) is custom
        assert converter_for(Annotated[float, "other"]) is converter_for(float)
        assert converter_for(Annotated[int, {"unhashable": []}]) is converter_for(int)


class TestModels:
    def test_flat_load(self):
        form = Flat.__converter__.from_json({"id": 1, "name": "x", "kind": "a", "extra": 0})
        assert (form.id, form.name, form.kind, form.page, form.active) == (
            1,
            "x",
            Kind.A,
            None,
            False,
        )
        assert getattr(form, FIELDS_SET) == {"id", "name", "kind"}
        assert not hasattr(form, "extra")

    def test_field_order(self):
        assert [f.name for f in Flat.__converter__.fields] == [
            "id",
            "name",
            "kind",
            "page",
            "active",
        ]

    def test_skips_classvar_and_private(self):
        assert [f.name for f in Skips.__converter__.fields] == ["value"]

    def test_nested_round_trip(self):
        data = {
            "item_id": 5,
            "qty": 2,
            "address": {"city": "Kyiv", "zip": "01001"},
            "tags": ["a", "b"],
            "meta": {"k": 1},
            "point": {"x": 1, "y": 2},
            "created": NOW.isoformat(),
        }
        form = OrderForm.__converter__.from_json(data)
        assert isinstance(form.address, Address)
        assert form.address.city == "Kyiv"
        assert form.point == Point(1, 2)
        assert form.created == NOW
        assert OrderForm.__converter__.dump(form) == data

    @pytest.mark.parametrize(
        ("data", "path", "value"),
        [
            ({"item_id": "5"}, "item_id", "5"),
            ({"item_id": 5, "address": {"city": "x", "zip": 1}}, "address.zip", 1),
            ({"item_id": 5, "address": {}}, "address.city", _converters.MISSING),
            ({"item_id": 5, "tags": ["a", "b", 3]}, "tags[2]", 3),
            ({"item_id": 5, "meta": {"k": "v"}}, "meta['k']", "v"),
            ({"item_id": 5, "point": {"x": "1"}}, "point.x", "1"),
            ({}, "item_id", _converters.MISSING),
        ],
    )
    def test_load_error_path(self, data, path, value):
        with pytest.raises(ConversionError) as exc_info:
            OrderForm.__converter__.from_json(data)
        assert exc_info.value.path == path
        assert exc_info.value.value == value

    def test_dump_error_path(self):
        form = OrderForm(item_id=5, address=Address(city=1))
        with pytest.raises(ConversionError) as exc_info:
            OrderForm.__converter__.dump(form)
        assert exc_info.value.path == "address.city"

    def test_recursive_error_path(self):
        with pytest.raises(ConversionError) as exc_info:
            Node.__converter__.from_json({"value": 1, "children": [{"value": 2}, {"value": "x"}]})
        assert exc_info.value.path == "children[1].value"
        assert str(exc_info.value) == "children[1].value: expected an integer (got 'x')"

    def test_error_message_without_path_or_value(self):
        assert str(ConversionError("boom")) == "boom"
        assert str(ConversionError("boom", 1)) == "boom (got 1)"

    def test_not_a_mapping(self):
        with pytest.raises(ConversionError, match="expected an object"):
            OrderForm.__converter__.from_json([1])

    def test_to_json_needs_instance(self):
        with pytest.raises(ConversionError, match="OrderForm instance"):
            OrderForm.__converter__.to_json({"item_id": 1})

    def test_post_init_error(self):
        with pytest.raises(ConversionError) as exc_info:
            OrderForm.__converter__.from_json({"item_id": 1, "point": {"x": -1}})
        assert exc_info.value.path == "point"
        assert exc_info.value.reason == "x must be >= 0"

    def test_dataclass_top_level(self):
        converter = model_converter(Point)
        assert converter is model_converter(Point)
        assert converter.from_json({"x": 3}) == Point(3, 0)
        assert converter.dump(Point(3), exclude_unset=True) == {"x": 3, "y": 0}


class TestDefaults:
    def test_init_defaults_and_fields_set(self):
        form = OrderForm(item_id=5)
        assert form.qty == 1
        assert form.tags == []
        assert form.meta == {}
        assert getattr(form, FIELDS_SET) == {"item_id"}

    def test_mutable_defaults_copied_per_instance(self):
        first, second = OrderForm(item_id=1), OrderForm(item_id=2)
        first.tags.append("x")
        first.meta["k"] = 1
        assert second.tags == []
        assert second.meta == {}
        loaded = OrderForm.__converter__.from_json({"item_id": 3})
        assert loaded.tags == []
        assert loaded.tags is not first.tags

    def test_immutable_default_shared(self):
        shared = Decimal("1.5")

        class Price(Model):
            value: Decimal = shared

        assert Price().value is shared
        assert Price.__converter__.from_json({}).value is shared

    def test_dataclass_default_factory(self):
        assert Tree().kids == []
        assert model_converter(Tree).from_json({}).kids == []

    def test_exclude_unset(self):
        converter = OrderForm.__converter__
        assert converter.dump(OrderForm(item_id=5, qty=1), exclude_unset=True) == {
            "item_id": 5,
            "qty": 1,
        }
        loaded = converter.from_json({"item_id": 5, "tags": ["a"]})
        assert converter.dump(loaded, exclude_unset=True) == {"item_id": 5, "tags": ["a"]}
        assert len(converter.dump(loaded)) == len(converter.fields)

    def test_init_missing_argument(self):
        with pytest.raises(TypeError, match="missing required argument 'item_id'"):
            OrderForm()

    def test_init_unexpected_argument(self):
        with pytest.raises(TypeError, match=r"unexpected arguments \['nope'\]"):
            OrderForm(item_id=1, nope=2)


class TestRecursion:
    def test_self_reference(self):
        node = Node.__converter__.from_json({"value": 1, "children": [{"value": 2}]})
        assert node.children[0].value == 2
        assert node.children[0].children == []

    def test_mutual_forward_reference(self):
        forward = Forward.__converter__.from_json({"later": {"back": {}}})
        assert isinstance(forward.later.back, Forward)
        assert Forward.__converter__.dump(forward) == {"later": {"back": {"later": None}}}

    def test_recursive_dataclass(self):
        tree = model_converter(Tree).from_json({"kids": [{"kids": [{}]}]})
        assert tree == Tree([Tree([Tree()])])

    @pytest.mark.skipif(sys.version_info < (3, 14), reason="deferred annotations (PEP 649)")
    def test_unquoted_self_reference(self):
        # No `from __future__ import annotations`: the class name is unbound while
        # __init_subclass__ runs, which the default annotation format rejects.
        module = types.ModuleType("_converters_pep649")
        module.__dict__["Model"] = Model
        sys.modules[module.__name__] = module
        try:
            exec(  # noqa: S102
                "class Leaf(Model):\n    child: Leaf | None = None\n", module.__dict__
            )
            leaf = module.Leaf.__converter__.from_json({"child": {"child": None}})
        finally:
            del sys.modules[module.__name__]
        assert isinstance(leaf.child, module.Leaf)


class Celsius:
    def __init__(self, degrees: float) -> None:
        self.degrees = degrees


class CelsiusConverter(Converter):
    def to_json(self, value):
        return value.degrees

    def from_json(self, value):
        return Celsius(value)


class TestExtensionHook:
    def test_register_converter(self, monkeypatch):
        monkeypatch.setattr(_converters, "_extra", {})
        register_converter(Celsius, CelsiusConverter())
        register_converter(int, converter_for(str))  # checked before the built-ins

        class Weather(Model):
            temp: Celsius
            code: int

        weather = Weather.__converter__.from_json({"temp": 21.5, "code": "x"})
        assert weather.temp.degrees == 21.5
        assert weather.code == "x"
        with pytest.raises(TypeError, match="no flat-string form"):
            converter_for(Celsius).to_str(weather.temp)


class FlatAll(Model):
    text: str
    number: int
    ratio: float
    flag: bool
    kind: Kind
    level: Level
    color: Color
    choice: Literal["a", 1]
    maybe: int | None
    ref: UUID
    price: Decimal
    part: Fraction


FLAT_ALL = FlatAll(
    text="x",
    number=-5,
    ratio=0.25,
    flag=True,
    kind=Kind.B,
    level=Level.HIGH,
    color=Color.RED,
    choice=1,
    maybe=None,
    ref=UID,
    price=Decimal("1.10"),
    part=Fraction(1, 3),
)
FLAT_ALL_PARTS = ["x", "-5", "0.25", "1", "b", "2", "red", "1", "", UID.hex, "1.10", "1/3"]


class TestFlatCodec:
    def test_rust_schema_in_use(self):
        FlatAll.__converter__.to_flat(FLAT_ALL)
        assert "_schema" in vars(FlatAll.__converter__)

    def test_to_flat(self):
        assert FlatAll.__converter__.to_flat(FLAT_ALL) == FLAT_ALL_PARTS

    @pytest.mark.parametrize("parts", [FLAT_ALL_PARTS, tuple(FLAT_ALL_PARTS)])
    def test_from_flat(self, parts):
        loaded = FlatAll.__converter__.from_flat(parts)
        assert FlatAll.__converter__.dump(loaded) == FlatAll.__converter__.dump(FLAT_ALL)
        assert getattr(loaded, FIELDS_SET) == {f.name for f in FlatAll.__converter__.fields}
        assert type(loaded.flag) is bool
        assert loaded.kind is Kind.B

    @pytest.mark.parametrize(
        ("index", "text", "value"),
        [
            (1, " 7 ", 7),
            (1, "1_000", 1000),
            (2, "inf", math.inf),
            (3, "true", True),
            (3, "Off", False),
        ],
    )
    def test_from_flat_lax_text(self, index, text, value):
        parts = list(FLAT_ALL_PARTS)
        parts[index] = text
        loaded = FlatAll.__converter__.from_flat(parts)
        assert getattr(loaded, FlatAll.__converter__.fields[index].name) == value

    @pytest.mark.parametrize(
        ("index", "text", "path"),
        [
            (1, "x", "number"),
            (3, "maybe", "flag"),
            (4, "c", "kind"),
            (7, "b", "choice"),
            (9, "zz", "ref"),
        ],
    )
    def test_from_flat_errors(self, index, text, path):
        parts = list(FLAT_ALL_PARTS)
        parts[index] = text
        with pytest.raises(ConversionError) as exc_info:
            FlatAll.__converter__.from_flat(parts)
        assert exc_info.value.path == path
        assert exc_info.value.value == text

    def test_from_flat_part_count(self):
        with pytest.raises(ConversionError, match="expected 12 parts"):
            FlatAll.__converter__.from_flat(FLAT_ALL_PARTS[:-1])

    def test_from_flat_needs_flat_fields(self):
        with pytest.raises(TypeError, match="no flat-string form"):
            Node.__converter__.from_flat(["1", ""])

    def test_to_flat_errors(self):
        with pytest.raises(ConversionError, match="FlatAll instance"):
            FlatAll.__converter__.to_flat(Flat(id=1, name="x", kind=Kind.A))
        values = {f.name: getattr(FLAT_ALL, f.name) for f in FlatAll.__converter__.fields}
        bad = FlatAll(**{**values, "number": "5"})
        with pytest.raises(ConversionError) as exc_info:
            FlatAll.__converter__.to_flat(bad)
        assert exc_info.value.path == "number"
        with pytest.raises(TypeError, match="no flat-string form"):
            Node.__converter__.to_flat(Node(value=1))


class TestLoadJson:
    DATA = {
        "item_id": 5,
        "address": {"city": "Kyiv", "zip": None},
        "tags": ["a"],
        "meta": {"k": 1},
        "point": {"x": 1},
        "created": NOW.isoformat(),
        "unknown": [{"deep": [1, 2.5, None, "x"]}],
    }

    @pytest.mark.parametrize(
        "encode", [lambda t: t.encode(), str, lambda t: bytearray(t.encode())]
    )
    def test_matches_from_json(self, encode):
        text = json.dumps(self.DATA)
        converter = OrderForm.__converter__
        loaded = converter.load_json(encode(text))
        assert converter.dump(loaded) == converter.dump(converter.from_json(self.DATA))
        assert getattr(loaded, FIELDS_SET) == set(self.DATA) - {"unknown"}
        assert getattr(loaded.address, FIELDS_SET) == {"city", "zip"}

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ('{"item_id": 5, "qty": 1, "qty": 3}', 3),  # last key wins, as in json.loads
            ('{"item_id": 5, "qty": 12345678901234567890123}', 12345678901234567890123),
            ('\ufeff{"item_id": 5}', 1),  # a BOM: json.loads(bytes) accepts it
        ],
    )
    def test_json_loads_semantics(self, text, expected):
        assert OrderForm.__converter__.load_json(text.encode()).qty == expected

    def test_nan_like_json_loads(self):
        loaded = FlatAll.__converter__.load_json(
            json.dumps({**FlatAll.__converter__.dump(FLAT_ALL), "ratio": math.nan})
        )
        assert math.isnan(loaded.ratio)

    def test_lone_surrogate_escape_is_invalid(self):
        # json.loads keeps an escaped lone surrogate; jiter rejects it (PD-35, F-08 Notes)
        with pytest.raises(ConversionError, match="invalid JSON"):
            Address.__converter__.load_json(rb'{"city": "\ud800"}')

    @pytest.mark.parametrize(
        ("text", "reason"),
        [
            (b'{"item_id": 5', "EOF while parsing an object at line 1 column 13"),
            (b'{"item_id": 5} []', "trailing characters at line 1 column 16"),
            (b"\xff", "expected value at line 1 column 1"),
            (b"", "EOF while parsing a value at line 1 column 0"),
        ],
    )
    def test_malformed(self, text, reason):
        with pytest.raises(ConversionError) as exc_info:
            OrderForm.__converter__.load_json(text)
        assert exc_info.value.reason == f"invalid JSON: {reason}"

    def test_not_text(self):
        with pytest.raises(TypeError, match="must be str, bytes or bytearray, not int"):
            OrderForm.__converter__.load_json(5)

    def test_error_path(self):
        with pytest.raises(ConversionError) as exc_info:
            OrderForm.__converter__.load_json(b'{"item_id": 5, "tags": ["a", 2]}')
        assert exc_info.value.path == "tags[1]"
        assert exc_info.value.value == 2


class Cat(Model):
    kind: Literal["cat"]
    lives: int = 9


class Dog(Model):
    kind: Literal["dog", "puppy"]
    good: bool = True


class Pets(Model):
    first: Cat | Dog
    tagged: Annotated[Cat | Dog | None, Discriminator("kind")] = None
    later: Annotated[Bird | Cat, Discriminator("kind")] | None = None


class Bird(Model):  # defined after Pets: its tag table is built on first use
    kind: Literal["bird"]


class Branch(TypedDict):
    name: str
    children: NotRequired[list[Branch]]


class Holder(Model):
    pairs: set[Pair]
    tree: Branch
    scaled: Annotated[int, TimesTen()] = 0


class Shout(Converter):
    flat = True

    def to_json(self, value):
        return value.upper()

    def from_json(self, value):
        return value.lower()

    def to_str(self, value):
        return value.upper()

    def from_str(self, value):
        return value.lower()


class Loud(Model):
    word: Annotated[str, Shout()]
    count: int = 0


class TestMoreKinds:
    def test_union_without_discriminator_is_left_to_right_for_models(self):
        pets = Pets.__converter__.from_json({"first": {"kind": "cat", "lives": 3}})
        assert isinstance(pets.first, Cat)
        with pytest.raises(ConversionError) as exc_info:
            Pets.__converter__.from_json({"first": {"kind": "fish"}})
        assert exc_info.value.path == "first"
        assert "Cat | " in exc_info.value.reason

    def test_union_dump_picks_member_by_type(self):
        pets = Pets(first=Dog(kind="puppy"), tagged=Cat(kind="cat"))
        assert Pets.__converter__.dump(pets) == {
            "first": {"kind": "puppy", "good": True},
            "tagged": {"kind": "cat", "lives": 9},
            "later": None,
        }

    @pytest.mark.parametrize(("tag", "cls"), [("cat", Cat), ("dog", Dog), ("puppy", Dog)])
    def test_discriminator(self, tag, cls):
        pets = Pets.__converter__.from_json({"first": {"kind": "cat"}, "tagged": {"kind": tag}})
        assert type(pets.tagged) is cls

    @pytest.mark.parametrize(
        ("tagged", "path", "value"),
        [
            ({"lives": 1}, "tagged.kind", _converters.MISSING),
            ({"kind": "fish"}, "tagged.kind", "fish"),
            ({"kind": ["cat"]}, "tagged.kind", ["cat"]),
            ({"kind": "cat", "lives": "x"}, "tagged.lives", "x"),
            ("cat", "tagged", "cat"),
        ],
    )
    def test_discriminator_errors(self, tagged, path, value):
        with pytest.raises(ConversionError) as exc_info:
            Pets.__converter__.from_json({"first": {"kind": "cat"}, "tagged": tagged})
        assert exc_info.value.path == path
        assert exc_info.value.value == value

    def test_discriminator_over_typeddicts(self):
        class FishDict(TypedDict):
            kind: Literal["fish"]
            fins: int

        converter = converter_for(Annotated[FishDict | Cat, Discriminator("kind")])
        assert converter.from_json({"kind": "fish", "fins": 2, "x": 0}) == {
            "kind": "fish",
            "fins": 2,
        }
        assert type(converter.from_json({"kind": "cat"})) is Cat

    def test_discriminator_with_a_later_member(self):
        pets = Pets.__converter__.from_json({"first": {"kind": "cat"}, "later": {"kind": "bird"}})
        assert type(pets.later) is Bird

    def test_discriminator_needs_literal_tags(self):
        with pytest.raises(TypeError, match="needs a Literal 'kind' field"):

            class Bad(Model):
                pet: Annotated[Cat | Address, Discriminator("kind")]

        with pytest.raises(TypeError, match="needs a Literal 'kind' field"):
            converter_for(Annotated[Cat | int, Discriminator("kind")])

    def test_typeddict(self):
        holder = Holder.__converter__.from_json(
            {
                "pairs": [{"x": 1}, {"x": 1}, {"x": 2, "label": "b"}],
                "tree": {"name": "a", "children": [{"name": "b", "extra": 1}]},
                "scaled": 70,
            }
        )
        assert holder.pairs == {Pair(1), Pair(2, "b")}
        assert holder.tree == {"name": "a", "children": [{"name": "b"}]}
        assert type(holder.tree) is dict
        assert holder.scaled == 7
        dumped = Holder.__converter__.dump(holder)
        assert dumped["tree"] == {"name": "a", "children": [{"name": "b"}]}
        assert dumped["scaled"] == 70

    def test_typeddict_error_path(self):
        with pytest.raises(ConversionError) as exc_info:
            Holder.__converter__.from_json(
                {"pairs": [], "tree": {"name": "a", "children": [{"name": 1}]}}
            )
        assert exc_info.value.path == "tree.children[0].name"

    def test_typeddict_bad_key_at_class_creation(self):
        class BadDict(TypedDict):
            value: complex

        with pytest.raises(TypeError, match=r"BadDict\.value: unsupported annotation"):
            converter_for(BadDict)
        assert BadDict not in _converters._typeddicts

    def test_untyped_namedtuple_rejected(self):
        with pytest.raises(TypeError, match="unsupported annotation"):
            converter_for(namedtuple("Plain", ["a"]))  # noqa: PYI024

    def test_per_field_converter_wins_over_register_converter(self, monkeypatch):
        monkeypatch.setattr(_converters, "_extra", {int: converter_for(str)})
        assert converter_for(Annotated[int, TimesTen()]).from_json(40) == 4

    def test_per_field_flat_converter(self):
        loud = Loud.__converter__.from_flat(["HEY", "2"])
        assert loud.word == "hey"
        assert Loud.__converter__.to_flat(loud) == ["HEY", "2"]
        assert Loud.__converter__.load_json(b'{"word": "HO"}').word == "ho"

    def test_new_kinds_have_no_flat_form(self):
        for tp in (set[int], int | str, Pair, Movie, Cat | Dog):
            assert not converter_for(tp).flat, tp

    @pytest.mark.parametrize(
        ("tp", "value", "expected"),
        [
            (int | str, True, _converters.ConversionError),
            (float | int, 1, int),
            (int | float, 1.0, float),
            (str | UUID, str(UID), str),
            (UUID | str, str(UID), UUID),
            (Literal["x"] | int, "x", str),
            (list[int] | dict[str, int], {"a": 1}, dict),
            (Pair | int, {"x": 1}, Pair),
            (Annotated[int, TimesTen()] | str, 50, int),
            (Movie | int, {"title": "t"}, dict),
            (Kind | Literal[5], 5, int),
            (Point | Address, {"city": "c"}, Address),
        ],
    )
    def test_smart_union_from_json(self, tp, value, expected):
        converter = converter_for(tp)
        if expected is _converters.ConversionError:
            with pytest.raises(ConversionError, match="expected"):
                converter.from_json(value)
        else:
            assert type(converter.from_json(value)) is expected

    @pytest.mark.parametrize(
        ("tp", "value", "expected"),
        [
            (int | str, Level.HIGH, 2),
            (UUID | str, UID, str(UID)),
            (Decimal | float, Decimal("1.5"), "1.5"),
            (Pair | Point, Point(3), {"x": 3, "y": 0}),
            (Kind | int, Kind.A, "a"),
            (Literal["x"] | int, "x", "x"),
            (set[int] | int, {1}, [1]),
            (dict[str, int] | int, {"a": 1}, {"a": 1}),
            (Annotated[int, TimesTen()] | str, 5, 50),
        ],
    )
    def test_smart_union_to_json(self, tp, value, expected):
        assert converter_for(tp).to_json(value) == expected


class Leaf(Model):
    kind: Literal["leaf"]


class Trunk(Model):
    kind: Literal["trunk"]
    children: list[Annotated[Leaf | Trunk, Discriminator("kind")]] = []  # noqa: RUF012


class Total(TypedDict):
    always: int
    maybe: Annotated[NotRequired[int], "meta"]


class Partial(TypedDict, total=False):
    sometimes: int
    must: Annotated[Required[int], "meta"]


class Upper(_converters._Str):
    """A subclass of a built-in converter that changes it: Rust must not use the native kind."""

    def from_json(self, value):
        return value.upper()


class Shouty(Model):
    word: Annotated[str, Upper()]


class Guarded(Model):
    x: int

    def __setattr__(self, name, value):
        msg = "frozen"
        raise AttributeError(msg)


@dataclasses.dataclass
class Counted:
    calls: ClassVar[list[int]] = []
    x: int

    def __post_init__(self) -> None:
        Counted.calls.append(self.x)
        msg = "never valid"
        raise ValueError(msg)


class HasCounted(Model):
    inner: Counted


class Interrupting(Converter):
    calls: ClassVar[int] = 0

    def from_json(self, value):
        Interrupting.calls += 1
        raise KeyboardInterrupt


class Interrupted(Model):
    value: Annotated[int, Interrupting()]


class Doc(TypedDict):
    kind: Literal["doc"]
    items: list[Annotated[Doc | LeafDict, Discriminator("kind")]]


class LeafDict(TypedDict):
    kind: Literal["leaf"]


class TestReviewFindings:
    def test_recursive_discriminated_typeddict(self):
        doc = converter_for(Doc).from_json(
            {"kind": "doc", "items": [{"kind": "leaf"}, {"kind": "doc", "items": []}]}
        )
        assert doc == {"kind": "doc", "items": [{"kind": "leaf"}, {"kind": "doc", "items": []}]}

    @pytest.mark.parametrize("value", [True, 2.0])
    def test_enum_matches_type_and_value(self, value):
        with pytest.raises(ConversionError, match="expected a Level value"):
            converter_for(Level).from_json(value)
        assert converter_for(Level).from_json(2) is Level.HIGH

    def test_flag_enums_rejected(self):
        class Permission(IntFlag):
            READ = 1
            WRITE = 2

        with pytest.raises(TypeError, match="Flag enum"):
            converter_for(Permission)

    @pytest.mark.parametrize(
        "tp", [set[list[int] | None], set[int | list[int]], set[Point], set[tuple[list[int], ...]]]
    )
    def test_unhashable_set_items_rejected_at_class_creation(self, tp):
        with pytest.raises(TypeError, match="unhashable set item"):
            converter_for(tp)

    def test_tolerant_enum_missing_hook(self):
        class Status(StrEnum):
            ACTIVE = "active"
            UNKNOWN = "unknown"

            @classmethod
            def _missing_(cls, value):
                return cls.UNKNOWN if isinstance(value, str) else None

        converter = converter_for(Status)
        assert converter.from_json("new-telegram-value") is Status.UNKNOWN
        with pytest.raises(ConversionError, match="expected a Status value"):
            converter.from_json(1)

    def test_hand_written_hash_set_items(self):
        @dataclasses.dataclass(frozen=True)
        class Keyed:
            key: int
            tags: list[str] = dataclasses.field(default_factory=list)

            def __hash__(self):
                return hash(self.key)

        assert converter_for(set[Keyed]).from_json([{"key": 1, "tags": ["a"]}]) == {
            Keyed(1, ["a"])
        }

    def test_load_json_text_subclasses(self):
        class Raw(bytes):
            pass

        class Text(str):
            pass

        assert Address.__converter__.load_json(Raw(b'{"city": "a"}')).city == "a"
        assert Address.__converter__.load_json(Text('{"city": "b"}')).city == "b"
        assert Address.__converter__.load_json('{"city": "\ud800"}').city == "\ud800"

    def test_used_converters_are_collected(self):
        refs = []
        for _ in range(20):
            converter = converter_for(list[int])
            assert converter.from_json([1]) == [1]  # compiles and caches its KindCore
            refs.append(weakref.ref(converter))
        del converter
        gc.collect()
        assert all(ref() is None for ref in refs)

    def test_frozen_dataclass_with_unhashable_field_rejected_in_set(self):
        @dataclasses.dataclass(frozen=True)
        class Tagged:
            tags: list[str]
            name: str = ""

        @dataclasses.dataclass(frozen=True)
        class Labelled:
            name: str
            tags: list[str] = dataclasses.field(default_factory=list, hash=False, compare=False)

        with pytest.raises(TypeError, match="unhashable set item"):
            converter_for(set[Tagged])
        assert converter_for(set[Labelled]).from_json([{"name": "a"}]) == {Labelled("a")}

    def test_duplicate_json_keys_last_wins_before_validation(self):
        converter = OrderForm.__converter__
        assert converter.load_json(b'{"item_id": "bad", "item_id": 2}').item_id == 2
        assert converter.load_json(b'{"item_id": 1, "meta": {"k": "x", "k": 3}}').meta == {"k": 3}
        holder = Holder.__converter__.load_json(b'{"pairs": [], "tree": {"name": 1, "name": "a"}}')
        assert holder.tree == {"name": "a"}
        with pytest.raises(ConversionError) as exc_info:
            converter.load_json(b'{"tags": [1], "item_id": "x"}')
        assert exc_info.value.path == "item_id"  # field order, as from_json reports it

    def test_hashable_set_items(self):
        assert converter_for(frozenset[Pair]).from_json([{"x": 1}]) == frozenset({Pair(1)})
        assert converter_for(set[Kind | None]).from_json(["a", None]) == {Kind.A, None}

    def test_float_overflow_is_a_conversion_error(self):
        with pytest.raises(ConversionError, match="expected a number"):
            converter_for(float).from_json(10**1000)
        with pytest.raises(ConversionError) as exc_info:
            FlatAll.__converter__.load_json(
                json.dumps({**FlatAll.__converter__.dump(FLAT_ALL), "ratio": 10**1000})
            )
        assert exc_info.value.path == "ratio"

    def test_big_integers_from_json(self):
        assert (
            OrderForm.__converter__.load_json(
                b'{"item_id": 123456789012345678901234567890}'
            ).item_id
            == 123456789012345678901234567890
        )

    def test_subclassed_builtin_converter_is_honoured(self):
        assert Shouty.__converter__.from_json({"word": "abc"}).word == "ABC"
        assert Shouty.__converter__.load_json(b'{"word": "abc"}').word == "ABC"

    def test_model_refusing_setattr_loads(self):
        guarded = Guarded.__converter__.from_json({"x": 1})
        assert guarded.x == 1
        assert getattr(guarded, FIELDS_SET) == {"x"}

    @pytest.mark.parametrize("load", ["from_json", "load_json"])
    def test_user_code_runs_once_or_twice_on_error(self, monkeypatch, load):
        monkeypatch.setattr(Counted, "calls", [])
        data = {"inner": {"x": 1}}
        with pytest.raises(ConversionError, match="never valid") as exc_info:
            if load == "from_json":
                HasCounted.__converter__.from_json(data)
            else:
                HasCounted.__converter__.load_json(json.dumps(data))
        # load_json: the one-pass walk, then the from_json path for the exact error (F-08 Notes)
        assert Counted.calls == ([1] if load == "from_json" else [1, 1])
        assert exc_info.value.path == "inner"
        assert isinstance(exc_info.value.__cause__, ValueError)

    def test_keyboard_interrupt_is_not_retried(self, monkeypatch):
        monkeypatch.setattr(Interrupting, "calls", 0)
        with pytest.raises(KeyboardInterrupt):
            Interrupted.__converter__.from_json({"value": 1})
        assert Interrupting.calls == 1

    def test_deep_nesting_raises_recursion_error_not_a_crash(self):
        depth = 100_000
        text = '{"value": 0, "children": [' * depth + "]}" * depth
        with pytest.raises(RecursionError):
            Node.__converter__.load_json(text.encode())

    def test_cyclic_dict_raises_recursion_error(self):
        data: dict[str, Any] = {"value": 0}
        data["children"] = [data]
        with pytest.raises(RecursionError):
            Node.__converter__.from_json(data)

    def test_moderate_nesting_loads(self):
        depth = 60
        text = '{"value": 0, "children": [' * depth + '{"value": 1}' + "]}" * depth
        node = Node.__converter__.load_json(text.encode())
        for _ in range(depth):
            node = node.children[0]
        assert node.value == 1

    def test_recursive_discriminated_union(self):
        trunk = Trunk.__converter__.from_json(
            {"kind": "trunk", "children": [{"kind": "leaf"}, {"kind": "trunk", "children": []}]}
        )
        assert [type(child) for child in trunk.children] == [Leaf, Trunk]

    def test_duplicate_discriminator_tag_rejected(self):
        class Kitten(Model):
            kind: Literal["cat"]

        with pytest.raises(TypeError, match="tag 'cat' is used by more than one member"):
            converter_for(Annotated[Cat | Kitten, Discriminator("kind")])

    def test_typeddict_required_inside_annotated(self):
        total, partial = converter_for(Total), converter_for(Partial)
        assert total.from_json({"always": 1}) == {"always": 1}
        assert partial.from_json({"must": 1}) == {"must": 1}
        with pytest.raises(ConversionError, match="must: field required"):
            partial.from_json({"sometimes": 1})


class TestCoreImport:
    def test_core_is_imported_once(self, monkeypatch):
        monkeypatch.setattr(_converters, "_CORE", None)
        core = _converters._rust()
        assert core is sys.modules["aiogram._core"]
        assert _converters._rust() is core

    @pytest.mark.parametrize("first", ["load_json", "dump", "to_json", "from_flat", "to_flat"])
    def test_any_method_compiles_the_schema(self, first):
        class Fresh(Model):
            value: int = 1

        converter = Fresh.__converter__
        assert "_schema" not in vars(converter)
        calls = {
            "load_json": lambda: converter.load_json(b'{"value": 2}').value,
            "dump": lambda: converter.dump(Fresh(value=2)),
            "to_json": lambda: converter.to_json(Fresh(value=2)),
            "from_flat": lambda: converter.from_flat(["2"]).value,
            "to_flat": lambda: converter.to_flat(Fresh(value=2)),
        }
        assert calls[first]() in (2, {"value": 2}, ["2"])
        assert "_schema" in vars(converter)

    def test_without_core_the_first_use_fails(self, monkeypatch):
        monkeypatch.setattr(_converters, "_CORE", None)
        monkeypatch.setitem(sys.modules, "aiogram._core", None)
        with pytest.raises(ImportError):
            converter_for(list[int]).from_json([1])


def test_no_heavy_imports():
    """The module imports only the standard library (checked with ``-X importtime``)."""
    path = Path(_converters.__file__)
    code = textwrap.dedent(f"""
        import importlib.util, sys
        spec = importlib.util.spec_from_file_location("_converters", {str(path)!r})
        module = sys.modules["_converters"] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    """)
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-X", "importtime", "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    imported = {line.rsplit("|", 1)[-1].strip() for line in result.stderr.splitlines()}
    assert "dataclasses" in imported  # the check sees the module's imports
    for name in imported:
        assert name.split(".")[0] not in {"pydantic", "pydantic_core", "attrs", "msgspec"}
        assert not name.startswith(("aiogram", "_core"))
