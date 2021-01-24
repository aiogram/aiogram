import asyncio
import contextvars
import inspect
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Type, Union

from aiogram.dispatcher.filters.base import BaseFilter
from aiogram.dispatcher.handler.base import BaseHandler

CallbackType = Callable[..., Awaitable[Any]]
SyncFilter = Callable[..., Any]
AsyncFilter = Callable[..., Awaitable[Any]]
FilterType = Union[SyncFilter, AsyncFilter, BaseFilter]
HandlerType = Union[FilterType, Type[BaseHandler]]


@dataclass
class CallableMixin:
    callback: HandlerType
    awaitable: bool = field(init=False)
    spec: inspect.FullArgSpec = field(init=False)

    def __post_init__(self) -> None:
        callback = inspect.unwrap(self.callback)
        self.awaitable = inspect.isawaitable(callback) or inspect.iscoroutinefunction(callback)
        self.spec = inspect.getfullargspec(callback)

    def _prepare_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        if self.spec.varkw:
            return kwargs

        return {k: v for k, v in kwargs.items() if k in self.spec.args}

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
    callback: FilterType


@dataclass
class HandlerObject(CallableMixin):
    callback: HandlerType
    filters: Optional[List[FilterObject]] = None

    def __post_init__(self) -> None:
        super(HandlerObject, self).__post_init__()
        callback = inspect.unwrap(self.callback)
        if inspect.isclass(callback) and issubclass(callback, BaseHandler):
            self.awaitable = True

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
