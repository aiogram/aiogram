"""Differential tests: the Rust backend gives the Python backend's results and errors (PD-35)."""

from __future__ import annotations

import dataclasses
import json
import math
from collections import OrderedDict
from enum import Enum
from typing import Any

import pytest

from aiogram.utils import _converters
from aiogram.utils._converters import FIELDS_SET, ModelConverter
from tests.test_utils.test_converters import (
    FLAT_ALL,
    Holder,
    Loud,
    Pets,
    FLAT_ALL_PARTS,
    NOW,
    RUST_AVAILABLE,
    Address,
    Color,
    Flat,
    FlatAll,
    Kind,
    Level,
    Model,
    Node,
    OrderForm,
    Point,
)

pytestmark = pytest.mark.skipif(not RUST_AVAILABLE, reason="needs the Rust backend")


class Weird(Model):
    big: int
    ratio: float
    flag: bool | None = None
    kind: Kind | None = None
    level: Level | None = None
    pair: tuple[int, ...] = ()
    lookup: dict[str, float] = dataclasses.field(default_factory=dict)


class MyStr(str):
    pass


class MyList(list):  # type: ignore[type-arg]
    pass


class Mixed(Enum):
    ONE = 1
    TEXT = "1"


def snapshot(value: Any) -> Any:
    """A comparable picture of a result: exact types, nested instances, NaN made equal."""
    if isinstance(value, float) and math.isnan(value):
        return ("nan",)
    if hasattr(value, FIELDS_SET):
        fields = {k: snapshot(v) for k, v in vars(value).items() if k != FIELDS_SET}
        return (type(value), fields, getattr(value, FIELDS_SET))
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return (type(value), snapshot(dataclasses.asdict(value)))
    if isinstance(value, (list, tuple)):
        return (type(value), [snapshot(v) for v in value])
    if isinstance(value, dict):
        return (type(value), list(value), {k: snapshot(v) for k, v in value.items()})
    return (type(value), value)


def outcome(call: Any) -> Any:
    try:
        result = call()
    except Exception as e:  # noqa: BLE001
        return (
            "error",
            type(e),
            str(e),
            getattr(e, "path", None),
            snapshot(getattr(e, "value", None)),
        )
    return ("ok", snapshot(result))


def both(converter: ModelConverter, method: str, arg: Any) -> tuple[Any, Any]:
    _converters._use_backend(rust=False)
    try:
        python = outcome(lambda: getattr(converter, method)(arg))
    finally:
        _converters._use_backend(rust=True)
    assert "_schema" in vars(converter)
    rust = outcome(lambda: getattr(converter, method)(arg))
    return python, rust


ORDER = {
    "item_id": 5,
    "qty": 2,
    "address": {"city": "Kyiv", "zip": "01001"},
    "tags": ["a", "b"],
    "meta": {"k": 1},
    "point": {"x": 1, "y": 2},
    "created": NOW.isoformat(),
}

DICT_CASES = [
    (OrderForm, ORDER),
    (OrderForm, {"item_id": 5}),
    (OrderForm, {**ORDER, "extra": object()}),
    (OrderForm, OrderedDict(ORDER)),  # a Mapping, not a dict
    (OrderForm, {}),
    (OrderForm, []),
    (OrderForm, {**ORDER, "item_id": True}),
    (OrderForm, {**ORDER, "item_id": 2**70}),
    (OrderForm, {**ORDER, "item_id": Level.HIGH}),  # int subclass: Python coerces
    (OrderForm, {**ORDER, "item_id": 5.0}),
    (OrderForm, {**ORDER, "address": None}),
    (OrderForm, {**ORDER, "address": {"zip": "1"}}),
    (OrderForm, {**ORDER, "address": "Kyiv"}),
    (OrderForm, {**ORDER, "tags": ("a", "b")}),
    (OrderForm, {**ORDER, "tags": MyList(["a"])}),
    (OrderForm, {**ORDER, "tags": ["a", 1]}),
    (OrderForm, {**ORDER, "tags": [MyStr("a")]}),
    (OrderForm, {**ORDER, "meta": {"k": "v"}}),
    (OrderForm, {**ORDER, "meta": {1: 1}}),
    (OrderForm, {**ORDER, "meta": OrderedDict(k=1)}),
    (OrderForm, {**ORDER, "point": {"x": -1}}),  # __post_init__ ValueError
    (OrderForm, {**ORDER, "point": {"x": "1"}}),
    (OrderForm, {**ORDER, "created": "never"}),
    (Weird, {"big": 2**70, "ratio": 2**70}),
    (Weird, {"big": 1, "ratio": 3}),
    (Weird, {"big": 1, "ratio": True}),
    (Weird, {"big": 1, "ratio": math.nan, "flag": 1}),
    (Weird, {"big": 1, "ratio": 1.5, "kind": "a", "level": 2, "pair": [1, 2]}),
    (Weird, {"big": 1, "ratio": 1.5, "kind": ["a"]}),
    (Weird, {"big": 1, "ratio": 1.5, "level": True}),
    (Weird, {"big": 1, "ratio": 1.5, "level": 2.0}),
    (Weird, {"big": 1, "ratio": 1.5, "lookup": {"a": 1, "b": 2.5}}),
    (Weird, {"big": 1, "ratio": 1.5, "lookup": {"a": "x"}}),
    (Node, {"value": 1, "children": [{"value": 2, "children": [{"value": 3}]}]}),
    (Node, {"value": 1, "children": [{"value": 2, "children": [{"value": "x"}]}]}),
    (FlatAll, FlatAll.__converter__.dump(FLAT_ALL)),
    (FlatAll, {**FlatAll.__converter__.dump(FLAT_ALL), "choice": True}),
    (FlatAll, {**FlatAll.__converter__.dump(FLAT_ALL), "choice": [1]}),
    (FlatAll, {**FlatAll.__converter__.dump(FLAT_ALL), "color": Color.RED}),
    # brief-05 kinds: set/frozenset, NamedTuple, TypedDict, unions, per-field converters
    (Holder, {"pairs": [{"x": 1}, {"x": 1}], "tree": {"name": "a"}, "scaled": 10}),
    (Holder, {"pairs": ({"x": 1},), "tree": {"name": "a", "children": [{"name": "b"}]}}),
    (Holder, {"pairs": [[1, "a"]], "tree": {"name": "a"}}),
    (Holder, {"pairs": [{"x": 1}], "tree": {"children": []}}),
    (Holder, {"pairs": {"x": 1}, "tree": {"name": "a"}}),
    (Pets, {"first": {"kind": "dog"}, "tagged": {"kind": "puppy", "good": False}}),
    (Pets, {"first": {"kind": "dog"}, "tagged": {"kind": "bird"}}),
    (Pets, {"first": {"kind": "dog"}, "later": {"kind": "bird"}}),
    (Pets, {"first": {"lives": 1}}),
    (Loud, {"word": "HEY", "count": 3}),
]

