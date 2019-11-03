import abc
import io
from typing import Any, Dict, Generic, Optional, Type, TypeVar, Union

from pydantic import BaseConfig, BaseModel, Extra
from pydantic.generics import GenericModel

from aiogram.api.types import InputFile, ResponseParameters

T = TypeVar("T")


class Request(BaseModel):
    method: str

    data: Dict[str, Optional[Any]]
    files: Optional[Dict[str, Union[io.BytesIO, bytes, InputFile]]]

    class Config(BaseConfig):
        arbitrary_types_allowed = True


class Response(ResponseParameters, GenericModel, Generic[T]):
    ok: bool
    result: Optional[T] = None
    description: Optional[str] = None
    error_code: Optional[int] = None


class TelegramMethod(abc.ABC, BaseModel, Generic[T]):
    class Config(BaseConfig):
        use_enum_values = True
        extra = Extra.allow
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        # orm_mode = True

    @property
    @abc.abstractmethod
    def __returning__(self) -> Type:
        pass

    @abc.abstractmethod
    def build_request(self) -> Request:
        pass

    def build_response(self, data: Dict[str, Any]) -> Response[T]:
        # noinspection PyTypeChecker
        return Response[self.__returning__](**data)  # type: ignore
