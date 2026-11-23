"""Routing side for aiogram 3.x: build each ``routing/*.toml`` topology, feed its events, trace.

Standalone: stdlib + aiogram only, run by the runner as ``python -I routing.py --corpus DIR
--out FILE --trace-module trace.py --header JSON [--poison]``. The topology schema is in
``benchmarks/corpus/README.md``; the probes are described in ``differential/README.md``.

Every user component (filter, middleware, handler, ``errors`` handler, scene action) is a small
closure that appends an entry to the current feed's list (a ``ContextVar``, which
``asyncio.to_thread`` copies into the worker thread). The aiogram filters (``command``,
``text_eq``, ``magic_*``) are registered as they are, unwrapped, so aiogram runs its own code for
them; their effect shows in what runs next and in the data it sees.
"""

from __future__ import annotations

import argparse
import asyncio
import contextvars
import copy
import importlib.util
import json
import logging
import platform
import sys
import threading
import tomllib
import types
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from types import ModuleType
from typing import Any

from pydantic import ValidationError

import aiogram
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.session.base import BaseSession
from aiogram.dispatcher.event.bases import UNHANDLED, SkipHandler
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.dispatcher.flags import get_flag
from aiogram.filters import Command, Filter
from aiogram.fsm.scene import Scene, SceneRegistry, ScenesManager, on
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import SendMessage, TelegramMethod
from aiogram.types import Message, TelegramObject, Update

TOKEN = "42:TEST"  # fake; the session below never reaches the network
FEEDS = ("polling", "webhook")
COMPILED = {"command", "text_eq", "magic_eq", "magic_true"}  # what 4.0 compiles into rejectors
MIDDLEWARE_KINDS = {
    "pass",
    "short_circuit",
    "call_twice",
    "write",
    "skip_after_write",
    "replace",
    "raise",
    "register",
    "get_flag",
}

Entry = dict[str, Any]
Spec = dict[str, Any]
Handler = Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]]

ENTRIES: contextvars.ContextVar[list[Entry]] = contextvars.ContextVar("oracle_entries")
UPDATE: contextvars.ContextVar[int] = contextvars.ContextVar("oracle_update", default=0)
LOOP_THREAD = threading.get_ident()


class OracleError(Exception):
    """Raised by ``raise`` components; its message is the spec's ``error``."""


class NoNetworkSession(BaseSession):
    async def close(self) -> None:
        pass

    async def make_request(
        self, bot: Bot, method: TelegramMethod[Any], timeout: int | None = None
    ) -> Any:
        msg = f"the routing oracle makes no requests (got {type(method).__name__})"
        raise RuntimeError(msg)

    async def stream_content(self, *args: Any, **kwargs: Any) -> AsyncGenerator[bytes, None]:
        msg = "the routing oracle streams nothing"
        raise RuntimeError(msg)
        yield b""  # pragma: no cover - makes this an async generator


# ------------------------------------------------------------------------------------------------
# Recording
# ------------------------------------------------------------------------------------------------


def shape(value: Any) -> Any:
    """The canonical subset of a data value: JSON data as is, objects as their type name."""
    if value is UNHANDLED:
        return "UNHANDLED"
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [shape(item) for item in value]
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return {key: shape(item) for key, item in value.items()}
    if isinstance(value, Router):
        return {"router": value.name}
    if isinstance(value, HandlerObject):
        callback = getattr(value.callback, "handler", None)  # a scene's SceneHandlerWrapper
        callback = getattr(callback, "callback", value.callback)
        name = getattr(callback, "__qualname__", type(callback).__name__)
        return {"handler": getattr(callback, "oracle_id", name)}
    if isinstance(value, TelegramMethod):
        return {
            "method": type(value).__name__,
            "params": value.model_dump(mode="json", exclude_defaults=True),
        }
    return {"type": type(value).__name__}