JSON_CASES = [
    (OrderForm, json.dumps(ORDER).encode()),
    (OrderForm, json.dumps(ORDER)),
    (OrderForm, b'{"item_id": 5, "item_id": 6, "qty": 1}'),
    (OrderForm, b' \n{"item_id": 5}\t'),
    (OrderForm, b'{"item_id": 5, "unknown": {"a": [1, {"b": null}], "c": NaN}}'),
    (OrderForm, b'{"item_id": 123456789012345678901234567890}'),
    (OrderForm, b'{"item_id": 5.0}'),
    (OrderForm, b'{"item_id": 1e2}'),
    (OrderForm, b'{"item_id": -0}'),
    (OrderForm, b'{"item_id": 5, "tags": ["\\u00e9", "\\ud83d\\ude00", "\\ud800"]}'),
    (OrderForm, b'{"item_id": 5, "address": {"city": "K", "zip": null, "zip": "1"}}'),
    (OrderForm, b'\xef\xbb\xbf{"item_id": 5}'),
    (OrderForm, b'{"item_id": 5'),
    (OrderForm, b'{"item_id": 5} x'),
    (OrderForm, b"[]"),
    (OrderForm, b"\xff"),
    (OrderForm, b'{"item_id": "5"}'),
    (OrderForm, b'{"item_id": 5, "point": {"x": -1}}'),
    (OrderForm, bytearray(b'{"item_id": 5}')),
    (OrderForm, "\ud800"),
    (Weird, b'{"big": 1, "ratio": 1}'),
    (Weird, b'{"big": 1, "ratio": 0.1, "lookup": {"a": 1e308, "b": -0.0, "c": 5e-324}}'),
    (Weird, b'{"big": 1, "ratio": 1e400}'),
    (Weird, b'{"big": 1, "ratio": Infinity}'),
    (Weird, b'{"big": 1, "ratio": 1.5, "kind": "b", "level": 1, "flag": false, "pair": [3]}'),
    (Weird, b'{"big": 1, "ratio": 1.5, "kind": 1, "level": "1"}'),
    (Weird, b'{"big": 1, "ratio": 1.5, "level": true}'),
    (Weird, b'{"big": 1, "ratio": 1.5, "kind": {"a": 1}}'),
    (Node, b'{"value": 1, "children": [{"value": 2, "children": [{"value": 3}]}]}'),
    (Node, b'{"value": 1, "children": [{"value": 2}, 3]}'),
    (FlatAll, json.dumps(FlatAll.__converter__.dump(FLAT_ALL)).encode()),
    (FlatAll, json.dumps({**FlatAll.__converter__.dump(FLAT_ALL), "choice": True}).encode()),
    (
        Holder,
        b'{"pairs": [{"x": 1}, {"x": 2}], "tree": {"name": "a", "children": [{"name": "b"}]}}',
    ),
    (Holder, b'{"pairs": [{"x": "1"}], "tree": {"name": "a"}}'),
    (Pets, b'{"first": {"kind": "cat", "lives": 2}, "tagged": {"kind": "dog"}}'),
    (Pets, b'{"first": {"kind": "cat"}, "tagged": {"kind": 1}}'),
    (Loud, b'{"word": "HO"}'),
]

