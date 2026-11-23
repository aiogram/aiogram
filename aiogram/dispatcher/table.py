"""
Compiled routing table and its executor (internal).

:func:`compile_table` turns a dispatcher's router tree into an immutable :class:`DispatchTable`;
:func:`execute` runs one update through it. The middleware chains are built at compile, so running
a compiled table builds no ``functools.partial`` chain and no closure per router (until the routing
snapshot cache lands, ``Dispatcher.feed_update`` compiles a table per update).

Semantics are 3.x's (03 §3, R09), with one documented break (D111 / PD-19, breaking change 24): a
router's outer middlewares for an event type run only when a router at or below it has a handler
for that type. Data scopes, each a shallow copy of the one above it, as in 3.x:

- update scope: the dict the ``dp.update`` outer chain gets;
- router scope: a copy at router entry, ``event_router`` set there; outer middlewares get it;
- body scope: a copy past the outer chain; root-filter results are merged into it;
- trigger scope: a copy shared by the candidates of one router (``handler`` set per candidate);
  inner middlewares get it, so their writes survive a ``SkipHandler``;
- candidate scope: copied lazily at the first dict-returning filter and merged into the trigger
  scope only when every filter passes, so a failed candidate leaves nothing behind.

The table captures the graph's structure when it is compiled: mutating routers while an update
runs is not supported and does not affect that update.
"""

from __future__ import annotations

import functools
import warnings
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final

from aiogram import loggers
from aiogram.types.update import UpdateTypeLookupError

from .event.bases import UNHANDLED, SkipHandler

if TYPE_CHECKING:
    from aiogram.client.bot import Bot
    from aiogram.filters.command import CommandObject
    from aiogram.types import TelegramObject, Update

    from .dispatcher import Dispatcher
    from .event.bases import MiddlewareType
    from .event.handler import FilterObject, HandlerObject
    from .router import Router

__all__ = (
    "Candidate",
    "DispatchTable",
    "EventPlan",
    "HandlerResultHook",
    "RouterFrame",
    "RoutingKeys",
    "compile_plan",
    "compile_table",
    "enter_frame",
    "execute",
    "route_update",
    "routing_keys",
)

Chain = Callable[[Any, dict[str, Any]], Any]
HandlerResultHook = Callable[[Any, dict[str, Any]], Any]
"""``(value, data) -> value``: sees each handler's return value inside its middleware scope."""


@dataclass(frozen=True, slots=True)
class Candidate:
    router: Router
    handler: HandlerObject
    filters: tuple[FilterObject, ...]
    call: Chain
    """The inner chain (inherited inner middlewares, root first) ending in the handler."""


@dataclass(frozen=True, slots=True)
class RouterFrame:
    router: Router
    parent: RouterFrame | None
    root_filters: tuple[FilterObject, ...]
    candidates: tuple[Candidate, ...]
    span: range
    """Positions of :attr:`candidates` in :attr:`EventPlan.candidates`."""
    # Set right after the frame is created (they refer back to it); never changed afterwards.
    children: tuple[RouterFrame, ...] = ()
    outer: Chain = None  # type: ignore[assignment]
    """The router's outer chain for this event type, ending in the frame body."""


@dataclass(frozen=True, slots=True)
class EventPlan:
    event_type: str
    frames: tuple[RouterFrame, ...]
    """DFS order (3.x ``sub_routers`` order); ``frames[0]`` is the root."""
    candidates: tuple[Candidate, ...]


@dataclass(frozen=True, slots=True)
class DispatchTable:
    dispatcher: Dispatcher
    update: RouterFrame
    """The ``dp.update`` level: the routing stage, then the user's ``dp.update`` handlers."""
    by_event: Mapping[str, EventPlan]
    """Only event types with at least one handler in the tree."""
    workflow_data: Mapping[str, Any]

    @property
    def outer_chain(self) -> Chain:
        """The prebuilt ``dp.update`` outer chain."""
        return self.update.outer


