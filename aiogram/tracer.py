from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from contextvars import ContextVar
from typing import TYPE_CHECKING

from aiogram.dispatcher.event.bases import MiddlewareEventType, MiddlewareType

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import HandlerObject
    from aiogram.types import TelegramObject


class AbstractTracer(ABC):
    @abstractmethod
    def get_middleware_span_manager(
        self, middleware: MiddlewareType[MiddlewareEventType]
    ) -> AbstractAsyncContextManager[None] | None:
        pass

    @abstractmethod
    def get_handler_span_manager(
        self, handler: HandlerObject
    ) -> AbstractAsyncContextManager[None] | None:
        pass

    @abstractmethod
    def get_trigger_span_manager(
        self, event: TelegramObject
    ) -> AbstractAsyncContextManager[None] | None:
        pass

    @abstractmethod
    def get_filter_span_manager(
        self, handler: HandlerObject
    ) -> AbstractAsyncContextManager[None] | None:
        pass


tracer: ContextVar[AbstractTracer | None] = ContextVar("tracer", default=None)
