import asyncio
import contextvars
import inspect
import warnings
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Tuple

from magic_filter.magic import MagicFilter as OriginalMagicFilter

from aiogram.dispatcher.flags import extract_flags_from_object
from aiogram.filters.base import Filter
from aiogram.handlers import BaseHandler
from aiogram.utils.magic_filter import MagicFilter
from aiogram.utils.warnings import Recommendation

CallbackType = Callable[..., Any]


@dataclass
class CallableMixin:
    callback: CallbackType
    awaitable: bool = field(init=False)
    spec: inspect.FullArgSpec = field(init=False)

    def __post_init__(self) -> None:
        callback = inspect.unwrap(self.callback)
        self.awaitable = inspect.isawaitable(callback) or inspect.iscoroutinefunction(callback)
        self.spec = inspect.getfullargspec(callback)

    def _prepare_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        if self.spec.varkw:
            return kwargs

        return {
            k: v for k, v in kwargs.items() if k in self.spec.args or k in self.spec.kwonlyargs
        }

    async def call(self, *args: Any, **kwargs: Any) -> Any:
        wrapped = partial(self.callback, *args, **self._prepare_kwargs(kwargs))
        if self.awaitable:
            return await wrapped()

        loop = asyncio.get_event_loop()
        context = contextvars.copy_context()
        wrapped = partial(context.run, wrapped)
        return await loop.run_in_executor(None, wrapped)


@dataclass
class FilterObject(CallableMixin):
    magic: Optional[MagicFilter] = None

    def __post_init__(self) -> None:
        if isinstance(self.callback, OriginalMagicFilter):
            # MagicFilter instance is callable but generates
            # only "CallOperation" instead of applying the filter
            self.magic = self.callback
            self.callback = self.callback.resolve
            if not isinstance(self.magic, MagicFilter):
                # Issue: https://github.com/aiogram/aiogram/issues/990
                warnings.warn(
                    category=Recommendation,
                    message="You are using F provided by magic_filter package directly, "
                    "but it lacks `.as_()` extension."
                    "\n Please change the import statement: from `from magic_filter import F` "
                    "to `from aiogram import F` to silence this warning.",
                    stacklevel=6,
                )

        super(FilterObject, self).__post_init__()

        if isinstance(self.callback, Filter):
            self.awaitable = True


@dataclass
class HandlerObject(CallableMixin):
    filters: Optional[List[FilterObject]] = None
    flags: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super(HandlerObject, self).__post_init__()
        callback = inspect.unwrap(self.callback)
        if inspect.isclass(callback) and issubclass(callback, BaseHandler):
            self.awaitable = True
        self.flags.update(extract_flags_from_object(callback))

    async def check(self, *args: Any, **kwargs: Any) -> Tuple[bool, Dict[str, Any]]:
        if not self.filters:
            return True, kwargs
        for event_filter in self.filters:
            check = await event_filter.call(*args, **kwargs)
            if not check:
                return False, kwargs
            if isinstance(check, dict):
                kwargs.update(check)
        return True, kwargs
