from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Generator,
    Generic,
    Optional,
    TypeVar,
)

from pydantic import BaseModel

from ..types import InputFile, ResponseParameters
from ..types.base import MutableTelegramObject

if TYPE_CHECKING:
    from ..client.bot import Bot

TelegramType = TypeVar("TelegramType", bound=Any)


class Request(BaseModel):
    method: str

    data: Dict[str, Optional[Any]]
    files: Optional[Dict[str, InputFile]]


class Response(BaseModel, Generic[TelegramType]):
    ok: bool
    result: Optional[TelegramType] = None
    description: Optional[str] = None
    error_code: Optional[int] = None
    parameters: Optional[ResponseParameters] = None


class TelegramMethod(MutableTelegramObject, Generic[TelegramType], ABC):
    if TYPE_CHECKING:
        __returning__: ClassVar[type]
        __api_method__: ClassVar[str]
    else:

        @property
        @abstractmethod
        def __returning__(self) -> type:
            pass

        @property
        @abstractmethod
        def __api_method__(self) -> str:
            pass

    async def emit(self, bot: Bot) -> TelegramType:
        return await bot(self)

    def __await__(self) -> Generator[Any, None, TelegramType]:
        bot = self._bot
        if not bot:
            raise RuntimeError(
                "This method is not mounted to a any bot instance, please call it explicilty "
                "with bot instance `await bot(method)`\n"
                "or mount method to a bot instance `method.as_(bot)` "
                "and then call it `await method()`"
            )
        return self.emit(bot).__await__()