def event_shape(event: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"type": type(event).__name__}
    for attr in ("text", "data"):
        if isinstance(getattr(event, attr, None), str):
            out[attr] = getattr(event, attr)
    exception = getattr(event, "exception", None)
    if isinstance(exception, BaseException):
        out["exception"] = {"type": type(exception).__name__, "message": str(exception)}
    return out


def raised(exc: BaseException) -> dict[str, Any]:
    return {"raised": type(exc).__name__}


class Where:
    """A component's identity: its id, kind and the router it belongs to."""

    def __init__(self, spec: Spec, kind: str, router: str, path: list[str]) -> None:
        self.id: str = spec["id"]
        self.kind = kind
        self.router = router
        self.path = path
        self.owner: str | None = None  # a filter's handler
        self.observer: str | None = None  # a middleware's event type
        self.late: str | None = None  # the registration that added it while handling (D114)

    def record(
        self,
        result: Any,
        *,
        data: dict[str, Any] | None = None,
        event: Any = None,
        threaded: bool = False,
        registers: str | None = None,
    ) -> None:
        entry: Entry = {
            "component": self.id,
            "kind": self.kind,
            "router": self.router,
            "path": self.path,
            "update": UPDATE.get(),
            "result": result,
        }
        if self.owner is not None:
            entry["owner"] = self.owner
        if self.observer is not None:
            entry["observer"] = self.observer
        if self.late is not None:
            entry["late"] = self.late
        if registers is not None:
            entry["registers"] = registers
        if data is not None:
            entry["data"] = {key: shape(data[key]) for key in sorted(data)}
            entry["event"] = event_shape(event)
        if threaded:
            entry["on_loop"] = threading.get_ident() == LOOP_THREAD
        ENTRIES.get().append(entry)


# ------------------------------------------------------------------------------------------------
# Components
# ------------------------------------------------------------------------------------------------


class FlagsFilter(Filter):
    """A filter that adds handler flags (``Filter.update_handler_flags``) and records its call."""

    def __init__(self, where: Where, flags: dict[str, Any]) -> None:
        self.where = where
        self.flags = flags

    def update_handler_flags(self, flags: dict[str, Any]) -> None:
        flags.update(self.flags)

    async def __call__(self, event: TelegramObject, **data: Any) -> bool:
        self.where.record(True, data=data, event=event, threaded=True)
        return True


def make_filter(spec: Spec, where: Where) -> Any:  # noqa: C901 - one branch per kind
    kind = spec["kind"]
    if kind == "command":
        return Command(*spec["commands"])
    if kind == "text_eq":
        return F.text == spec["value"]
    if kind == "magic_eq":
        return getattr(F, spec["attr"]) == spec["value"]
    if kind == "magic_true":
        return getattr(F, spec["attr"])
    if kind == "flags":
        return FlagsFilter(where, spec["flags"])
    result = spec.get("result", True)
    if kind == "data":
        result = spec["returns"]

    def outcome(event: TelegramObject, data: dict[str, Any]) -> Any:
        if kind == "raise":
            where.record({"raised": "OracleError"}, data=data, event=event, threaded=True)
            raise OracleError(spec["error"])
        sum(range(spec.get("work", 0)))  # D34: a sync filter doing work
        for key, items in spec.get("mutate", {}).items():  # R09: copies are shallow
            data[key].update(items)
        value = copy.deepcopy(result)  # a fresh dict per call, as a real filter returns
        where.record(value, data=data, event=event, threaded=True)
        return value

    if kind == "sync":

        def sync_filter(event: TelegramObject, **data: Any) -> Any:
            return outcome(event, data)

        return sync_filter
    if kind in {"async", "data", "raise"}:

        async def async_filter(event: TelegramObject, **data: Any) -> Any:
            return outcome(event, data)

        return async_filter
    msg = f"unknown filter kind {kind!r}"
    raise ValueError(msg)


def patched_event(event: TelegramObject, patch: dict[str, Any]) -> TelegramObject:
    """A copy of ``event`` with dotted-path fields replaced (models are frozen)."""
    payload = event.model_dump(mode="json", exclude_unset=True, by_alias=True)
    apply_patch(payload, patch)
    return type(event).model_validate(payload, context={"bot": event.bot})


