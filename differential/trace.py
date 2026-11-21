"""Canonical trace records shared by the runner and every side script.

Stdlib only: side scripts run with ``python -I`` in a venv that holds aiogram and nothing
from this repository, and load this one file by path (``--trace-module``).
``tests/test_differential_framework.py`` checks that it imports only the standard library.

A trace is JSONL. Line 1 is ``{"__header__": {...}}`` (provenance: side spec, adapter, aiogram
version, commit, python, platform, kind, poison); every later line is one record::

    {"case": "update.text.small", "probe": "dump", "ok": true, "value": ..., "meta": {...}}
    {"case": "c", "probe": "p", "ok": false, "error": {"type": "T", "attrs": {...}}, "meta": {}}

Values are made JSON-native by :func:`canonical`; anything JSON cannot hold exactly carries a
``__kind__`` tag.
"""

from __future__ import annotations

import base64
import datetime
import decimal
import enum
import json
import math
from pathlib import Path
from typing import Any

HEADER_KEY = "__header__"
KIND_KEY = "__kind__"


def _qualname(tp: type) -> str:
    return f"{tp.__module__}.{tp.__qualname__}"


def dumps(obj: Any) -> str:
    """The one canonical serialisation: sorted keys, no whitespace, no NaN."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def canonical(value: Any) -> Any:  # noqa: C901, PLR0911 - one branch per tagged kind
    """Convert ``value`` to a JSON-native tree with a stable, lossless-enough shape."""
    # Enum first: StrEnum / IntEnum members are also str / int
    if isinstance(value, enum.Enum):
        return {KIND_KEY: "enum", "type": _qualname(type(value)), "value": canonical(value.value)}
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value  # json writes repr(), which round-trips
        return {KIND_KEY: "float", "repr": repr(value)}
    if isinstance(value, (bytes, bytearray, memoryview)):
        return {KIND_KEY: "bytes", "b64": base64.b64encode(bytes(value)).decode("ascii")}
    if isinstance(value, datetime.datetime):
        return {KIND_KEY: "datetime", "iso": value.isoformat()}
    if isinstance(value, datetime.date):
        return {KIND_KEY: "date", "iso": value.isoformat()}
    if isinstance(value, datetime.time):
        return {KIND_KEY: "time", "iso": value.isoformat()}
    if isinstance(value, datetime.timedelta):
        return {
            KIND_KEY: "timedelta",
            "days": value.days,
            "seconds": value.seconds,
            "microseconds": value.microseconds,
        }
    if isinstance(value, decimal.Decimal):
        return {KIND_KEY: "decimal", "str": str(value)}
    if isinstance(value, dict):
        if all(isinstance(key, str) for key in value) and KIND_KEY not in value:
            return {key: canonical(item) for key, item in value.items()}
        items = [[canonical(key), canonical(item)] for key, item in value.items()]
        return {KIND_KEY: "dict", "items": sorted(items, key=dumps)}
    if isinstance(value, list):
        return [canonical(item) for item in value]
    if isinstance(value, tuple):
        return {KIND_KEY: "tuple", "items": [canonical(item) for item in value]}
    if isinstance(value, (set, frozenset)):
        return {KIND_KEY: "set", "items": sorted((canonical(item) for item in value), key=dumps)}
    return {KIND_KEY: "repr", "type": _qualname(type(value)), "repr": repr(value)}


def ok(case: str, probe: str, value: Any, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "case": case,
        "probe": probe,
        "ok": True,
        "value": canonical(value),
        "meta": canonical(meta or {}),
    }


def error(
    case: str,
    probe: str,
    exc: BaseException,
    attrs: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """A failed probe. ``attrs`` defaults to the exception message; sides may pass narrower."""
    return {
        "case": case,
        "probe": probe,
        "ok": False,
        "error": {
            "type": type(exc).__name__,
            "attrs": canonical({"message": str(exc)} if attrs is None else attrs),
        },
        "meta": canonical(meta or {}),
    }


def write(path: str | Path, header: dict[str, Any], records: list[dict[str, Any]]) -> None:
    lines = [dumps({HEADER_KEY: canonical(header)})]
    lines.extend(dumps(record) for record in records)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def read(path: str | Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if not lines:
        msg = f"{path}: empty trace"
        raise ValueError(msg)
    first = json.loads(lines[0])
    if not isinstance(first, dict) or set(first) != {HEADER_KEY}:
        msg = f"{path}: line 1 is not a {HEADER_KEY} line"
        raise ValueError(msg)
    return first[HEADER_KEY], [json.loads(line) for line in lines[1:] if line]
