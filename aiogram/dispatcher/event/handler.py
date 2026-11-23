import asyncio
import inspect
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial
from typing import Any

from magic_filter.magic import MagicFilter as OriginalMagicFilter

from aiogram.dispatcher.flags import extract_flags_from_object
from aiogram.filters.base import Filter

CallbackType = Callable[..., Any]

_ACCEPTED_PARAM_KINDS = {
    inspect.Parameter.POSITIONAL_ONLY,
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
    inspect.Parameter.KEYWORD_ONLY,
}


@dataclass
class CallableObject:
    callback: CallbackType
    awaitable: bool = field(init=False)
    params: set[str] = field(init=False)
    varkw: bool = field(init=False)

    def __post_init__(self) -> None:
        callback = inspect.unwrap(self.callback)
        self.awaitable = (
            inspect.isawaitable(callback)
            or inspect.iscoroutinefunction(callback)
            # A callable object is async when its `__call__` is a coroutine function
            or (callable(callback) and inspect.iscoroutinefunction(type(callback).__call__))
        )

        kwargs: dict[str, Any] = {}
        if sys.version_info >= (3, 14):
            import annotationlib

            kwargs["annotation_format"] = annotationlib.Format.FORWARDREF

        try:
            signature = inspect.signature(callback, **kwargs)
        except (ValueError, TypeError):  # pragma: no cover
            self.params = set()
            self.varkw = False
            return

        params: set[str] = set()
        varkw: bool = False

        for p in signature.parameters.values():
            if p.kind in _ACCEPTED_PARAM_KINDS:
                params.add(p.name)
            elif p.kind == inspect.Parameter.VAR_KEYWORD:
                varkw = True
        self.params = params
        self.varkw = varkw

    def _prepare_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        if self.varkw:
            return kwargs

        return {k: kwargs[k] for k in self.params if k in kwargs}

    async def call(self, *args: Any, **kwargs: Any) -> Any:
        wrapped = partial(self.callback, *args, **self._prepare_kwargs(kwargs))
        if self.awaitable:
            return await wrapped()
        return await asyncio.to_thread(wrapped)

    async def call_event(self, event: Any, data: dict[str, Any]) -> Any:
        """
        ``call(event, **data)`` without copying ``data`` first (the dispatch executor's path).

        The callback still gets its own keyword arguments, so it cannot change ``data``.
        """
        kwargs = self._prepare_kwargs(data)
        if self.awaitable:
            return await self.callback(event, **kwargs)
        return await asyncio.to_thread(partial(self.callback, event, **kwargs))


@dataclass
class FilterObject(CallableObject):
    magic: OriginalMagicFilter | None = None

    def __post_init__(self) -> None:
        if isinstance(self.callback, OriginalMagicFilter):
            # MagicFilter instance is callable but generates
            # only "CallOperation" instead of applying the filter
            self.magic = self.callback
            self.callback = self.callback.resolve

        super().__post_init__()

        if isinstance(self.callback, Filter):
            self.awaitable = True

    async def call(self, *args: Any, **kwargs: Any) -> Any:
        return self._checked(await super().call(*args, **kwargs))

    async def call_event(self, event: Any, data: dict[str, Any]) -> Any:
        return self._checked(await super().call_event(event, data))

    def _checked(self, result: Any) -> Any:
        if inspect.isawaitable(result):
            # An awaitable is truthy: never let it pass as a match. Nothing is awaited or
            # cancelled; only a coroutine is closed, so it leaves no "never awaited" warning
            if inspect.iscoroutine(result):
                result.close()
            msg = (
                f"Filter {self.magic if self.magic is not None else self.callback!r} "
                "returned an awaitable instead of a result. "
                "Declare async filters with `async def`; sync filters must return a bool or a dict"
            )
            raise TypeError(msg)
        return result


@dataclass
class HandlerObject(CallableObject):
    filters: list[FilterObject] | None = None
    flags: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.flags.update(extract_flags_from_object(inspect.unwrap(self.callback)))

    async def check(self, *args: Any, **kwargs: Any) -> tuple[bool, dict[str, Any]]:
        if not self.filters:
            return True, kwargs
        for event_filter in self.filters:
            check = await event_filter.call(*args, **kwargs)
            if not check:
                return False, kwargs
            if isinstance(check, dict):
                kwargs.update(check)
        return True, kwargs
