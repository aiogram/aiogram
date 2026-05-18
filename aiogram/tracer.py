from __future__ import annotations

import functools
import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from contextvars import ContextVar
from types import TracebackType
from typing import TYPE_CHECKING, ParamSpec, TypeVar

from aiogram.dispatcher.event.bases import MiddlewareEventType, MiddlewareType

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import HandlerObject
    from aiogram.types import TelegramObject


SPAN_MANAGER_TYPE = AbstractAsyncContextManager[None] | None


class AbstractTracer(ABC):
    @abstractmethod
    def get_middleware_span_manager(
        self, middleware: MiddlewareType[MiddlewareEventType]
    ) -> SPAN_MANAGER_TYPE:
        """
        Method for getting manager that will be used to wrap each middleware.
        """

    @abstractmethod
    def get_handler_span_manager(self, handler: HandlerObject) -> SPAN_MANAGER_TYPE:
        """
        Method for getting manager that will be used to wrap handler.
        """

    @abstractmethod
    def get_trigger_span_manager(self, event: TelegramObject) -> SPAN_MANAGER_TYPE:
        """
        Method for getting manager that will be used to wrap full update processing flow
        (e.g. routing, filtering, etc).
        """

    @abstractmethod
    def get_filter_span_manager(self, handler: HandlerObject) -> SPAN_MANAGER_TYPE:
        """
        Method for getting manager that will be used to wrap filter check for handler,
        both handler and observer filters. In the case of observer-level filters,
        ``HandlerObject`` with dummy callback(lambda function) will be passed.
        """


T = TypeVar("T")


async def execute_with_tracing(manager: SPAN_MANAGER_TYPE, func: Awaitable[T]) -> T:
    if manager is not None:
        async with manager:
            return await func
    return await func


logger = logging.getLogger(__name__)


class SpanProxy:
    def __init__(self, span: AbstractAsyncContextManager[None]):
        self.span = span
        self.have_error_during_enter = False

    async def __aenter__(self) -> None:
        try:
            return await self.span.__aenter__()
        except Exception:
            logger.exception("Exception during entering span.")
            self.have_error_during_enter = True

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        if self.have_error_during_enter:
            return None
        try:
            return await self.span.__aexit__(exc_type, exc_value, traceback)
        except Exception:
            logger.exception("Exception during exiting span.")
        return None


P = ParamSpec("P")


def safe_span_manager(
    name: str,
) -> Callable[[Callable[P, SPAN_MANAGER_TYPE]], Callable[P, SPAN_MANAGER_TYPE]]:
    def decorator(func: Callable[P, SPAN_MANAGER_TYPE]) -> Callable[P, SPAN_MANAGER_TYPE]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> SPAN_MANAGER_TYPE:
            try:
                span = func(*args, **kwargs)
                return SpanProxy(span) if span else None
            except Exception:
                logger.exception(f"Exception during initialization of {name} span manager.")
                return None

        return wrapper

    return decorator


class TracerProxy(AbstractTracer):
    def __init__(self, tracer: AbstractTracer) -> None:
        self.tracer = tracer

    @safe_span_manager("middleware")
    def get_middleware_span_manager(
        self, middleware: MiddlewareType[MiddlewareEventType]
    ) -> SPAN_MANAGER_TYPE:
        return self.tracer.get_middleware_span_manager(middleware)

    @safe_span_manager("handler")
    def get_handler_span_manager(self, handler: HandlerObject) -> SPAN_MANAGER_TYPE:
        return self.tracer.get_handler_span_manager(handler)

    @safe_span_manager("trigger")
    def get_trigger_span_manager(self, event: TelegramObject) -> SPAN_MANAGER_TYPE:
        return self.tracer.get_trigger_span_manager(event)

    @safe_span_manager("filter")
    def get_filter_span_manager(self, handler: HandlerObject) -> SPAN_MANAGER_TYPE:
        return self.tracer.get_filter_span_manager(handler)


tracer: ContextVar[AbstractTracer | None] = ContextVar("tracer", default=None)
