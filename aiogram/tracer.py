from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram import BaseMiddleware
    from aiogram.dispatcher.event.handler import CallbackType, HandlerObject
    from aiogram.types import TelegramObject


class AbstractTracer(ABC):
    @abstractmethod
    def get_middleware_span_manager(
        self, middleware: BaseMiddleware
    ) -> AbstractAsyncContextManager | None:
        pass

    @abstractmethod
    def get_handler_span_manager(
        self, handler: HandlerObject
    ) -> AbstractAsyncContextManager | None:
        pass

    @abstractmethod
    def get_trigger_span_manager(
        self, event: TelegramObject
    ) -> AbstractAsyncContextManager | None:
        pass

    @abstractmethod
    def get_filter_span_manager(
        self, handler: HandlerObject
    ) -> AbstractAsyncContextManager | None:
        pass


tracer: ContextVar[AbstractTracer | None] = ContextVar("tracer", default=None)