# ------------------------------------------------------------------------------------------------
# Routing keys (a Python shim until E-09 swaps in the native ``update.routing_keys()``)
# ------------------------------------------------------------------------------------------------

# The order of the if-chain in Update.event_type: it decides when an update has two event fields
_EVENT_FIELDS: Final[tuple[str, ...]] = (
    "message",
    "edited_message",
    "channel_post",
    "edited_channel_post",
    "inline_query",
    "chosen_inline_result",
    "callback_query",
    "shipping_query",
    "pre_checkout_query",
    "poll",
    "poll_answer",
    "my_chat_member",
    "chat_member",
    "chat_join_request",
    "message_reaction",
    "message_reaction_count",
    "chat_boost",
    "removed_chat_boost",
    "deleted_business_messages",
    "business_connection",
    "edited_business_message",
    "business_message",
    "purchased_paid_media",
    "guest_message",
    "managed_bot",
    "subscription",
    "stopped_message_generation",
    "widget_query",
    "shared_widget_query",
)
_EVENT_PRIORITY: Final[dict[str, int]] = {name: i for i, name in enumerate(_EVENT_FIELDS)}


class RoutingKeys:
    """
    What routing reads from one update.

    ``event_type`` and ``event`` are computed at once; the other keys on first access.
    """

    def __init__(self, update: Update) -> None:
        # The fields set on the update (usually update_id and one event), not all 30 fields
        found = [
            name
            for name in update.model_fields_set
            if name in _EVENT_PRIORITY and getattr(update, name) is not None
        ]
        if not found:
            msg = "Update does not contain any known event type."
            raise UpdateTypeLookupError(msg)
        self.event_type: str = min(found, key=_EVENT_PRIORITY.__getitem__)
        self.event: TelegramObject = getattr(update, self.event_type)

    @functools.cached_property
    def text(self) -> str | None:
        """``text`` or ``caption``, as :class:`~aiogram.filters.command.Command` reads them."""
        from aiogram.types import Message  # noqa: PLC0415

        if not isinstance(self.event, Message):
            return None
        return self.event.text or self.event.caption

    @functools.cached_property
    def command(self) -> CommandObject | None:
        """The command, parsed by the exact 3.x rule (``Command.extract_command``)."""
        from aiogram.filters.command import Command, CommandException  # noqa: PLC0415

        if not self.text:
            return None
        try:
            return Command.extract_command(self.text)
        except CommandException:
            return None

    @functools.cached_property
    def callback_data(self) -> str | None:
        from aiogram.types import CallbackQuery  # noqa: PLC0415

        return self.event.data if isinstance(self.event, CallbackQuery) else None

    @functools.cached_property
    def chat_type(self) -> str | None:
        chat = getattr(self.event, "chat", None)
        return getattr(chat, "type", None)

    @functools.cached_property
    def content_kind(self) -> str | None:
        from aiogram.types import Message  # noqa: PLC0415

        return self.event.content_type if isinstance(self.event, Message) else None


def routing_keys(update: Update) -> RoutingKeys:
    """Routing keys of an update; raises :class:`UpdateTypeLookupError` for an unknown type."""
    return RoutingKeys(update)


# ------------------------------------------------------------------------------------------------
# Compile
# ------------------------------------------------------------------------------------------------


def _chain(middlewares: Iterable[MiddlewareType[Any]], terminal: Chain) -> Chain:
    for middleware in reversed(tuple(middlewares)):
        terminal = functools.partial(middleware, terminal)
    return terminal


def _inner_middlewares(router: Router, event_type: str) -> list[MiddlewareType[Any]]:
    """Inner middlewares a handler of ``router`` inherits: its real parents', root first."""
    middlewares: list[MiddlewareType[Any]] = []
    for item in reversed(tuple(router.chain_head)):
        observer = item.observers.get(event_type)
        if observer:
            middlewares.extend(observer.middleware)
    return middlewares


