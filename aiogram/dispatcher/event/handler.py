import inspect
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Union

from aiogram.dispatcher.filters.base import BaseFilter
from aiogram.dispatcher.handler.base import BaseHandler

CallbackType = Callable[[Any], Awaitable[Any]]
SyncFilter = Callable[[Any], Any]
AsyncFilter = Callable[[Any], Awaitable[Any]]
FilterType = Union[SyncFilter, AsyncFilter, BaseFilter]
HandlerType = Union[FilterType, BaseHandler]


@dataclass
class CallableMixin:
    callback: HandlerType
    awaitable: bool = field(init=False)
    spec: inspect.FullArgSpec = field(init=False)

    def __post_init__(self):
        callback = self.callback
        self.awaitable = inspect.isawaitable(callback) or inspect.iscoroutinefunction(callback)
        while hasattr(callback, "__wrapped__"):  # Try to resolve decorated callbacks
            callback = callback.__wrapped__
        self.spec = inspect.getfullargspec(callback)

    def _prepare_kwargs(self, kwargs):
        if self.spec.varkw:
            return kwargs

        return {k: v for k, v in kwargs.items() if k in self.spec.args}

    async def call(self, *args, **kwargs):
        wrapped = partial(self.callback, *args, **self._prepare_kwargs(kwargs))
        if self.awaitable:
            return await wrapped()
        return wrapped()


@dataclass
class FilterObject(CallableMixin):
    callback: FilterType


@dataclass
class HandlerObject(CallableMixin):
    callback: HandlerType
    filters: Optional[List[FilterObject]] = None

    def __post_init__(self):
        super(HandlerObject, self).__post_init__()

        if inspect.isclass(self.callback) and issubclass(self.callback, BaseHandler):
            self.awaitable = True

    async def check(self, *args: Any, **kwargs: Any) -> Tuple[bool, Dict[str, Any]]:
        if not self.filters:
            return True, {}
        for event_filter in self.filters:
            check = await event_filter.call(*args, **kwargs)
            if not check:
                return False, {}
            if isinstance(check, dict):
                kwargs.update(check)
        return True, kwargs