def make_middleware(spec: Spec, where: Where, build: Builder) -> Any:  # noqa: C901
    kind = spec["kind"]
    if kind not in MIDDLEWARE_KINDS:
        msg = f"unknown middleware kind {kind!r}"
        raise ValueError(msg)

    async def middleware(handler: Handler, event: TelegramObject, data: dict[str, Any]) -> Any:
        entered: Any = "enter"
        registers = None
        if kind == "get_flag":
            entered = {"flag": shape(get_flag(data, spec["name"]))}
        elif kind == "register" and build.register_late(spec["register"]):
            registers = spec["register"]["id"]
        where.record(entered, data=data, event=event, registers=registers)
        try:
            if kind == "short_circuit":
                result: Any = spec.get("value", where.id)
            elif kind == "raise":
                raise OracleError(spec["error"])
            elif kind == "skip_after_write" and shape(data.get("handler")) == {
                "handler": spec["handler"]
            }:
                data[spec["key"]] = copy.deepcopy(spec["value"])  # R09: survives SkipHandler
                raise SkipHandler
            else:
                if kind == "write":
                    data[spec["key"]] = copy.deepcopy(spec["value"])
                elif kind == "replace":
                    event = patched_event(event, spec["patch"])
                result = await handler(event, data)
                if kind == "call_twice":
                    result = [shape(result), shape(await handler(event, data))]
        except Exception as exc:
            where.record(raised(exc))
            raise
        where.record(shape(result))
        return result

    middleware.oracle_id = where.id  # type: ignore[attr-defined]
    return middleware


def make_handler(spec: Spec, where: Where, build: Builder, *, scene: bool = False) -> Any:
    action: Spec = spec.get("action", {"kind": "return"})
    kind = action["kind"]

    def finish(event: TelegramObject, data: dict[str, Any]) -> Any:
        """The part of every action that needs no await."""
        if kind == "skip":
            where.record({"raised": "SkipHandler"}, data=data, event=event, threaded=True)
            raise SkipHandler
        if kind == "raise":
            where.record({"raised": "OracleError"}, data=data, event=event, threaded=True)
            raise OracleError(action["error"])
        if kind == "unhandled":
            where.record("UNHANDLED", data=data, event=event, threaded=True)
            return UNHANDLED
        if kind == "get_flag":
            value = {"flag": shape(get_flag(data, action["name"]))}
            where.record(value, data=data, event=event, threaded=True)
            return value
        if kind == "reply":
            chat_id = event.chat.id  # type: ignore[attr-defined]
            method = SendMessage(chat_id=chat_id, text=action.get("text", where.id))
            where.record(shape(method), data=data, event=event, threaded=True)
            return method
        value = action.get("value", where.id)
        where.record(value, data=data, event=event, threaded=True)
        return value

    async def run(event: TelegramObject, data: dict[str, Any]) -> Any:
        if kind == "register":
            registers = (
                action["register"]["id"] if build.register_late(action["register"]) else None
            )
            where.record(where.id, data=data, event=event, threaded=True, registers=registers)
            return where.id
        if kind == "await_yield":
            where.record("start", data=data, event=event, threaded=True)
            for _ in range(action.get("yields", 3)):
                await asyncio.sleep(0)
        elif kind == "scene_enter":
            scenes: ScenesManager = data["scenes"]
            where.record(f"enter {action['scene']}", data=data, event=event, threaded=True)
            await scenes.enter(build.scenes[action["scene"]])
            return where.id
        elif kind in {"scene_leave", "scene_back", "scene_exit", "scene_goto"}:
            wizard = data["wizard"]
            where.record(kind, data=data, event=event, threaded=True)
            if kind == "scene_goto":
                await wizard.goto(build.scenes[action["scene"]])
            else:
                await getattr(wizard, kind.removeprefix("scene_"))()
            return where.id
        return finish(event, data)

    async def by_signature(event: TelegramObject, event_from_user: Any) -> Any:
        return await run(event, {"event_from_user": event_from_user})

    async def scene_method(self: Scene, event: TelegramObject, **data: Any) -> Any:
        return await run(event, {**data, "wizard": self.wizard})

    def sync_handler(event: TelegramObject, **data: Any) -> Any:
        return finish(event, data)

    async def async_handler(event: TelegramObject, **data: Any) -> Any:
        return await run(event, data)

    callback: Any
    if spec.get("params") == ["event_from_user"]:  # D12: asks for it by signature, no **data
        callback = by_signature
    elif spec.get("params"):
        msg = f"unsupported params {spec['params']!r}"
        raise ValueError(msg)
    elif scene:
        callback = scene_method
    elif spec.get("sync"):
        callback = sync_handler
    else:
        callback = async_handler
    callback.oracle_id = where.id
    return callback


