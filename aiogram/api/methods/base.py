from __future__ import annotations

import abc
import secrets
from typing import TYPE_CHECKING, Any, Dict, Generic, Optional, Type, TypeVar

from pydantic import BaseConfig, BaseModel, Extra
from pydantic.generics import GenericModel

from ..types import InputFile, ResponseParameters

if TYPE_CHECKING:  # pragma: no cover
    from ..client.bot import Bot

T = TypeVar("T")


class Request(BaseModel):
    method: str

    data: Dict[str, Optional[Any]]
    files: Optional[Dict[str, InputFile]]

    class Config(BaseConfig):
        arbitrary_types_allowed = True


class Response(ResponseParameters, GenericModel, Generic[T]):
    ok: bool
    result: Optional[T] = None
    description: Optional[str] = None
    error_code: Optional[int] = None


class TelegramMethod(abc.ABC, BaseModel, Generic[T]):
    class Config(BaseConfig):
        # use_enum_values = True
        extra = Extra.allow
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        orm_mode = True

    @property
    @abc.abstractmethod
    def __returning__(self) -> Type:  # pragma: no cover
        pass

    @abc.abstractmethod
    def build_request(self) -> Request:  # pragma: no cover
        pass

    def build_response(self, data: Dict[str, Any]) -> Response[T]:
        # noinspection PyTypeChecker
        return Response[self.__returning__](**data)  # type: ignore

    def prepare_file(self, name: str, value: Any, data: Dict[str, Any], files: Dict[str, Any]):
        if not value:
            return
        if name == "thumb":
            tag = secrets.token_urlsafe(10)
            files[tag] = value
            data["thumb"] = f"attach://{tag}"
        elif isinstance(value, InputFile):
            files[name] = value
        else:
            data[name] = value

    def prepare_parse_mode(self, root: Any) -> None:
        if isinstance(root, list):
            for item in root:
                self.prepare_parse_mode(item)
            return

        if "parse_mode" not in root:
            return

        from ..client.bot import Bot

        bot = Bot.get_current(no_error=True)
        if bot and bot.parse_mode:
            root["parse_mode"] = bot.parse_mode
            return
        return

    async def emit(self, bot: Bot) -> T:
        return await bot.emit(self)

    def __await__(self):
        from aiogram.api.client.bot import Bot

        bot = Bot.get_current(no_error=False)
        return self.emit(bot).__await__()
