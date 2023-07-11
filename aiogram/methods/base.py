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

from pydantic import BaseModel, ConfigDict
from pydantic.functional_validators import model_validator

from aiogram.client.context_controller import BotContextController

from ..types import InputFile, ResponseParameters
from ..types.base import UNSET_TYPE

if TYPE_CHECKING:
    from ..client.bot import Bot

TelegramType = TypeVar("TelegramType", bound=Any)


class Request(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    method: str

    data: Dict[str, Optional[Any]]
    files: Optional[Dict[str, InputFile]]


class Response(BaseModel, Generic[TelegramType]):
    ok: bool
    result: Optional[TelegramType] = None
    description: Optional[str] = None
    error_code: Optional[int] = None
    parameters: Optional[ResponseParameters] = None


class TelegramMethod(BotContextController, BaseModel, Generic[TelegramType], ABC):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    @model_validator(mode="before")
    @classmethod
    def remove_unset(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove UNSET before fields validation.

        We use UNSET as a sentinel value for `parse_mode` and replace it to real value later.
        It isn't a problem when it's just default value for a model field,
        but UNSET might be passing to a model initialization from `Bot.method_name`,
        so we must take care of it and remove it before fields validation.
        """
        return {k: v for k, v in values.items() if not isinstance(v, UNSET_TYPE)}

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
