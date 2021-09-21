from __future__ import annotations

from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, Type, TypeVar, Union
from uuid import UUID

from magic_filter import MagicFilter
from pydantic import BaseModel

from aiogram.dispatcher.filters import BaseFilter
from aiogram.types import CallbackQuery

T = TypeVar("T", bound="CallbackData")

MAX_CALLBACK_LENGTH: int = 64


class CallbackDataException(Exception):
    pass


class CallbackData(BaseModel):
    if TYPE_CHECKING:
        sep: str
        prefix: str

    def __init_subclass__(cls, **kwargs: Any) -> None:
        if "prefix" not in kwargs:
            raise ValueError(
                f"prefix required, usage example: "
                f"`class {cls.__name__}(CallbackData, prefix='my_callback'): ...`"
            )
        cls.sep = kwargs.pop("sep", ":")
        cls.prefix = kwargs.pop("prefix")
        if cls.sep in cls.prefix:
            raise ValueError(
                f"Separator symbol {cls.sep!r} can not be used inside prefix {cls.prefix!r}"
            )

    def _encode_value(self, key: str, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, Enum):
            return str(value.value)
        if isinstance(value, (int, str, float, Decimal, Fraction, UUID)):
            return str(value)
        raise ValueError(
            f"Attribute {key}={value!r} of type {type(value).__name__!r}"
            f" can not be packed to callback data"
        )

    def pack(self) -> str:
        result = [self.prefix]
        for key, value in self.dict().items():
            encoded = self._encode_value(key, value)
            if self.sep in encoded:
                raise ValueError(
                    f"Separator symbol {self.sep!r} can not be used in value {key}={encoded!r}"
                )
            result.append(encoded)
        callback_data = self.sep.join(result)
        if len(callback_data.encode()) > MAX_CALLBACK_LENGTH:
            raise ValueError(
                f"Resulted callback data is too long! len({callback_data!r}.encode()) > {MAX_CALLBACK_LENGTH}"
            )
        return callback_data

    @classmethod
    def unpack(cls: Type[T], value: str) -> T:
        prefix, *parts = value.split(cls.sep)
        names = cls.__fields__.keys()
        if len(parts) != len(names):
            raise TypeError(
                f"Callback data {cls.__name__!r} takes {len(names)} arguments but {len(parts)} were given"
            )
        if prefix != cls.prefix:
            raise ValueError(f"Bad prefix ({prefix!r} != {cls.prefix!r})")
        payload = {}
        for k, v in zip(names, parts):  # type: str, Optional[str]
            if field := cls.__fields__.get(k):
                if v == "" and not field.required:
                    v = None
            payload[k] = v
        return cls(**payload)

    @classmethod
    def filter(cls, rule: Optional[MagicFilter] = None) -> CallbackQueryFilter:
        return CallbackQueryFilter(callback_data=cls, rule=rule)

    class Config:
        use_enum_values = True


class CallbackQueryFilter(BaseFilter):
    callback_data: Type[CallbackData]
    rule: Optional[MagicFilter] = None

    async def __call__(self, query: CallbackQuery) -> Union[Literal[False], Dict[str, Any]]:
        if not isinstance(query, CallbackQuery) or not query.data:
            return False
        try:
            callback_data = self.callback_data.unpack(query.data)
        except (TypeError, ValueError):
            return False

        if self.rule is None or self.rule.resolve(callback_data):
            return {"callback_data": callback_data}
        return False

    class Config:
        arbitrary_types_allowed = True