# ------------------------------------------------------------------------------------------------
# Topology
# ------------------------------------------------------------------------------------------------


def ids(specs: list[Spec], prefix: str) -> list[Spec]:
    """Give every spec without an ``id`` a positional one."""
    return [{"id": f"{prefix}{n}", **spec} for n, spec in enumerate(specs)]


class Builder:
    """One Dispatcher built from a topology; ``register_late`` adds components while handling."""

    def __init__(self, topology: dict[str, Any], *, fsm: bool) -> None:
        self.routers: dict[str, Router] = {}
        self.paths: dict[str, list[str]] = {}
        self.scenes: dict[str, type[Scene]] = {}
        self.registered: set[str] = set()
        # (event type, handler id, path, compiled filters): who may match, for the meta
        self.candidates: list[tuple[str, str, list[str], list[Any]]] = []
        self.d12_params: list[str] = []  # handlers that ask for event_from_user by signature
        for spec in topology["router"]:
            self.add_router(spec, fsm=fsm)
        for spec in topology.get("scene", []):
            self.add_scene(spec)
        if self.scenes:
            SceneRegistry(self.dp).add(*self.scenes.values())

    @property
    def dp(self) -> Dispatcher:
        root = next(iter(self.routers.values()))
        assert isinstance(root, Dispatcher)  # noqa: S101 - the first router is the root
        return root

    def add_router(self, spec: Spec, *, fsm: bool = True, late: str | None = None) -> None:
        name = spec["name"]
        router: Router
        if "parent" not in spec:
            router = Dispatcher(storage=MemoryStorage(), disable_fsm=not fsm, name=name)
            self.paths[name] = [name]
        else:
            router = Router(name=name)
            self.paths[name] = [*self.paths[spec["parent"]], name]
            self.routers[spec["parent"]].include_router(router)
        self.routers[name] = router
        for mw in ids(spec.get("outer_middlewares", []), f"{name}.outer"):
            self.add_middleware(name, mw, outer=True, late=late)
        for mw in ids(spec.get("inner_middlewares", []), f"{name}.inner"):
            self.add_middleware(name, mw, outer=False, late=late)
        for flt in ids(spec.get("root_filters", []), f"{name}.root"):
            where = self.where(flt, "filter", name, late)
            router.observers[flt["event"]].filter(make_filter(flt, where))
        for handler in ids(spec.get("handler", []), f"{name}.h"):
            self.add_handler(name, handler, late=late)
        for handler in ids(spec.get("error_handler", []), f"{name}.e"):
            self.add_handler(name, {**handler, "event": "error"}, kind="error", late=late)

    def where(
        self, spec: Spec, kind: str, router: str, late: str | None, owner: str | None = None
    ) -> Where:
        where = Where(spec, kind, router, self.paths[router])
        where.late = late
        where.owner = owner
        return where

    def add_middleware(self, router: str, spec: Spec, *, outer: bool, late: str | None) -> None:
        where = self.where(spec, "outer" if outer else "inner", router, late)
        where.observer = spec["event"]
        observer = self.routers[router].observers[spec["event"]]
        middleware = make_middleware(spec, where, self)
        if outer:
            observer.outer_middleware(middleware)
        else:
            observer.middleware(middleware)

    def add_handler(
        self, router: str, spec: Spec, *, kind: str = "handler", late: str | None
    ) -> None:
        where = self.where(spec, kind, router, late)
        specs = ids(spec.get("filters", []), f"{spec['id']}.f")
        filters = [
            make_filter(flt, self.where(flt, "filter", router, late, owner=spec["id"]))
            for flt in specs
        ]
        if kind == "handler":
            self.add_candidate(spec["event"], spec["id"], router, specs, filters)
        if spec.get("params"):
            self.d12_params.append(spec["id"])
        self.routers[router].observers[spec["event"]].register(
            make_handler(spec, where, self), *filters, flags=spec.get("flags")
        )

    def add_scene(self, spec: Spec) -> None:
        name = spec["name"]
        self.paths[name] = [*self.paths[spec.get("parent", next(iter(self.routers)))], name]
        namespace: dict[str, Any] = {"__module__": "oracle", "__qualname__": name}
        for handler in ids(spec.get("handler", []), f"{name}.h"):
            where = self.where(handler, "handler", name, None)
            specs = ids(handler.get("filters", []), f"{handler['id']}.f")
            filters = [
                make_filter(flt, self.where(flt, "filter", name, None, owner=handler["id"]))
                for flt in specs
            ]
            self.add_candidate(handler["event"], handler["id"], name, specs, filters)
            marker = getattr(on, handler["event"])
            callback = make_handler(handler, where, self, scene=True)
            namespace[f"handler_{handler['id']}"] = marker(*filters)(callback)
        for action in ids(spec.get("action", []), f"{name}.a"):
            where = self.where(action, "scene_action", name, None)
            marker = getattr(getattr(on, action["event"]), action["on"])
            callback = make_handler(
                {**action, "action": {"kind": "return", "value": action["on"]}},
                where,
                self,
                scene=True,
            )
            namespace[f"action_{action['id']}"] = marker()(callback)
        self.scenes[name] = types.new_class(
            name, (Scene,), {"state": name}, lambda body: body.update(namespace)
        )

    def add_candidate(
        self, event: str, handler: str, router: str, specs: list[Spec], filters: list[Any]
    ) -> None:
        compiled = [
            obj for flt, obj in zip(specs, filters, strict=True) if flt["kind"] in COMPILED
        ]
        self.candidates.append((event, handler, self.paths[router], compiled))

    async def eligibility(self, bot: Bot, index: int, update: Update) -> list[dict[str, Any]]:
        """The candidates for the update's event type, and whether a compiled filter (``command``,
        ``text_eq``, ``magic_*``) is certainly false on the original event: what PD-19 and
        breaking change 13 decide on in 4.0. Computed before feeding, so late handlers are not
        candidates of the update that registers them."""
        event_type, event = update.event_type, update.event
        out = []
        for observer, handler, path, compiled in self.candidates:
            if observer != event_type:
                continue
            rejected = False
            for obj in compiled:
                if isinstance(obj, Command):
                    passed: Any = isinstance(event, Message) and await obj(event, bot=bot)
                else:
                    passed = obj.resolve(event)
                if not passed:
                    rejected = True
                    break
            out.append({"update": index, "handler": handler, "path": path, "rejected": rejected})
        return out

    def register_late(self, spec: Spec) -> bool:
        """D114: add components while an update is being handled; True the first time only."""
        key = spec["id"]
        if key in self.registered:
            return False
        self.registered.add(key)
        what = spec["what"]
        if what == "router":
            self.add_router(spec["router"], late=key)
        elif what in {"outer_middleware", "inner_middleware"}:
            self.add_middleware(
                spec["router"], spec["middleware"], outer=what == "outer_middleware", late=key
            )
        elif what == "handler":
            self.add_handler(spec["router"], spec["handler"], late=key)
        else:
            msg = f"unknown late registration {what!r}"
            raise ValueError(msg)
        return True

    def poison(self) -> None:
        """Swap the first two handlers of every observer that has two or more."""
        for router in self.routers.values():
            for observer in router.observers.values():
                if len(observer.handlers) >= 2:  # noqa: PLR2004
                    observer.handlers[0:2] = observer.handlers[1::-1]