def _terminal(handler: HandlerObject, hook: HandlerResultHook | None) -> Chain:
    if hook is None:
        return handler.call_event
    return functools.partial(_call_hooked, handler, hook)


async def _call_hooked(
    handler: HandlerObject, hook: HandlerResultHook, event: Any, data: dict[str, Any]
) -> Any:
    return hook(await handler.call_event(event, data), data)


def _frame(
    router: Router,
    event_type: str,
    parent: RouterFrame | None,
    candidates: list[Candidate],
    terminals: Callable[[HandlerObject], Chain],
) -> RouterFrame:
    """One router's frame; its own candidates go to ``candidates`` (DFS order)."""
    observer = router.observers.get(event_type)
    start = len(candidates)
    if observer is not None:
        inner = _inner_middlewares(router, event_type)
        candidates.extend(
            Candidate(
                router=router,
                handler=handler,
                filters=tuple(handler.filters or ()),
                call=_chain(inner, terminals(handler)),
            )
            for handler in observer.handlers
        )
    frame = RouterFrame(
        router=router,
        parent=parent,
        root_filters=tuple(observer._handler.filters or ()) if observer is not None else (),
        candidates=tuple(candidates[start:]),
        span=range(start, len(candidates)),
    )
    body = functools.partial(_frame_body, frame)
    outer = observer.outer_middleware if observer is not None else ()
    # The outer chain's terminal copies the data, as 3.x does; without outer middlewares no
    # one else holds the router scope, so the copy is skipped
    object.__setattr__(  # noqa: PLC2801 - frozen dataclass, set once while compiling
        frame, "outer", _chain(outer, functools.partial(_copy_into, body)) if outer else body
    )
    return frame


def compile_plan(
    root: Router, event_type: str, *, on_handler_result: HandlerResultHook | None = None
) -> EventPlan | None:
    """
    The plan of one event type over ``root``'s subtree, or ``None`` when it has no handler.

    A router gets a frame iff its subtree has a handler for ``event_type`` (D111 / PD-19).
    """
    candidates: list[Candidate] = []
    frames: list[RouterFrame] = []

    def terminals(handler: HandlerObject) -> Chain:
        return _terminal(handler, on_handler_result)

    def build(router: Router, parent: RouterFrame | None) -> RouterFrame | None:
        mark = len(candidates), len(frames)
        frame = _frame(router, event_type, parent, candidates, terminals)
        frames.append(frame)
        children = tuple(
            child
            for child in (build(sub, frame) for sub in router.sub_routers)
            if child is not None
        )
        if not frame.candidates and not children:
            del candidates[mark[0] :], frames[mark[1] :]
            return None
        object.__setattr__(frame, "children", children)  # noqa: PLC2801 - see _frame
        return frame

    if build(root, None) is None:
        return None
    return EventPlan(event_type=event_type, frames=tuple(frames), candidates=tuple(candidates))


def compile_table(
    dispatcher: Dispatcher, *, on_handler_result: HandlerResultHook | None = None
) -> DispatchTable:
    """
    Compile ``dispatcher``'s router tree.

    ``on_handler_result(value, data) -> value`` is called with each handler's return value,
    inside the handler's inner and outer middlewares (not for ``SkipHandler`` or an error).
    """
    event_types = {
        name
        for router in dispatcher.chain_tail
        for name, observer in router.observers.items()
        if observer.handlers and name != "update"
    }
    by_event: dict[str, EventPlan] = {}
    for event_type in sorted(event_types):
        plan = compile_plan(dispatcher, event_type, on_handler_result=on_handler_result)
        if plan is not None:  # pragma: no branch - event_types only holds types with a handler
            by_event[event_type] = plan
    from .dispatcher import Dispatcher  # noqa: PLC0415 - dispatcher imports this module

    builtin_listener = Dispatcher._listen_update
    plans = MappingProxyType(by_event)
    routing_stage = functools.partial(route_update, plans)

    def terminals(handler: HandlerObject) -> Chain:
        # The built-in listener only: a subclass override of _listen_update still runs as written
        callback = handler.callback
        if (
            getattr(callback, "__func__", None) is builtin_listener
            and getattr(callback, "__self__", None) is dispatcher
        ):
            return routing_stage
        return _terminal(handler, on_handler_result)

    update = _frame(dispatcher, "update", None, [], terminals)
    return DispatchTable(
        dispatcher=dispatcher,
        update=update,
        by_event=plans,
        workflow_data=MappingProxyType(dict(dispatcher.workflow_data)),
    )