FLAT_CASES = [
    (FlatAll, FLAT_ALL_PARTS),
    (FlatAll, tuple(FLAT_ALL_PARTS)),
    (FlatAll, FLAT_ALL_PARTS[:-1]),
    (FlatAll, "x:y"),
    (FlatAll, [MyStr(p) for p in FLAT_ALL_PARTS]),
    (FlatAll, [1, *FLAT_ALL_PARTS[1:]]),
    *[
        (FlatAll, [*FLAT_ALL_PARTS[:index], text, *FLAT_ALL_PARTS[index + 1 :]])
        for index, texts in {
            1: [" 7", "+7", "-0", "007", "1_0", "٣", "9" * 30, "", "x"],
            2: ["1", "-1.5e3", ".5", "5.", "inf", "-Infinity", "nan", "1_0.5", "1e", ""],
            3: ["1", "0", "true", "NO", "2", ""],
            4: ["a", "c", ""],
            5: ["1", "01", "3"],
            6: ["red", "RED"],
            7: ["a", "1", "b", ""],
            8: ["", "5", "x"],
            9: [str(FLAT_ALL.ref), "x"],
        }.items()
        for text in texts
    ],
    (Flat, ["1", "x", "a", "", "1"]),
    (Loud, ["HEY", "2"]),
    (Loud, ["HEY", "x"]),
    (Holder, ["1", "2", "3"]),
    (Node, ["1", ""]),
]

TO_FLAT_CASES = [
    (FlatAll, FLAT_ALL),
    (FlatAll, Flat(id=1, name="x", kind=Kind.A)),
    (Flat, Flat(id=1, name=MyStr("x"), kind=Kind.B, page=0, active=False)),
    (Flat, Flat(id=1, name="x", kind=Kind.B)),
    (Flat, Flat(id=-3, name="", kind=Kind.A, page=7, active=True)),
    (Flat, Flat(id=True, name="x", kind=Kind.A)),
    (Flat, Flat(id=Level.HIGH, name="x", kind=Kind.A)),
    (Flat, Flat(id=1, name=1, kind=Kind.A)),
    (Flat, Flat(id=1, name="x", kind="a")),
    (Flat, Flat(id=1, name="x", kind=Kind.A, page="1")),
    (Flat, Flat(id=1, name="x", kind=Kind.A, active=1)),
    (
        FlatAll,
        FlatAll(
            **{
                **{f.name: getattr(FLAT_ALL, f.name) for f in FlatAll.__converter__.fields},
                "ratio": 2,
            }
        ),
    ),
    (Node, Node(value=1)),
    (Loud, Loud(word="hey", count=2)),
    (Loud, Loud(word=1)),
]


def _ids(cases: list[tuple[Any, Any]]) -> list[str]:
    return [f"{cls.__name__}-{index}" for index, (cls, _) in enumerate(cases)]


@pytest.mark.parametrize(("cls", "value"), DICT_CASES, ids=_ids(DICT_CASES))
def test_from_json(cls, value):
    python, rust = both(cls.__converter__, "from_json", value)
    assert rust == python


@pytest.mark.parametrize(("cls", "data"), JSON_CASES, ids=_ids(JSON_CASES))
def test_load_json(cls, data):
    python, rust = both(cls.__converter__, "load_json", data)
    assert rust == python


@pytest.mark.parametrize(("cls", "parts"), FLAT_CASES, ids=_ids(FLAT_CASES))
def test_from_flat(cls, parts):
    python, rust = both(cls.__converter__, "from_flat", parts)
    assert rust == python


@pytest.mark.parametrize(("cls", "value"), TO_FLAT_CASES, ids=_ids(TO_FLAT_CASES))
def test_to_flat(cls, value):
    python, rust = both(cls.__converter__, "to_flat", value)
    assert rust == python


def test_mixed_enum_without_flat_form():
    class Holder(Model):
        mixed: Mixed

    for parts in (["1"], ["x"]):
        python, rust = both(Holder.__converter__, "from_flat", parts)
        assert rust == python
    python, rust = both(Holder.__converter__, "from_json", {"mixed": "1"})
    assert rust == python == ("ok", snapshot(Holder(mixed=Mixed.TEXT)))


def test_fallback_runs_python_converters_once_more():
    """On a fallback the input is re-run in Python, so a raising user converter sees it twice."""
    calls = []

    class Counting(_converters.Converter):
        def from_json(self, value):
            calls.append(value)
            if value == "bad":
                raise _converters.ConversionError("nope", value)
            return value

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(_converters, "_extra", {Address: Counting()})

        class Holder(Model):
            first: Address
            second: int

    Holder.__converter__.from_json({"first": "ok", "second": 1})
    assert calls == ["ok"]
    calls.clear()
    with pytest.raises(_converters.ConversionError):
        Holder.__converter__.from_json({"first": "bad", "second": 1})
    assert calls == ["bad", "bad"]
    assert Point  # imported for the dataclass cases above
