import inspect
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Type, Union

from aiogram.dispatcher.filters.base import BaseFilter
from aiogram.dispatcher.handler.base import BaseHandler

CallbackType = Callable[[Any], Awaitable[Any]]
SyncFilter = Callable[[Any], Any]
AsyncFilter = Callable[[Any], Awaitable[Any]]
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
        if isinstance(callback, BaseFilter):
            # Pydantic 1.5 has incorrect signature generator
            # Issue: https://github.com/samuelcolvin/pydantic/issues/1419
            # Fixes: https://github.com/samuelcolvin/pydantic/pull/1427
            # TODO: Remove this temporary fix
            callback = inspect.unwrap(callback.__call__)
        self.spec = inspect.getfullargspec(callback)

    def _prepare_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        if self.spec.varkw:
            return kwargs

        return {k: v for k, v in kwargs.items() if k in self.spec.args}

    async def call(self, *args: Any, **kwargs: Any) -> Any:
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

    def __post_init__(self) -> None:
        super(HandlerObject, self).__post_init__()
        if inspect.isclass(self.callback) and issubclass(self.callback, BaseHandler):  # type: ignore
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