def apply_patch(payload: dict[str, Any], patch: dict[str, Any]) -> None:
    for dotted, value in patch.items():
        *path, last = dotted.split(".")
        node = payload
        for key in path:
            node = node[key]
        node[last] = value


# ------------------------------------------------------------------------------------------------
# Feeding
# ------------------------------------------------------------------------------------------------


def outcome_of(exc: BaseException) -> dict[str, Any]:
    if isinstance(exc, ValidationError):  # no str(exc): it embeds the pydantic version
        attrs: Any = exc.errors(include_url=False, include_input=False)
        return {"raised": {"type": "ValidationError", "errors": attrs}}
    return {"raised": {"type": type(exc).__name__, "message": str(exc)}}


async def feed_one(dp: Dispatcher, bot: Bot, update: Update, index: int, feed: str) -> Any:
    UPDATE.set(index)  # each gathered task runs in its own context copy
    try:
        if feed == "webhook":
            result: Any = await dp.feed_webhook_update(bot, update)
        else:
            result = await dp.feed_update(bot, update)
    except Exception as exc:  # noqa: BLE001 - an escaping exception is a recorded outcome
        return outcome_of(exc)
    return {"returned": shape(result)}


@asynccontextmanager
async def recording() -> AsyncGenerator[list[Entry], None]:
    entries: list[Entry] = []
    token = ENTRIES.set(entries)
    try:
        yield entries
    finally:
        ENTRIES.reset(token)


