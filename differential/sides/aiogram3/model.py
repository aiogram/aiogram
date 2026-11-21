"""Model side for aiogram 3.x (A-08): what 3.x models do on every corpus update, plus fixed cases.

Standalone: stdlib + aiogram only, run by the runner as ``python -I model.py --corpus DIR
--out FILE --trace-module trace.py --header JSON [--poison]``. Probe names are the contract a 4.0
adapter implements too; they are listed in ``differential/README.md`` (*Model kind*).

Cases:

- ``model.<input id>`` for every corpus input of kind ``update``: the decode, dump, access and
  value-semantics probes. When ``decode.json`` fails, every later probe of the case is recorded
  as a ``DecodeFailed`` error, so both sides always emit the same keys.
- ``model.construct.<type>``: constructor kwargs, aliases and ``Default(...)`` placeholders.
- ``model.mutate.<type>``: attribute assignment.
- ``model.codex11.<name>``: the model probes of ``v4/research/codex-review.md`` section 11.

The bots carry fabricated tokens and never send a request.
"""

from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import pickle
import platform
import re
import sys
import tomllib
from collections.abc import Callable
from functools import partial
from pathlib import Path
from types import ModuleType
from typing import Any

from pydantic import BaseModel, ValidationError

import aiogram
from aiogram import Bot
from aiogram.methods import SendMessage
from aiogram.types import (
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    TelegramObject,
    Update,
    User,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

ACCESS = Path(__file__).resolve().parents[2] / "manifests" / "model.access.toml"

BOT = Bot("42:A08-ORACLE")
SAME_TOKEN = Bot("42:A08-ORACLE")  # another Bot object with the same token
OTHER = Bot("43:A08-ORACLE")
BOTS = {id(BOT): "bot", id(SAME_TOKEN): "same_token", id(OTHER): "other"}

DATE = datetime.datetime(2026, 11, 18, tzinfo=datetime.UTC)
PATH_PART = re.compile(r"([A-Za-z_]\w*)|\[(-?\d+)\]")

Record = dict[str, Any]


class DecodeFailed(Exception):  # noqa: N818 - the recorded outcome, named as 4.0 sides will name it
    """Recorded for every probe of a case whose ``decode.json`` failed."""


def load_module(path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location("differential_trace", path)
    if spec is None or spec.loader is None:
        msg = f"cannot load {path}"
        raise ImportError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def error_attrs(exc: BaseException) -> dict[str, Any]:
    """Stable across dependency versions: no messages, no URLs, no inputs."""
    if isinstance(exc, ValidationError):
        errors = exc.errors(include_url=False, include_input=False, include_context=False)
        return {
            "error_count": exc.error_count(),
            "errors": [{"type": item["type"], "loc": list(item["loc"])} for item in errors],
        }
    return {}


def bot_name(obj: TelegramObject) -> str | None:
    return None if obj.bot is None else BOTS.get(id(obj.bot), "unknown")


def resolve(obj: Any, path: str) -> Any:
    """Follow ``a.b[0].c`` with plain attribute and index access, as user code does."""
    for name, index in PATH_PART.findall(path):
        obj = getattr(obj, name) if name else obj[int(index)]
    return obj


def walk_extras(obj: Any, path: str, out: dict[str, Any]) -> None:
    """``model_extra`` of the root (always) and of every nested object that has extras."""
    if isinstance(obj, TelegramObject):
        if obj.model_extra or not path:
            out[path or "$"] = obj.model_extra
        for name in type(obj).model_fields:
            walk_extras(getattr(obj, name), f"{path}.{name}" if path else name, out)
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            walk_extras(item, f"{path}[{index}]", out)


class Recorder:
    def __init__(self, trace: ModuleType, *, poison: bool) -> None:
        self.trace = trace
        self.poison = poison
        self.records: list[Record] = []

    def probe(self, case: str, probe: str, func: Callable[[], Any]) -> None:
        """Run one probe; its exception is the recorded outcome, never raised."""
        try:
            value = func()
        except Exception as exc:  # noqa: BLE001 - a failing probe is a record
            self.records.append(self.trace.error(case, probe, exc, attrs=error_attrs(exc)))
            return
        if self.poison and probe.startswith("dump.") and isinstance(value, dict) and value:
            value = dict(value)
            del value[min(value)]  # drop one field, the alphabetically first, from every dump.*
        self.records.append(self.trace.ok(case, probe, value))

    def failed(self, case: str, probe: str) -> None:
        self.records.append(self.trace.error(case, probe, DecodeFailed(), attrs={}))


# ------------------------------------------------------------------------------------------------
# Corpus updates
# ------------------------------------------------------------------------------------------------

UPDATE_PROBES = (
    "dump.python",
    "dump.wire",
    "dump_json.default",
    "event",
    "access",
    "extra",
    "eq.same_bot",
    "eq.same_token",
    "eq.other_bot",
    "hash",
    "hash.event",
    "pickle.unbound",
    "pickle.bound",
    "copy.valid",
    "copy.invalid",
)


def without_nulls(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: without_nulls(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [without_nulls(item) for item in value]
    return value


def dump_json(obj: TelegramObject) -> dict[str, Any]:
    text = obj.model_dump_json()
    wire = obj.model_dump_json(by_alias=True, exclude_unset=True)
    value = json.loads(text)
    stripped = without_nulls(value)
    # nulls dropped: a field added to the tree but not to the release would differ otherwise
    return {
        "type": type(text).__name__,
        "value": stripped,
        "nulls": stripped != value,
        "wire": json.loads(wire),
    }


def access(obj: Any, paths: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for path in paths:
        try:
            out[path] = {"ok": True, "value": resolve(obj, path)}
        except Exception as exc:  # noqa: BLE001 - a missing attribute is the observation
            out[path] = {"ok": False, "error": type(exc).__name__}
    return out


def hash_class(obj: Any) -> str:
    return type(hash(obj)).__name__  # the value is salted per process; its class is not


def pickle_unbound(raw: bytes) -> dict[str, Any]:
    obj = Update.model_validate_json(raw)
    restored = pickle.loads(pickle.dumps(obj))  # noqa: S301 - our own bytes
    return {"equal": restored == obj, "type": type(restored).__name__}


def pickle_bound(obj: TelegramObject) -> bool:
    pickle.dumps(obj)
    return True


def copy_valid(update: Update) -> dict[str, Any]:
    copied = update.model_copy(update={"update_id": update.update_id + 1})
    return {
        "update_id": copied.update_id,
        "bot": bot_name(copied),
        "is_new": copied is not update,
        "original": update.update_id,
    }


def copy_invalid(update: Update) -> dict[str, Any]:
    copied = update.model_copy(update={"update_id": "not-an-int"})
    return {"update_id": copied.update_id, "type": type(copied.update_id).__name__}


def probe_update(rec: Recorder, case: str, raw: bytes, paths: list[str]) -> None:
    update: Update | None = None

    def decode_json() -> dict[str, Any]:
        nonlocal update
        update = Update.model_validate_json(raw, context={"bot": BOT})
        return {"type": type(update).__name__}

    def decode_dict() -> dict[str, Any]:
        decoded = Update.model_validate(json.loads(raw), context={"bot": BOT})
        return {"type": type(decoded).__name__}

    rec.probe(case, "decode.json", decode_json)
    rec.probe(case, "decode.dict", decode_dict)
    if update is None:
        for probe in UPDATE_PROBES:
            rec.failed(case, probe)
        return
    obj: Update = update

    def same(bot: Bot) -> bool:
        return Update.model_validate_json(raw, context={"bot": bot}) == obj

    rec.probe(case, "dump.python", lambda: obj.model_dump(mode="json", exclude_unset=True))
    rec.probe(
        case,
        "dump.wire",
        lambda: obj.model_dump(mode="json", by_alias=True, exclude_unset=True),
    )
    rec.probe(case, "dump_json.default", lambda: dump_json(obj))
    rec.probe(
        case,
        "event",
        lambda: {"event_type": obj.event_type, "event": type(obj.event).__name__},
    )
    rec.probe(case, "access", lambda: access(obj, paths))
    rec.probe(case, "extra", lambda: _extras(obj))
    rec.probe(case, "eq.same_bot", lambda: same(BOT))
    rec.probe(case, "eq.same_token", lambda: same(SAME_TOKEN))
    rec.probe(case, "eq.other_bot", lambda: same(OTHER))
    rec.probe(case, "hash", lambda: hash_class(obj))  # Update hashes (type, update_id)
    rec.probe(case, "hash.event", lambda: hash_class(obj.event))
    rec.probe(case, "pickle.unbound", lambda: pickle_unbound(raw))
    rec.probe(case, "pickle.bound", lambda: pickle_bound(obj))
    rec.probe(case, "copy.valid", lambda: copy_valid(obj))
    rec.probe(case, "copy.invalid", lambda: copy_invalid(obj))


def _extras(obj: TelegramObject) -> dict[str, Any]:
    out: dict[str, Any] = {}
    walk_extras(obj, "", out)
    return out


# ------------------------------------------------------------------------------------------------
# Fixed cases: constructors, mutation, codex section 11
# ------------------------------------------------------------------------------------------------


def user() -> User:
    return User(id=100000001, is_bot=False, first_name="Ada")


def message_wire_kwargs() -> Message:
    kwargs: dict[str, Any] = {"from": user()}  # the wire name of from_user
    return Message(message_id=1, date=DATE, chat=Chat(id=1, type="private"), text="hi", **kwargs)


CONSTRUCT: dict[str, Callable[[], BaseModel]] = {
    "User": user,
    "Chat": lambda: Chat(id=100000001, type="private", first_name="Ada"),
    "Message": lambda: Message(
        message_id=1, date=DATE, chat=Chat(id=1, type="private"), from_user=user(), text="hi"
    ),
    "Message.wire_kwargs": message_wire_kwargs,
    "InlineKeyboardMarkup": lambda: InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="a", callback_data="a")]]
    ),
    "SendMessage": lambda: SendMessage(chat_id=100000001, text="hi"),
    "User.invalid": lambda: User.model_validate({"id": "x", "is_bot": False, "first_name": "Ada"}),
}


def dump_python(build: Callable[[], BaseModel]) -> dict[str, Any]:
    # exclude_none, not exclude_unset: keeps Default(...), drops fields a release lacks
    return build().model_dump(exclude_none=True)


def dump_wire(build: Callable[[], BaseModel]) -> dict[str, Any]:
    return build().model_dump(mode="json", by_alias=True, exclude_unset=True)


def probe_construct(rec: Recorder) -> None:
    for name, build in CONSTRUCT.items():
        case = f"model.construct.{name}"
        # Python mode keeps Default(...) placeholders, which canonical() records by repr
        rec.probe(case, "dump.python", partial(dump_python, build))
        rec.probe(case, "dump.wire", partial(dump_wire, build))
    # D87: 3.x keeps any object as an extra
    rec.probe(
        "model.construct.User",
        "extra.non_json",
        lambda: User(id=1, is_bot=False, first_name="Ada", future=DATE).model_extra,
    )


def assign(obj: BaseModel, name: str, value: Any) -> dict[str, Any]:
    setattr(obj, name, value)
    return {name: getattr(obj, name)}


MUTATE: dict[str, Callable[[], dict[str, Any]]] = {
    "InlineKeyboardButton": lambda: assign(
        InlineKeyboardButton(text="a", callback_data="a"), "text", "b"
    ),
    "InlineKeyboardMarkup": lambda: assign(
        InlineKeyboardMarkup(inline_keyboard=[]), "inline_keyboard", []
    ),
    "User": lambda: assign(user(), "first_name", "Bob"),
    "Message": lambda: assign(CONSTRUCT["Message"](), "text", "bye"),
}


def probe_mutate(rec: Recorder) -> None:
    for name, func in MUTATE.items():
        rec.probe(f"model.mutate.{name}", "mutate", func)


def codex_eq_across_bots(raw: bytes) -> bool:
    left = Update.model_validate_json(raw, context={"bot": BOT})
    return left == Update.model_validate_json(raw, context={"bot": OTHER})


def codex_dump_json_type(raw: bytes) -> str:
    return type(Update.model_validate_json(raw).model_dump_json()).__name__


def codex_model_extra_only_unknown() -> dict[str, Any] | None:
    return User(id=1, is_bot=False, first_name="Ada", future_field=1).model_extra


def codex_exclude_none_nested_null() -> dict[str, Any]:
    obj = User(id=1, is_bot=False, first_name="Ada", future={"kept": None, "n": 1})
    return obj.model_dump(exclude_none=True)


def codex_pickle_bound(raw: bytes) -> dict[str, Any]:
    out = {"unbound": pickle_unbound(raw)["equal"]}
    try:
        pickle.dumps(Update.model_validate_json(raw, context={"bot": BOT}))
        out["bound"] = "ok"
    except Exception as exc:  # noqa: BLE001 - the failure is the observation
        out["bound"] = type(exc).__name__
    return out


def codex_as_keeps_nested_bot(raw: bytes) -> dict[str, Any]:
    update = Update.model_validate_json(raw, context={"bot": BOT})
    message = update.message
    assert message is not None  # noqa: S101 - update.text.small is a message
    view = message.as_(OTHER)
    return {
        "returns_self": view is message,
        "original": bot_name(message),
        "view": bot_name(view),
        "view_child": bot_name(view.chat),
        "root": bot_name(update),
    }


def codex_builder_export_copy() -> dict[str, Any]:
    builder = InlineKeyboardBuilder()
    builder.button(text="a", callback_data="a")
    exported = builder.export()
    exported[0][0].text = "changed"
    return {"assigned": exported[0][0].text, "builder": builder.export()[0][0].text}


def probe_codex11(rec: Recorder, small: bytes) -> None:
    cases: dict[str, Callable[[], Any]] = {
        "eq_across_bots": lambda: codex_eq_across_bots(small),
        "dump_json_type": lambda: codex_dump_json_type(small),
        "model_extra_only_unknown": codex_model_extra_only_unknown,
        "exclude_none_nested_null": codex_exclude_none_nested_null,
        "pickle_bound": lambda: codex_pickle_bound(small),
        "as_keeps_nested_bot": lambda: codex_as_keeps_nested_bot(small),
        "builder_export_copy": codex_builder_export_copy,
    }
    for name, func in cases.items():
        rec.probe(f"model.codex11.{name}", "observe", func)


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
    paths = tomllib.loads(ACCESS.read_text(encoding="utf-8"))["access"]
    updates = {item["id"]: item["path"] for item in manifest["input"] if item["kind"] == "update"}

    rec = Recorder(trace, poison=args.poison)
    for input_id, path in updates.items():
        # KeyError on a missing access list: a new corpus input needs one
        probe_update(rec, f"model.{input_id}", (corpus / path).read_bytes(), paths[input_id])
    probe_construct(rec)
    probe_mutate(rec)
    probe_codex11(rec, (corpus / updates["update.text.small"]).read_bytes())

    header = json.loads(args.header)
    header.update(
        aiogram=aiogram.__version__,
        python=sys.version.split()[0],
        implementation=platform.python_implementation(),
        platform=sys.platform,
    )
    trace.write(args.out, header, records=rec.records)


if __name__ == "__main__":
    main()