# ------------------------------------------------------------------------------------------------
# Execute (stage boundaries are separate functions for the tracing / error plans to wrap)
# ------------------------------------------------------------------------------------------------


async def execute(table: DispatchTable, bot: Bot, update: Update, data: dict[str, Any]) -> Any:
    """Run one update through ``table``; ``data`` holds the caller's extra keyword arguments."""
    scope = {"dispatcher": table.dispatcher, **table.workflow_data, **data, "bot": bot}
    return await table.outer_chain(update, scope)


async def route_update(
    plans: Mapping[str, EventPlan], update: Update, data: dict[str, Any]
) -> Any:
    """The routing stage: the first ``dp.update`` handler (3.x ``Dispatcher._listen_update``)."""
    try:
        keys = routing_keys(update)
    except UpdateTypeLookupError as e:
        # Constant text: Python keeps every distinct warning text for the process lifetime
        warnings.warn(
            "Detected unknown update type.\n"
            "Seems like Telegram Bot API was updated and you have "
            "installed not latest version of aiogram framework",
            RuntimeWarning,
            stacklevel=2,
        )
        loggers.event.debug("Unknown update type: %r", update)
        raise SkipHandler() from e
    plan = plans.get(keys.event_type)
    if plan is None:
        return UNHANDLED
    return await enter_frame(plan.frames[0], keys.event, {**data, "event_update": update})


async def enter_frame(frame: RouterFrame, event: Any, data: dict[str, Any]) -> Any:
    """Enter a router: ``data`` is its router scope, a dict the caller hands over."""
    data["event_router"] = frame.router
    return await frame.outer(event, data)


async def _copy_into(body: Chain, event: Any, data: dict[str, Any]) -> Any:
    return await body(event, {**data})


async def _frame_body(frame: RouterFrame, event: Any, data: dict[str, Any]) -> Any:
    """Root filters, own candidates, then the children; ``data`` is the body scope."""
    if frame.root_filters:
        scope = await check_filters(frame.root_filters, event, data)
        if scope is None:
            return UNHANDLED
        if scope is not data:
            data.update(scope)
    if frame.candidates:
        response = await trigger(frame.candidates, event, data)
        if response is not UNHANDLED:
            return response
    for child in frame.children:
        response = await enter_frame(child, event, {**data})
        if response is not UNHANDLED:
            return response
    return UNHANDLED


async def check_filters(
    filters: tuple[FilterObject, ...], event: Any, data: dict[str, Any]
) -> dict[str, Any] | None:
    """
    ``None`` if a filter fails, else the scope the filters produced.

    That is ``data`` itself when no filter returned a dict, else a copy with the results merged;
    ``data`` is never changed.
    """
    scope = data
    for event_filter in filters:
        result = await event_filter.call_event(event, scope)
        if not result:
            return None
        if isinstance(result, dict):
            if scope is data:
                scope = {**data}
            scope.update(result)
    return scope


async def trigger(candidates: tuple[Candidate, ...], event: Any, data: dict[str, Any]) -> Any:
    """The first candidate whose filters pass and that does not raise ``SkipHandler`` wins."""
    scope = {**data}
    for candidate in candidates:
        scope["handler"] = candidate.handler
        if candidate.filters:
            checked = await check_filters(candidate.filters, event, scope)
            if checked is None:
                continue
            if checked is not scope:
                scope.update(checked)
        try:
            return await candidate.call(event, scope)
        except SkipHandler:
            continue
    return UNHANDLED
