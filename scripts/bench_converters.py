"""
F-08 micro-benchmark: load a 5-field flat class from a JSON-shaped dict.

Follows the A-05 method (warm-up, GC off, loops calibrated to >= 0.2 s, median of 7)
and prints the 3.x pydantic ``CallbackData.unpack`` for reference.

    uv run python scripts/bench_converters.py
"""

# ponytail: stand-in until the A-05 harness exists; move to benchmarks/cases/fsm.py then.
from __future__ import annotations

import gc
import statistics
import timeit
from collections.abc import Callable
from enum import Enum
from typing import Any

from aiogram.utils._converters import register_model


class Kind(Enum):
    A = "a"
    B = "b"


class Flat:
    id: int
    name: str
    kind: Kind
    page: int | None = None
    active: bool = False


DATA = {"id": 42, "name": "item", "kind": "a", "page": 3, "active": True}


def measure(fn: Callable[[], Any]) -> float:
    for _ in range(20):
        fn()
    timer = timeit.Timer(fn)
    number = 1
    while timer.timeit(number) < 0.2:  # noqa: PLR2004
        number *= 2
    gc.disable()
    try:
        samples = [timer.timeit(number) / number for _ in range(7)]
    finally:
        gc.enable()
    return statistics.median(samples) * 1e6


def main() -> None:
    load = register_model(Flat).from_json
    print(f"converters: from_json(5-field flat dict)  {measure(lambda: load(DATA)):.2f} us")

    from aiogram.filters.callback_data import CallbackData  # 3.x reference (pydantic)

    class FlatCallback(CallbackData, prefix="flat"):
        id: int
        name: str
        kind: Kind
        page: int | None = None
        active: bool = False

    packed = FlatCallback(**{**DATA, "kind": Kind.A}).pack()
    unpack = FlatCallback.unpack
    print(f"3.x pydantic: CallbackData.unpack         {measure(lambda: unpack(packed)):.2f} us")


if __name__ == "__main__":
    main()
