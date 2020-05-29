from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, Generic, TypeVar

T = TypeVar("T")


class BaseMiddleware(ABC, Generic[T]):
    @abstractmethod
    async def __call__(
        self,
        handler: Callable[[T, Dict[str, Any]], Awaitable[Any]],
        event: T,
        data: Dict[str, Any],
    ) -> Any:  # pragma: no cover
        pass
