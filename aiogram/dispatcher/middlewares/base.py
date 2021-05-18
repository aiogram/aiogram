from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, Generic, TypeVar

T = TypeVar("T")


class BaseMiddleware(ABC, Generic[T]):
    """
    Generic middleware class
    """

    @abstractmethod
    async def __call__(
        self,
        handler: Callable[[T, Dict[str, Any]], Awaitable[Any]],
        event: T,
        data: Dict[str, Any],
    ) -> Any:  # pragma: no cover
        """
        Execute middleware

        :param handler: Wrapped handler in middlewares chain
        :param event: Incoming event (Subclass of :class:`aiogram.types.base.TelegramObject`)
        :param data: Contextual data. Will be mapped to handler arguments
        :return: :class:`Any`
        """
        pass