def batches(events: list[Spec]) -> list[list[Spec]]:
    """Consecutive events with the same ``group`` are fed concurrently, one case per group."""
    out: list[list[Spec]] = []
    for event in events:
        group = event.get("group")
        if out and group is not None and out[-1][0].get("group") == group:
            out[-1].append(event)
        else:
            out.append([event])
    return out


def probes(entries: list[Entry]) -> dict[str, list[Entry]]:
    """Split entries into the ``trace``, ``kwargs`` and ``threads`` probes.

    Each keeps the identity fields (component, kind, router, path, update, owner, late,
    registers); ``trace`` adds ``result``, ``kwargs`` the visible ``data`` and ``event``,
    ``threads`` ``on_loop``.
    """
    own = {"result": "trace", "data": "kwargs", "event": "kwargs", "on_loop": "threads"}
    out: dict[str, list[Entry]] = {"trace": [], "kwargs": [], "threads": []}
    for entry in entries:
        common = {k: v for k, v in entry.items() if k not in own}
        out["trace"].append({**common, "result": entry["result"]})
        if "data" in entry:
            out["kwargs"].append({**common, "data": entry["data"], "event": entry["event"]})
        if "on_loop" in entry:
            out["threads"].append({**common, "on_loop": entry["on_loop"]})
    return out


def raised_entry(entry: Entry) -> bool:
    result = entry["result"]
    return isinstance(result, dict) and "raised" in result and result["raised"] != "SkipHandler"


def reference(
    entries: list[Entry], candidates: list[dict[str, Any]], count: int
) -> dict[str, Any]:
    """What the 3.x reference knows that the approved 4.0 differences decide on (``meta``,
    read by the comparators only). It also drops ``late`` from components registered in an
    earlier case: from then on they are part of the routing."""
    here = {e["registers"] for e in entries if "registers" in e}
    for entry in entries:
        if entry.get("late") not in here:
            entry.pop("late", None)
    late_handled = [
        any(
            e["update"] == index and e["kind"] == "handler" and "late" in e and not raised_entry(e)
            for e in entries
        )
        for index in range(count)
    ]
    errors = []
    for index in range(count):
        mine = [e for e in entries if e["update"] == index]
        handlers = [e for e in mine if e["kind"] == "error"]
        raising = next((e for e in mine if raised_entry(e)), None)
        if not handlers or raising is None:
            continue
        exception = next(
            (e["event"]["exception"] for e in handlers if "exception" in e.get("event", {})), None
        )
        errors.append(
            {
                "update": index,
                "raise_path": raising["path"],
                "exception": exception,
                "handlers": [
                    {"component": e["component"], "router": e["router"], "result": e["result"]}
                    for e in handlers
                ],
            }
        )
    return {"candidates": candidates, "late_handled": late_handled, "errors": errors}


