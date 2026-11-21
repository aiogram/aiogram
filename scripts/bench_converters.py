"""
F-08 micro-benchmarks: the converter core (Rust, PD-36) against pydantic v2.

Same cases as tasks/F-08 report-03 (a: callback unpack, b: flat dict, c/c': flat JSON,
d/d': 20 fields), A-05 method (warm-up, GC off, loops >= 0.2 s, median of 7).

    uv run python scripts/bench_converters.py
"""

# ponytail: stand-in until the A-05 harness exists; move to benchmarks/cases/fsm.py then.

from __future__ import annotations

import dataclasses
import gc
import json
import statistics
import sys
import timeit
from collections.abc import Callable
from datetime import UTC, datetime, timezone
from decimal import Decimal
from enum import Enum, IntEnum
from typing import Any
from uuid import UUID

from aiogram.utils import _converters
from aiogram.utils._converters import FIELDS_SET, ModelConverter, register_model

try:
    import pydantic
except ImportError:  # an environment without the 3.x stack
    pydantic = None


class Model:
    __converter__: ModelConverter

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.__converter__ = register_model(cls)


class Kind(Enum):
    A = "a"
    B = "b"


class Level(IntEnum):
    LOW = 1
    HIGH = 2


@dataclasses.dataclass
class Point:
    x: int
    y: int = 0


class Flat(Model):
    id: int
    name: str
    kind: Kind
    page: int | None = None
    active: bool = False


class FlatPoint(Model):
    id: int
    name: str
    kind: Kind
    page: int | None = None
    active: bool = False
    point: Point | None = None


class Address(Model):
    city: str
    street: str
    zip: str | None = None


class OrderNative(Model):  # ~20 fields, every type handled natively by the prototype
    item_id: int
    qty: int
    title: str
    note: str | None
    kind: Kind
    level: Level
    active: bool
    price: float
    rating: float | None
    address: Address
    points: list[Point]
    counters: dict[str, int]
    tags: list[str]
    parent_id: int | None
    flags: list[bool]
    comment: str
    page: int
    extra_kind: Kind | None
    weight: float
    seats: dict[str, int]


class Order(Model):  # same, with 3 fields that go through the Python fallback
    item_id: int
    qty: int
    title: str
    note: str | None
    kind: Kind
    level: Level
    active: bool
    price: float
    rating: float | None
    address: Address
    points: list[Point]
    counters: dict[str, int]
    tags: list[str]
    parent_id: int | None
    flags: list[bool]
    comment: str
    page: int
    created: datetime
    ref: UUID
    amount: Decimal


FLAT = {"id": 42, "name": "item", "kind": "a", "page": 3, "active": True}
FLAT_POINT = {**FLAT, "point": {"x": 1, "y": 2}}
ORDER_NATIVE = {
    "item_id": 5,
    "qty": 2,
    "title": "Pizza",
    "note": None,
    "kind": "b",
    "level": 2,
    "active": True,
    "price": 12.5,
    "rating": 4.8,
    "address": {"city": "Kyiv", "street": "Khreshchatyk 1", "zip": "01001"},
    "points": [{"x": 1, "y": 2}, {"x": 3, "y": 4}, {"x": 5}],
    "counters": {"a": 1, "b": 2, "c": 3, "d": 4},
    "tags": ["hot", "new", "veg"],
    "parent_id": None,
    "flags": [True, False, True],
    "comment": "ring twice",
    "page": 1,
    "extra_kind": None,
    "weight": 0.75,
    "seats": {"x": 1, "y": 2},
}
ORDER = {k: v for k, v in ORDER_NATIVE.items() if k not in {"extra_kind", "weight", "seats"}}
ORDER |= {
    "created": datetime(2026, 11, 21, 12, 0, tzinfo=UTC).isoformat(),
    "ref": "12345678-1234-5678-1234-567812345678",
    "amount": "19.99",
}


def measure(fn: Callable[[], Any]) -> tuple[float, float]:
    for _ in range(20):
        fn()
    timer = timeit.Timer(fn)
    number = 1
    while timer.timeit(number) < 0.2:  # noqa: PLR2004
        number *= 2
    gc.disable()
    try:
        samples = [timer.timeit(number) / number * 1e6 for _ in range(7)]
    finally:
        gc.enable()
    return statistics.median(samples), min(samples)


