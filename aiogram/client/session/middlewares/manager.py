from __future__ import annotations

import inspect
import warnings
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, NamedTuple, TypeVar, overload

if TYPE_CHECKING:
    from aiogram.client.bot import Bot
    from aiogram.client.session.middlewares.base import RequestContext, RequestMiddlewareType
    from aiogram.methods import TelegramMethod

#: A middleware to place next to: a class (its first registered instance) or a registered object
Anchor = object
M = TypeVar("M")

_LEGACY_ARGUMENTS = 3  # make_request, bot, method
_POSITIONAL = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)


class _Entry(NamedTuple):
    middleware: Any
    call: RequestMiddlewareType
    before: Anchor | None
    after: Anchor | None


class _LegacyMiddleware:
    """Runs a 3.x ``(make_request, bot, method)`` middleware in a ``(ctx)`` chain."""

    __slots__ = ("middleware",)

    def __init__(self, middleware: Any) -> None:
        self.middleware = middleware

    async def __call__(self, ctx: RequestContext[Any]) -> Any:
        # Each call gets its own context, as each 3.x partial was its own call: concurrent
        # calls each run the inner chain, and a rewrite does not outlive its call.
        async def make_request(bot: Bot, method: TelegramMethod[Any]) -> Any:
            return await ctx._fork(bot, method).next()

        return await self.middleware(make_request, ctx.bot, ctx.method)


def _name(obj: Any) -> str:
    return getattr(obj, "__qualname__", None) or type(obj).__qualname__


def _adapt(middleware: Any) -> RequestMiddlewareType:
    try:
        parameters = inspect.signature(middleware).parameters.values()
    except (TypeError, ValueError):
        parameters = None
    if parameters is not None and not any(
        p.kind is inspect.Parameter.VAR_POSITIONAL for p in parameters
    ):
        required = sum(p.kind in _POSITIONAL and p.default is p.empty for p in parameters)
        if required == 1:
            return middleware  # type: ignore[no-any-return]
        if required == _LEGACY_ARGUMENTS:
            # ponytail: plain DeprecationWarning until I-12's AiogramDeprecationWarning lands
            warnings.warn(
                f"AG4062: request middleware {_name(middleware)} takes the 3.x arguments "
                "(make_request, bot, method); take one RequestContext instead: "
                "`async def middleware(ctx)` and `await ctx.next()`.",
                DeprecationWarning,
                stacklevel=4,  # _adapt, _register, register / __call__ / decorator, caller
            )
            return _LegacyMiddleware(middleware)
    msg = (
        f"request middleware {_name(middleware)} must take one positional argument, "
        "the RequestContext: `async def middleware(ctx)` (a wrapper needs functools.wraps)"
    )
    raise TypeError(msg)


def _find(entries: list[_Entry], anchor: Anchor, skip: int) -> int | None:
    for index, entry in enumerate(entries):
        if index == skip:
            continue
        if isinstance(anchor, type):
            if isinstance(entry.middleware, anchor):
                return index
        elif entry.middleware is anchor:
            return index
    return None


def _resolve(entries: list[_Entry]) -> list[_Entry]:
    """
    Registration order, moved by the anchors.

    Walks the entries in registration order and places each one after everything that must run
    outside it, so entries that no anchor relates keep their registration order.
    """
    outer: list[list[int]] = [[] for _ in entries]
    for index, entry in enumerate(entries):
        for anchor, side in ((entry.before, "before"), (entry.after, "after")):
            if anchor is None:
                continue
            target = _find(entries, anchor, index)
            if target is None:
                msg = (
                    f"request middleware {_name(entry.middleware)} is anchored "
                    f"{side}={_name(anchor)}, which is not registered"
                )
                raise ValueError(msg)
            if side == "before":
                outer[target].append(index)
            else:
                outer[index].append(target)

    order: list[int] = []
    placed: set[int] = set()
    stack: list[int] = []

    def place(index: int) -> None:
        if index in placed:
            return
        if index in stack:
            cycle = stack[stack.index(index) :][::-1]
            names = " -> ".join(_name(entries[i].middleware) for i in [*cycle, cycle[0]])
            msg = f"request middleware anchors form a cycle: {names}"
            raise ValueError(msg)
        stack.append(index)
        for parent in sorted(outer[index]):
            place(parent)
        stack.pop()
        placed.add(index)
        order.append(index)

    for index in range(len(entries)):
        place(index)
    return [entries[index] for index in order]


class RequestMiddlewareManager(Sequence[Any]):
    """
    Request middlewares of a session, in execution order (outermost first).

    The order is the registration order, moved by the ``before=`` / ``after=`` anchors. It is
    resolved once and reused until the next :meth:`register` / :meth:`unregister`.
    """

    def __init__(self) -> None:
        self._entries: list[_Entry] = []
        self._order: list[_Entry] | None = []
        self._chain: tuple[RequestMiddlewareType, ...] | None = ()

    def register(
        self,
        middleware: M,
        *,
        before: Anchor | None = None,
        after: Anchor | None = None,
    ) -> M:
        """
        Add a middleware.

        :param middleware: ``async def middleware(ctx: RequestContext)``; a 3.x
            ``(make_request, bot, method)`` middleware still works, with a deprecation warning
        :param before: run outside this middleware (a class: its first registered instance)
        :param after: run inside this middleware
        :return: the middleware, so this works as a decorator

        Anchors are resolved at the next API call: a missing anchor or a cycle raises
        :class:`ValueError` there.
        """
        return self._register(middleware, before, after)

    def _register(self, middleware: M, before: Anchor | None, after: Anchor | None) -> M:
        self._entries.append(_Entry(middleware, _adapt(middleware), before, after))
        self._order = self._chain = None
        return middleware

    def unregister(self, middleware: Any) -> None:
        for index, entry in enumerate(self._entries):
            if entry.middleware == middleware:
                del self._entries[index]
                self._order = self._chain = None
                return
        msg = f"request middleware {_name(middleware)} is not registered"
        raise ValueError(msg)

    @overload
    def __call__(
        self,
        middleware: None = None,
        *,
        before: Anchor | None = None,
        after: Anchor | None = None,
    ) -> Callable[[M], M]: ...

    @overload
    def __call__(
        self,
        middleware: M,
        *,
        before: Anchor | None = None,
        after: Anchor | None = None,
    ) -> M: ...

    def __call__(
        self,
        middleware: Any = None,
        *,
        before: Anchor | None = None,
        after: Anchor | None = None,
    ) -> Any:
        if middleware is None:
            return lambda m: self._register(m, before, after)
        return self._register(middleware, before, after)

    def _resolved(self) -> list[_Entry]:
        if self._order is None:
            self._order = _resolve(self._entries)
        return self._order

    @property
    def chain(self) -> tuple[RequestMiddlewareType, ...]:
        """The callables to run, outermost first; resolved again only after a change."""
        if self._chain is None:
            self._chain = tuple(entry.call for entry in self._resolved())
        return self._chain

    @overload
    def __getitem__(self, item: int) -> Any: ...

    @overload
    def __getitem__(self, item: slice) -> Sequence[Any]: ...

    def __getitem__(self, item: int | slice) -> Any:
        order = self._resolved()
        if isinstance(item, slice):
            return [entry.middleware for entry in order[item]]
        return order[item].middleware

    def __len__(self) -> int:
        return len(self._entries)
