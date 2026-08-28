import types
import typing
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import Any, Protocol, TypeVar, runtime_checkable
from uuid import UUID

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from aiogram.utils.payload import decode_payload, encode_payload

T = TypeVar("T", bound=BaseModel)

_UNION_TYPES = {typing.Union, types.UnionType}


@runtime_checkable
class ArgsCodec(Protocol):
    def encode(self, model: BaseModel) -> str: ...
    def decode(self, args: str, model_cls: type[T]) -> T: ...


class PositionalCodec(ArgsCodec):
    """
    Serializes fields as positional values joined by :code:`sep`.

    :param sep: separator between field values
    """

    def __init__(self, sep: str = " ") -> None:
        self.sep = sep

    def encode(self, model: BaseModel) -> str:
        parts: list[str] = []
        for name, value in model.model_dump(mode="python").items():
            encoded = _encode_value(name, value)
            if self.sep in encoded:
                raise ValueError(
                    f"Separator {self.sep!r} found in field {name!r}={encoded!r}. "
                    f"Use a different sep or Base64Codec."
                )
            parts.append(encoded)
        while parts and parts[-1] == "":
            parts.pop()
        return self.sep.join(parts)

    def decode(self, args: str, model_cls: type[T]) -> T:
        parts = args.split(self.sep) if args else []
        model_fields = model_cls.model_fields

        if len(parts) > len(model_fields):
            raise ValueError(
                f"Args has {len(parts)} segments but "
                f"{model_cls.__name__!r} has {len(model_fields)} fields"
            )

        kwargs: dict[str, Any] = {
            name: _decode_field(parts[i] if i < len(parts) else "", field)
            for i, (name, field) in enumerate(model_fields.items())
        }
        return model_cls(**kwargs)


class NamedCodec(ArgsCodec):
    """
    Serializes fields as :code:`key=value` pairs joined by :code:`sep`. Order-independent.

    :param sep: separator between pairs
    :param kv_sep: separator between key and value
    """

    def __init__(self, sep: str = " ", kv_sep: str = "=") -> None:
        self.sep = sep
        self.kv_sep = kv_sep

    def encode(self, model: BaseModel) -> str:
        parts: list[str] = []
        for name, value in model.model_dump(mode="python").items():
            encoded = _encode_value(name, value)
            if encoded == "":
                continue
            parts.append(f"{name}{self.kv_sep}{encoded}")
        return self.sep.join(parts)

    def decode(self, args: str, model_cls: type[T]) -> T:
        kwargs: dict[str, Any] = {}
        if args:
            for token in args.split(self.sep):
                if self.kv_sep not in token:
                    raise ValueError(f"Token {token!r} is not a valid key{self.kv_sep}value pair")
                key, _, value = token.partition(self.kv_sep)
                key = key.strip()
                field = model_cls.model_fields.get(key)
                if field is not None:
                    value = _decode_field(value, field)
                kwargs[key] = value

        for name, field in model_cls.model_fields.items():
            if name not in kwargs:
                kwargs[name] = _decode_field("", field)
        return model_cls(**kwargs)


class Base64Codec:
    """
    Wraps any :class:`ArgsCodec` with base64url encoding of the entire payload.
    Makes the payload deeplink-safe regardless of field content.

    :param inner: The codec to wrap. Defaults to :class:`PositionalCodec` with ``sep="_"``.
    """

    def __init__(self, inner: ArgsCodec | None = None) -> None:
        self.inner: ArgsCodec = inner if inner is not None else PositionalCodec(sep="_")

    def encode(self, model: BaseModel) -> str:
        return encode_payload(self.inner.encode(model))

    def decode(self, args: str, model_cls: type[T]) -> T:
        return self.inner.decode(decode_payload(args) if args else "", model_cls)


def _encode_value(key: str, value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, UUID):
        return value.hex
    if isinstance(value, bool):
        return str(int(value))
    if isinstance(value, (int, str, float, Decimal, Fraction)):
        return str(value)
    raise ValueError(
        f"Attribute {key}={value!r} of type {type(value).__name__!r} can not be packed to payload"
    )


def _decode_field(raw: str, field: FieldInfo) -> Any:
    if not raw:
        if field.default is not PydanticUndefined and field.default != "":
            return field.default
        if type(None) in typing.get_args(field.annotation):
            return None
        return ""
    return raw