def same(cls: type, a: Any, b: Any) -> None:
    conv = cls.__converter__
    assert conv.dump(a) == conv.dump(b), (conv.dump(a), conv.dump(b))
    assert getattr(a, FIELDS_SET) == getattr(b, FIELDS_SET)


def pydantic_models() -> dict[str, Any]:
    if pydantic is None:
        return {}
    from pydantic import BaseModel

    class PFlat(BaseModel):
        id: int
        name: str
        kind: Kind
        page: int | None = None
        active: bool = False

    class PFlatPoint(PFlat):
        point: Point | None = None

    class PAddress(BaseModel):
        city: str
        street: str
        zip: str | None = None

    fields = {name: (hint, ...) for name, hint in Order.__annotations__.items()}
    ns = {
        "Kind": Kind,
        "Level": Level,
        "Point": Point,
        "Address": PAddress,
        "datetime": datetime,
        "UUID": UUID,
        "Decimal": Decimal,
    }
    resolved = {name: (eval(hint, ns), ...) for name, (hint, _) in fields.items()}  # noqa: S307
    POrder = pydantic.create_model("POrder", **resolved)
    native = {name: (eval(hint, ns), ...) for name, hint in OrderNative.__annotations__.items()}  # noqa: S307
    POrderNative = pydantic.create_model("POrderNative", **native)

    from aiogram.filters.callback_data import CallbackData

    class FlatCallback(CallbackData, prefix="flat"):
        id: int
        name: str
        kind: Kind
        page: int | None = None
        active: bool = False

    return {
        "flat": PFlat,
        "flat_point": PFlatPoint,
        "order": POrder,
        "order_native": POrderNative,
        "callback": FlatCallback,
    }


def main() -> None:  # noqa: C901
    p = pydantic_models()
    packed = "flat:42:item:a:3:1"

    def unpack(value: str) -> Any:
        prefix, *parts = value.split(":")
        assert prefix == "flat"
        return Flat.__converter__.from_flat(parts)

    cases: list[tuple[str, str, Callable[[], Any]]] = [
        ("a", "split + from_flat", lambda: unpack(packed))
    ]
    cases.append(("b", "from_json(dict)", lambda: Flat.__converter__.from_json(FLAT)))
    for case, cls, data in (
        ("c", Flat, FLAT),
        ("c'", FlatPoint, FLAT_POINT),
        ("d", OrderNative, ORDER_NATIVE),
        ("d'", Order, ORDER),
    ):
        raw = json.dumps(data).encode()
        conv = cls.__converter__
        cases.append((case, "load_json(bytes)", lambda conv=conv, raw=raw: conv.load_json(raw)))
        if case.startswith("d"):
            cases.append(
                (case, "from_json(dict)", lambda conv=conv, data=data: conv.from_json(data))
            )

    reference: dict[tuple[str, str], Callable[[], Any]] = {}
    if p:
        reference["a", "split + from_flat"] = lambda: p["callback"].unpack(packed)
        reference["b", "from_json(dict)"] = lambda: p["flat"].model_validate(FLAT)
        for case, key, data in (
            ("c", "flat", FLAT),
            ("c'", "flat_point", FLAT_POINT),
            ("d", "order_native", ORDER_NATIVE),
            ("d'", "order", ORDER),
        ):
            raw = json.dumps(data).encode()
            reference[case, "load_json(bytes)"] = lambda key=key, raw=raw: p[
                key
            ].model_validate_json(raw)
            if case.startswith("d"):
                reference[case, "from_json(dict)"] = lambda key=key, data=data: p[
                    key
                ].model_validate(data)

    print(f"{'case':<5}{'path':<20}{'rust':>10}{'pydantic':>10}  (median us)")  # noqa: T201
    for case, label, fn in cases:
        rust = measure(fn)[0]
        ref = reference.get((case, label))
        cell = "" if ref is None else f"{measure(ref)[0]:10.2f}"
        print(f"{case:<5}{label:<20}{rust:10.2f}{cell}")  # noqa: T201
    gil = getattr(sys, "_is_gil_enabled", lambda: True)()
    print(sys.implementation.name, sys.version.split()[0], "GIL" if gil else "no-GIL")  # noqa: T201


if __name__ == "__main__":
    main()
