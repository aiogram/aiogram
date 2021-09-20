from __future__ import annotations

import abc
import secrets
from typing import TYPE_CHECKING, Any, Dict, Generator, Generic, Optional, TypeVar, Union

from pydantic import BaseConfig, BaseModel, Extra, root_validator
from pydantic.generics import GenericModel

from ..types import UNSET, InputFile, ResponseParameters

if TYPE_CHECKING:
    from ..client.bot import Bot

TelegramType = TypeVar("TelegramType", bound=Any)


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


class Response(GenericModel, Generic[TelegramType]):
    ok: bool
    result: Optional[TelegramType] = None
    description: Optional[str] = None
    error_code: Optional[int] = None
    parameters: Optional[ResponseParameters] = None


class TelegramMethod(abc.ABC, BaseModel, Generic[TelegramType]):
    class Config(BaseConfig):
        # use_enum_values = True
        extra = Extra.allow
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        orm_mode = True

    @root_validator(pre=True)
    def remove_unset(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove UNSET from `parse_mode` before fields validation.

        We use UNSET as a sentinel value for `parse_mode` and replace it to real value later.
        It isn't a problem when it's just default value for a model field, but UNSET might be passing to
        a model initialization from `Bot.method_name`, so we must take care of it and
        remove it before fields validation.
        """
        for parse_mode_attribute in {"parse_mode", "explanation_parse_mode"}:
            if parse_mode_attribute in values and values[parse_mode_attribute] is UNSET:
                values.pop(parse_mode_attribute)
        return values

    @property
    @abc.abstractmethod
    def __returning__(self) -> type:  # pragma: no cover
        pass

    @abc.abstractmethod
    def build_request(self, bot: Bot) -> Request:  # pragma: no cover
        pass

    def dict(self, **kwargs: Any) -> Any:
        # override dict of pydantic.BaseModel to overcome exporting request_timeout field
        exclude = kwargs.pop("exclude", set())

        return super().dict(exclude=exclude, **kwargs)

    def build_response(self, data: Dict[str, Any]) -> Response[TelegramType]:
        # noinspection PyTypeChecker
        return Response[self.__returning__](**data)  # type: ignore

    async def emit(self, bot: Bot) -> TelegramType:
        return await bot(self)

    def __await__(self) -> Generator[Any, None, TelegramType]:
        from aiogram.client.bot import Bot

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


def prepare_parse_mode(
    bot: Bot,
    root: Any,
    parse_mode_property: str = "parse_mode",
    entities_property: str = "entities",
) -> None:
    """
    Find and set parse_mode with highest priority.

    Developer can manually set parse_mode for each message (or message-like) object,
    but if parse_mode was unset we should use value from Bot object.

    We can't use None for "unset state", because None itself is the parse_mode option.
    """
    if isinstance(root, list):
        for item in root:
            prepare_parse_mode(
                bot=bot,
                root=item,
                parse_mode_property=parse_mode_property,
                entities_property=entities_property,
            )
    elif root.get(parse_mode_property, UNSET) is UNSET:
        if bot.parse_mode and root.get(entities_property, None) is None:
            root[parse_mode_property] = bot.parse_mode
        else:
            root[parse_mode_property] = None
