from __future__ import annotations

import abc
import secrets
from typing import TYPE_CHECKING, Any, Dict, Generator, Generic, Optional, TypeVar, Union

from pydantic import BaseConfig, BaseModel, Extra
from pydantic.generics import GenericModel

from ..types import InputFile, ResponseParameters

if TYPE_CHECKING:  # pragma: no cover
    from ..client.bot import Bot

T = TypeVar("T")
DEFAULT_REQUEST_TIMEOUT_SECONDS = 60.0


class Request(BaseModel):
    method: str

    data: Dict[str, Optional[Any]]
    files: Optional[Dict[str, InputFile]]

    class Config(BaseConfig):
        arbitrary_types_allowed = True

    def render_webhook_request(self) -> Dict[str, Any]:
        return {
            "method": self.method,
            **{key: value for key, value in self.data.items() if value is not None},
        }


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
    def __returning__(self) -> type:  # pragma: no cover
        pass

    @abc.abstractmethod
    def build_request(self) -> Request:  # pragma: no cover
        pass

    request_timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS

    def dict(self, **kwargs: Any) -> Any:
        # override dict of pydantic.BaseModel to overcome exporting request_timeout field
        exclude = kwargs.pop("exclude", set())
        if isinstance(exclude, set):
            exclude.add("request_timeout")

        return super().dict(exclude=exclude, **kwargs)

    def build_response(self, data: Dict[str, Any]) -> Response[T]:
        # noinspection PyTypeChecker
        return Response[self.__returning__](**data)  # type: ignore

    async def emit(self, bot: Bot) -> T:
        return await bot(self)

    def __await__(self) -> Generator[Any, None, T]:
        from aiogram.api.client.bot import Bot

        bot = Bot.get_current(no_error=False)
        return self.emit(bot).__await__()


def prepare_file(name: str, value: Any, data: Dict[str, Any], files: Dict[str, Any]) -> None:
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


def prepare_input_media(data: Dict[str, Any], files: Dict[str, InputFile]) -> None:
    for input_media in data.get("media", []):  # type: Dict[str, Union[str, InputFile]]
        if (
            "media" in input_media
            and input_media["media"]
            and isinstance(input_media["media"], InputFile)
        ):
            tag = secrets.token_urlsafe(10)
            files[tag] = input_media.pop("media")  # type: ignore
            input_media["media"] = f"attach://{tag}"


def prepare_media_file(data: Dict[str, Any], files: Dict[str, InputFile]) -> None:
    if (
        data["media"]
        and "media" in data["media"]
        and isinstance(data["media"]["media"], InputFile)
    ):
        tag = secrets.token_urlsafe(10)
        files[tag] = data["media"].pop("media")
        data["media"]["media"] = f"attach://{tag}"


def prepare_parse_mode(root: Any) -> None:
    if isinstance(root, list):
        for item in root:
            prepare_parse_mode(item)
        return

    if root.get("parse_mode"):
        return

    from ..client.bot import Bot

    bot = Bot.get_current(no_error=True)
    if bot and bot.parse_mode:
        root["parse_mode"] = bot.parse_mode
        return
    return
