"""Write the 3.x signature tables used by the 4.0 codemod (D100, I-15, I-17, I-18).

Run it with the interpreter of the 3.x environment whose behaviour is recorded (PD-12): on
``dev-3.x`` that is the repository environment. Shortcut names come from
``.butcher/types/*/aliases.yml`` (top-level keys, no YAML dependency); everything else comes from
``inspect`` on the installed aiogram.
Usage: ``python scripts/butcher_signatures_3x.py --out <file>``.
"""

from __future__ import annotations

import argparse
import inspect
import json
import re
import types
import typing
from pathlib import Path

from aiogram import Bot, Router
from aiogram.methods import TelegramMethod
from aiogram.types import ErrorEvent, TelegramObject, Update

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "aiogram" / "_migration" / "data" / "signatures_3x.json"
# Only generated modules: ``aiogram.utils.web_app`` types exist only once something imports them.
_GENERATED = ("aiogram.types.", "aiogram.methods.")
_POSITIONAL = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)


def _positional(func: typing.Callable[..., object]) -> list[str]:
    params = inspect.signature(func).parameters.values()
    return [p.name for p in params if p.kind in _POSITIONAL and p.name != "self"]


def _subclasses(base: type) -> list[type]:
    found: dict[str, type] = {}
    stack = [base]
    while stack:
        for sub in stack.pop().__subclasses__():
            stack.append(sub)
            # pydantic's parametrized generics (``TelegramMethod[Message]``) are only bases
            if sub.__module__.startswith(_GENERATED) and "[" not in sub.__name__:
                found[sub.__name__] = sub
    return [found[name] for name in sorted(found)]


def _is_collection(annotation: object) -> bool:
    origin = typing.get_origin(annotation)
    if origin in (list, tuple):
        return True
    if origin in (typing.Union, types.UnionType):
        return any(_is_collection(arg) for arg in typing.get_args(annotation))
    return False


def _bot_methods() -> dict[str, list[str]]:
    return {
        f"Bot.{name}": _positional(func)
        for name, func in inspect.getmembers(Bot, inspect.isfunction)
        if not name.startswith("_")
    }


def _shortcuts() -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for path in sorted((ROOT / ".butcher" / "types").glob("*/aliases.yml")):
        receiver = path.parent.name
        cls = getattr(__import__("aiogram.types", fromlist=[receiver]), receiver)
        for name in re.findall(r"^([a-z_0-9]+):", path.read_text(encoding="utf-8"), re.M):
            out[f"{receiver}.{name}"] = {
                "receiver": receiver,
                "positional": _positional(getattr(cls, name)),
            }
    return out


def build() -> dict[str, object]:
    constructors = {f"{cls.__name__}": _positional(cls) for cls in _subclasses(TelegramMethod)}
    constructors.update({cls.__name__: _positional(cls) for cls in _subclasses(TelegramObject)})
    collections = {
        cls.__name__: sorted(
            n for n, f in cls.model_fields.items() if _is_collection(f.annotation)
        )
        for cls in _subclasses(TelegramObject)
    }
    update_types = {
        name: typing.get_args(f.annotation)[0].__name__
        for name, f in Update.model_fields.items()
        if typing.get_args(f.annotation)
    }
    observers = {
        name: ErrorEvent.__name__ if name == "error" else update_types[name]
        for name in Router().observers
    }
    return {
        "schema": 1,
        "methods": {**dict(sorted(_bot_methods().items())), **dict(sorted(constructors.items()))},
        "shortcuts": dict(sorted(_shortcuts().items())),
        "collection_fields": {k: v for k, v in collections.items() if v},
        "observers": observers,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    text = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