def make_updates(batch: list[Spec], payloads: dict[str, bytes], bot: Bot) -> list[Update]:
    updates = []
    for event in batch:
        payload = json.loads(payloads[event["update"]])
        apply_patch(payload, event.get("patch", {}))
        updates.append(Update.model_validate(payload, context={"bot": bot}))
    return updates


async def run_topology(
    trace: ModuleType,
    topology_id: str,
    topology: dict[str, Any],
    payloads: dict[str, bytes],
    *,
    poison: bool,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    variants = topology.get("variants", {})
    for feed in variants.get("feed", ["polling"]):
        if feed not in FEEDS:
            msg = f"{topology_id}: unknown feed {feed!r}"
            raise ValueError(msg)
        for fsm in variants.get("fsm", ["on"]):  # the A-05 bench's default too
            prefix = f"{topology_id}.{feed}.fsm-{fsm}"
            build = Builder(topology, fsm=fsm == "on")
            if poison:
                build.poison()
            used = build.dp.resolve_used_update_types()
            records.append(trace.ok(prefix, "used_update_types", used))
            bot = Bot(TOKEN, session=NoNetworkSession())
            seen: set[str] = set()
            for batch in batches(topology["event"]):
                updates = make_updates(batch, payloads, bot)
                case = f"{prefix}.{batch[0].get('group', batch[0]['name'])}"
                if case in seen:
                    msg = f"{topology_id}: event or group name {case.rsplit('.', 1)[1]!r} reused"
                    raise ValueError(msg)
                seen.add(case)
                candidates = [
                    candidate
                    for index, update in enumerate(updates)
                    for candidate in await build.eligibility(bot, index, update)
                ]
                loop = asyncio.get_running_loop()
                started = loop.time()
                async with recording() as entries:
                    results = await asyncio.gather(
                        *(
                            feed_one(build.dp, bot, update, index, feed)
                            for index, update in enumerate(updates)
                        )
                    )
                meta = {
                    "elapsed_s": loop.time() - started,
                    **reference(entries, candidates, len(updates)),
                    "d12_params": build.d12_params,
                }
                for probe, value in probes(entries).items():
                    records.append(trace.ok(case, probe, value, meta=meta))
                records.append(trace.ok(case, "result", results, meta=meta))
    return records


def load_module(path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location("differential_trace", path)
    if spec is None or spec.loader is None:
        msg = f"cannot load {path}"
        raise ImportError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--trace-module", required=True)
    parser.add_argument("--header", required=True)
    parser.add_argument("--poison", action="store_true")
    args = parser.parse_args()

    logging.disable(logging.CRITICAL)  # aiogram logs escaping exceptions; they are recorded
    trace = load_module(args.trace_module)
    corpus = Path(args.corpus)
    manifest = tomllib.loads((corpus / "MANIFEST.toml").read_text(encoding="utf-8"))
    inputs = {item["id"]: item for item in manifest["input"]}
    payloads = {
        key: (corpus / item["path"]).read_bytes()
        for key, item in inputs.items()
        if item["kind"] == "update"
    }

    records: list[dict[str, Any]] = []
    for key, item in inputs.items():
        if item["kind"] != "routing":
            continue
        topology = tomllib.loads((corpus / item["path"]).read_text(encoding="utf-8"))
        records.extend(
            asyncio.run(run_topology(trace, key, topology, payloads, poison=args.poison))
        )

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
