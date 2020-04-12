from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING, Any, AsyncGenerator, Callable, Dict, Generator, List, Type

from pydantic import ValidationError

from ..filters.base import BaseFilter
from ..middlewares.types import MiddlewareStep, UpdateType
from .handler import CallbackType, FilterObject, FilterType, HandlerObject, HandlerType

if TYPE_CHECKING:  # pragma: no cover
    from aiogram.dispatcher.router import Router


class SkipHandler(Exception):
    pass


class EventObserver:
    """
    Base events observer
    """

    def __init__(self) -> None:
        self.handlers: List[HandlerObject] = []

    def register(self, callback: HandlerType) -> HandlerType:
        """
        Register callback with filters
        """
        self.handlers.append(HandlerObject(callback=callback))
        return callback

    async def trigger(self, *args: Any, **kwargs: Any) -> AsyncGenerator[Any, None]:
        """
        Propagate event to handlers.
        Handler will be called when all its filters is pass.
        """
        for handler in self.handlers:
            try:
                yield await handler.call(*args, **kwargs)
            except SkipHandler:
                continue

    def __call__(self) -> Callable[[CallbackType], CallbackType]:
        """
        Decorator for registering event handlers
        """

        def wrapper(callback: CallbackType) -> CallbackType:
            self.register(callback)
            return callback

        return wrapper


class TelegramEventObserver(EventObserver):
    """
    Event observer for Telegram events
    """

    def __init__(self, router: Router, event_name: str) -> None:
        super().__init__()

        self.router: Router = router
        self.event_name: str = event_name
        self.filters: List[Type[BaseFilter]] = []

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

    async def trigger_middleware(
        self, step: MiddlewareStep, event: UpdateType, data: Dict[str, Any], result: Any = None,
    ) -> None:
        """
        Trigger middlewares chain

        :param step:
        :param event:
        :param data:
        :param result:
        :return:
        """
        reverse = step == MiddlewareStep.POST_PROCESS
        recursive = self.event_name == "update" or step == MiddlewareStep.PROCESS

        if self.event_name == "update":
            routers = self.router.chain
        else:
            routers = self.router.chain_head
        for router in routers:
            await router.middleware.trigger(
                step=step,
                event_name=self.event_name,
                event=event,
                data=data,
                result=result,
                reverse=reverse,
            )
            if not recursive:
                break

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

    async def trigger(self, *args: Any, **kwargs: Any) -> AsyncGenerator[Any, None]:
        """
        Propagate event to handlers and stops propagation on first match.
        Handler will be called when all its filters is pass.
        """
        event = args[0]
        await self.trigger_middleware(step=MiddlewareStep.PRE_PROCESS, event=event, data=kwargs)
        for handler in self.handlers:
            result, data = await handler.check(*args, **kwargs)
            if result:
                kwargs.update(data)
                await self.trigger_middleware(
                    step=MiddlewareStep.PROCESS, event=event, data=kwargs
                )
                try:
                    response = await handler.call(*args, **kwargs)
                    await self.trigger_middleware(
                        step=MiddlewareStep.POST_PROCESS,
                        event=event,
                        data=kwargs,
                        result=response,
                    )
                    yield response
                except SkipHandler:
                    continue
                break

    def __call__(
        self, *args: FilterType, **bound_filters: BaseFilter
    ) -> Callable[[CallbackType], CallbackType]:
        """
        Decorator for registering event handlers
        """

        def wrapper(callback: CallbackType) -> CallbackType:
            self.register(callback, *args, **bound_filters)
            return callback

        return wrapper
