from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generator,
    Generic,
    Optional,
    TypeVar,
    Union,
)

import msgspec

from aiogram.types import *  # noqa

from ..types import InputFile, ResponseParameters

if TYPE_CHECKING:
    from ..client.bot import Bot

TelegramType = TypeVar("TelegramType", bound=Any)


class Request(msgspec.Struct, weakref=True):
    method: str

    data: Dict[str, Optional[Any]]
    files: Optional[Dict[str, InputFile]]


class Response(msgspec.Struct, Generic[TelegramType], weakref=True, kw_only=True):
    ok: bool
    result: Optional[Union[Any, None]] = None
    description: Optional[str] = None
    error_code: Optional[int] = None
    parameters: Optional[ResponseParameters] = None


class TelegramMethod(
    msgspec.Struct,
    Generic[TelegramType],
    omit_defaults=True,
    weakref=True,
    kw_only=True,
    forbid_unknown_fields=False,
):
    method: str = msgspec.UNSET

    @property
    @abstractmethod
    def __returning__(self) -> type:  # pragma: no cover
        pass

    @property
    @abstractmethod
    def __api_method__(self) -> str:
        pass

    def build_response(self, data: Union[str, bytes, Dict[str, Any]]) -> Response[TelegramType]:
        # noinspection PyTypeChecker
        if isinstance(data, (bytes, str)):
            data = msgspec.json.decode(data)
        if "result" in data:
            data["result"] = msgspec.from_builtins(data["result"], type=self.__returning__)
        return msgspec.from_builtins(data, type=Response)

    async def emit(self, bot: Bot) -> TelegramType:
        return await bot(self)

    as_ = emit

    def __await__(self) -> Generator[Any, None, TelegramType]:
        from aiogram.client.bot import Bot

        bot = Bot.get_current(no_error=False)
        return self.emit(bot).__await__()
