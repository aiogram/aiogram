import asyncio
import contextvars
import inspect
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Type, Union, cast

from aiogram.dispatcher.filters.base import BaseFilter
from aiogram.dispatcher.handler.base import BaseHandler
from aiogram.dispatcher.requirement import (
    CacheKeyType,
    Requirement,
    get_reqs_from_callable,
    get_reqs_from_class,
)

CallbackType = Callable[..., Awaitable[Any]]
SyncFilter = Callable[..., Any]
AsyncFilter = Callable[..., Awaitable[Any]]
FilterType = Union[SyncFilter, AsyncFilter, BaseFilter]
HandlerType = Union[FilterType, Type[BaseHandler]]

REQUIREMENT_CACHE_KEY = "_req_cache"
ASYNC_STACK_KEY = "_stack"


def _is_class_handler(handler: HandlerType) -> bool:
    return isinstance(handler, type) and issubclass(handler, BaseHandler)


@dataclass
class CallableMixin:
    callback: HandlerType
    awaitable: bool = field(init=False)
    spec: inspect.FullArgSpec = field(init=False)

    requirements: Dict[str, Requirement[Any]] = field(init=False)

    def __post_init__(self) -> None:
        callback = inspect.unwrap(self.callback)
        self.awaitable = inspect.isawaitable(callback) or inspect.iscoroutinefunction(callback)
        if isinstance(callback, BaseFilter):
            callback = callback.__call__

        self.spec = inspect.getfullargspec(callback)

        if _is_class_handler(callback):
            self.awaitable = True
            self.requirements = get_reqs_from_class(callback)
        else:
            self.requirements = get_reqs_from_callable(callable_=callback)

    def _prepare_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        if self.spec.varkw:
            return kwargs

        return {k: v for k, v in kwargs.items() if k in self.spec.args}

    async def call(self, *args: Any, **data: Any) -> Any:
        # we don't requirements_data and kwargs keys to intersect
        requirements_data: Dict[str, Any] = {}

        if self.requirements:
            stack = cast(AsyncExitStack, data.get(ASYNC_STACK_KEY))
            cache_dict: Dict[CacheKeyType, Any] = data.get(REQUIREMENT_CACHE_KEY, {})
            requirements_data = data.copy()

            for req_id, req in self.requirements.items():
                requirements_data[req_id] = await req(
                    cache_dict=cache_dict, stack=stack, data=requirements_data,
                )

            for to_pop in data:
                requirements_data.pop(to_pop, None)

        data.pop(ASYNC_STACK_KEY, None)
        data.pop(REQUIREMENT_CACHE_KEY, None)

        if _is_class_handler(self.callback):
            wrapped = partial(self.callback, *args, requirements_data, data)
        else:
            wrapped = partial(
                self.callback,
                *args,
                **self._prepare_kwargs(data),
                **self._prepare_kwargs(requirements_data),
            )

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
