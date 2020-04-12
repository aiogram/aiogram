from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional

from aiogram.dispatcher.middlewares.types import MiddlewareStep, UpdateType

if TYPE_CHECKING:  # pragma: no cover
    from aiogram.dispatcher.middlewares.manager import MiddlewareManager


class AbstractMiddleware(ABC):
    """
    Abstract class for middleware.
    """

    def __init__(self) -> None:
        self._manager: Optional[MiddlewareManager] = None

    @property
    def manager(self) -> MiddlewareManager:
        """
        Instance of MiddlewareManager
        """
        if self._manager is None:
            raise RuntimeError("Middleware is not configured!")
        return self._manager

    def setup(self, manager: MiddlewareManager, _stack_level: int = 1) -> AbstractMiddleware:
        """
        Mark middleware as configured

        :param manager:
        :param _stack_level:
        :return:
        """
        if self.configured:
            return manager.setup(self, _stack_level=_stack_level + 1)

        self._manager = manager
        return self

    @property
    def configured(self) -> bool:
        """
        Check middleware is configured

        :return:
        """
        return bool(self._manager)

    @abstractmethod
    async def trigger(
        self,
        step: MiddlewareStep,
        event_name: str,
        event: UpdateType,
        data: Dict[str, Any],
        result: Any = None,
    ) -> Any:  # pragma: no cover
        pass
