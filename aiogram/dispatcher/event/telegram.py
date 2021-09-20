from __future__ import annotations

import functools
from itertools import chain
from typing import TYPE_CHECKING, Any, Callable, Dict, Generator, List, Optional, Type, Union

from pydantic import ValidationError

from ...types import TelegramObject
from ..filters.base import BaseFilter
from .bases import (
    REJECTED,
    UNHANDLED,
    MiddlewareEventType,
    MiddlewareType,
    NextMiddlewareType,
    SkipHandler,
)
from .handler import CallbackType, FilterObject, FilterType, HandlerObject, HandlerType

if TYPE_CHECKING:
    from aiogram.dispatcher.router import Router


class TelegramEventObserver:
    """
    Event observer for Telegram events

    Here you can register handler with filters or bounded filters which can be used as keyword arguments instead of writing full references when you register new handlers.
    This observer will stops event propagation when first handler is pass.
    """

    def __init__(self, router: Router, event_name: str) -> None:
        self.router: Router = router
        self.event_name: str = event_name

        self.handlers: List[HandlerObject] = []
        self.filters: List[Type[BaseFilter]] = []
        self.outer_middlewares: List[MiddlewareType[TelegramObject]] = []
        self.middlewares: List[MiddlewareType[TelegramObject]] = []

        # Re-used filters check method from already implemented handler object
        # with dummy callback which never will be used
        self._handler = HandlerObject(callback=lambda: True, filters=[])

    def filter(self, *filters: FilterType, **bound_filters: Any) -> None:
        """
        Register filter for all handlers of this event observer

        :param filters: positional filters
        :param bound_filters: keyword filters
        """
        resolved_filters = self.resolve_filters(bound_filters)
        if self._handler.filters is None:
            self._handler.filters = []
        self._handler.filters.extend(
            [FilterObject(filter_) for filter_ in chain(resolved_filters, filters)]
        )

    def bind_filter(self, bound_filter: Type[BaseFilter]) -> None:
        """
        Register filter class in factory

        :param bound_filter:
        """
        if not issubclass(bound_filter, BaseFilter):
            raise TypeError(
                "bound_filter() argument 'bound_filter' must be subclass of BaseFilter"
            )
        self.filters.append(bound_filter)

    def _resolve_filters_chain(self) -> Generator[Type[BaseFilter], None, None]:
        """
        Get all bounded filters from current observer and from the parents
        with the same event type without duplicates
        """
        registry: List[Type[BaseFilter]] = []

        for router in self.router.chain:
            observer = router.observers[self.event_name]

            for filter_ in observer.filters:
                if filter_ in registry:
                    continue
                yield filter_
                registry.append(filter_)

    def _resolve_middlewares(self, *, outer: bool = False) -> List[MiddlewareType[TelegramObject]]:
        """
        Get all middlewares in a tree
        :param *:
        """
        middlewares = []
        if outer:
            middlewares.extend(self.outer_middlewares)
        else:
            for router in reversed(list(self.router.chain_head)):
                observer = router.observers[self.event_name]
                middlewares.extend(observer.middlewares)

        return middlewares

    def resolve_filters(self, full_config: Dict[str, Any]) -> List[BaseFilter]:
        """
        Resolve keyword filters via filters factory
        """
        filters: List[BaseFilter] = []
        if not full_config:
            return filters

        for bound_filter in self._resolve_filters_chain():
            # Try to initialize filter.
            try:
                f = bound_filter(**full_config)
            except ValidationError:
                continue

            # Clean full config to prevent to re-initialize another filter
            # with the same configuration
            for key in f.__fields__:
                full_config.pop(key, None)

            filters.append(f)

        if full_config:
            raise ValueError(f"Unknown keyword filters: {set(full_config.keys())}")

        return filters

    def register(
        self, callback: HandlerType, *filters: FilterType, **bound_filters: Any
    ) -> HandlerType:
        """
        Register event handler
        """
        resolved_filters = self.resolve_filters(bound_filters)
        self.handlers.append(
            HandlerObject(
                callback=callback,
                filters=[FilterObject(filter_) for filter_ in chain(resolved_filters, filters)],
            )
        )
        return callback

    @classmethod
    def _wrap_middleware(
        cls, middlewares: List[MiddlewareType[MiddlewareEventType]], handler: HandlerType
    ) -> NextMiddlewareType[MiddlewareEventType]:
        @functools.wraps(handler)
        def mapper(event: TelegramObject, kwargs: Dict[str, Any]) -> Any:
            return handler(event, **kwargs)

        middleware = mapper
        for m in reversed(middlewares):
            middleware = functools.partial(m, middleware)
        return middleware

    def wrap_outer_middleware(
        self, callback: Any, event: TelegramObject, data: Dict[str, Any]
    ) -> Any:
        wrapped_outer = self._wrap_middleware(self._resolve_middlewares(outer=True), callback)
        return wrapped_outer(event, data)

    async def trigger(self, event: TelegramObject, **kwargs: Any) -> Any:
        """
        Propagate event to handlers and stops propagation on first match.
        Handler will be called when all its filters is pass.
        """
        # Check globally defined filters before any other handler will be checked
        result, data = await self._handler.check(event, **kwargs)
        if not result:
            return REJECTED
        kwargs.update(data)

        for handler in self.handlers:
            result, data = await handler.check(event, **kwargs)
            if result:
                kwargs.update(data)
                try:
                    wrapped_inner = self._wrap_middleware(
                        self._resolve_middlewares(), handler.call
                    )
                    return await wrapped_inner(event, kwargs)
                except SkipHandler:
                    continue

        return UNHANDLED

    def __call__(
        self, *args: FilterType, **bound_filters: Any
    ) -> Callable[[CallbackType], CallbackType]:
        """
        Decorator for registering event handlers
        """

        def wrapper(callback: CallbackType) -> CallbackType:
            self.register(callback, *args, **bound_filters)
            return callback

        return wrapper

    def middleware(
        self,
        middleware: Optional[MiddlewareType[TelegramObject]] = None,
    ) -> Union[
        Callable[[MiddlewareType[TelegramObject]], MiddlewareType[TelegramObject]],
        MiddlewareType[TelegramObject],
    ]:
        """
        Decorator for registering inner middlewares

        Usage:

        .. code-block:: python

            @<event>.middleware()  # via decorator (variant 1)

        .. code-block:: python

            @<event>.middleware  # via decorator (variant 2)

        .. code-block:: python

            async def my_middleware(handler, event, data): ...
            <event>.middleware(my_middleware)  # via method
        """

        def wrapper(m: MiddlewareType[TelegramObject]) -> MiddlewareType[TelegramObject]:
            self.middlewares.append(m)
            return m

        if middleware is None:
            return wrapper
        return wrapper(middleware)

    def outer_middleware(
        self,
        middleware: Optional[MiddlewareType[TelegramObject]] = None,
    ) -> Union[
        Callable[[MiddlewareType[TelegramObject]], MiddlewareType[TelegramObject]],
        MiddlewareType[TelegramObject],
    ]:
        """
        Decorator for registering outer middlewares

        Usage:

        .. code-block:: python

            @<event>.outer_middleware()  # via decorator (variant 1)

        .. code-block:: python

            @<event>.outer_middleware  # via decorator (variant 2)

        .. code-block:: python

            async def my_middleware(handler, event, data): ...
            <event>.outer_middleware(my_middleware)  # via method
        """

        def wrapper(m: MiddlewareType[TelegramObject]) -> MiddlewareType[TelegramObject]:
            self.outer_middlewares.append(m)
            return m

        if middleware is None:
            return wrapper
        return wrapper(middleware)
