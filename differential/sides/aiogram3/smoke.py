"""Smoke side for aiogram 3.x: decode ``update.text.small`` and dump it.

Standalone: stdlib + aiogram only, run by the runner as ``python -I smoke.py --corpus DIR
--out FILE --trace-module trace.py --header JSON [--poison]``. It exists to test the framework
end to end; the real probes are A-08..A-10.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sys
import tomllib
from pathlib import Path
from types import ModuleType
from typing import Any

import aiogram
from aiogram.types import TelegramObject, Update

CASES = ("update.text.small",)


def load_module(path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location("differential_trace", path)
    if spec is None or spec.loader is None:
        msg = f"cannot load {path}"
        raise ImportError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def poison(obj: TelegramObject) -> None:
    """Flip one field of every decoded object: first int +1, else first str reversed."""
    for name in type(obj).model_fields:
        value = getattr(obj, name)
        if isinstance(value, bool) or value is None:
            continue
        if isinstance(value, int):
            obj.__dict__[name] = value + 1  # models are frozen; bypass on purpose
            break
        if isinstance(value, str):
            obj.__dict__[name] = value[::-1]
            break
    for name in type(obj).model_fields:
        value = getattr(obj, name)
        if isinstance(value, TelegramObject):
            poison(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--trace-module", required=True)
    parser.add_argument("--header", required=True)
    parser.add_argument("--poison", action="store_true")
    args = parser.parse_args()

    trace = load_module(args.trace_module)
    corpus = Path(args.corpus)
    manifest = tomllib.loads((corpus / "MANIFEST.toml").read_text(encoding="utf-8"))
    paths = {item["id"]: item.get("path") for item in manifest["input"]}

    records: list[dict[str, Any]] = []
    for case in CASES:
        raw = (corpus / paths[case]).read_bytes()
        try:
            update = Update.model_validate_json(raw)
        except Exception as exc:  # noqa: BLE001 - a failed decode is a recorded outcome
            records.append(trace.error(case, "decode", exc))
            continue
        if args.poison:
            poison(update)
        records.append(trace.ok(case, "decode", {"type": type(update).__name__}))
        records.append(trace.ok(case, "dump", update.model_dump(mode="json", exclude_unset=True)))

    header = json.loads(args.header)
    header.update(
        aiogram=aiogram.__version__,
        python=sys.version.split()[0],
        implementation=platform.python_implementation(),
        platform=sys.platform,
    )
    trace.write(args.out, header, records)


if __name__ == "__main__":
    main()
