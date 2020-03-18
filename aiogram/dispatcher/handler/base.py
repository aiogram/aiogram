from abc import ABC, abstractmethod
from typing import (
    Optional,
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    TypeVar,
    cast,
)

from aiogram import Bot
from aiogram.api.types import Update

T = TypeVar("T")


class BaseHandlerMixin(Generic[T]):
    if TYPE_CHECKING:  # pragma: no cover
        event: T
        data: Dict[str, Any]


class BaseHandler(BaseHandlerMixin[T], ABC):
    """
    Base class for all class-based handlers
    """

    def __init__(self, event: T, **kwargs: Any) -> None:
        self.event: T = event
        self.data: Dict[str, Any] = kwargs

    @property
    def bot(self) -> Optional[Bot]:
        if "bot" in self.data:
            # TODO: remove cast
            return cast(Bot, self.data["bot"])
        return Bot.get_current()

    @property
    def update(self) -> Update:
        # TODO: remove cast
        return cast(Update, self.data["update"])

    @abstractmethod
    async def handle(self) -> Any:  # pragma: no cover
        pass

    def __await__(self) -> Any:
        return self.handle().__await__()
