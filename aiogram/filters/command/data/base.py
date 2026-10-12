import re
from typing import Any, ClassVar

from pydantic import BaseModel
from typing_extensions import Self

from aiogram.filters.command.data.codecs import ArgsCodec, Base64Codec, PositionalCodec

PAYLOAD_MAX_LEN = 64


class DeeplinkDataException(Exception):
    """Raised when :class:`DeeplinkData` cannot be packed or unpacked."""


class DeeplinkData(BaseModel):
    """
    Base class for typed deeplink payload.
    """

    __codec__: ClassVar[ArgsCodec] = PositionalCodec(sep="_")
    __prefix__: ClassVar[str | None] = None

    def __init_subclass__(
        cls,
        codec: ArgsCodec | None = None,
        prefix: str | None = None,
        encoded: bool = False,
        **kwargs: Any,
    ) -> None:
        if codec is not None or encoded:
            inner = codec or PositionalCodec(sep="_")
            cls.__codec__ = Base64Codec(inner) if encoded else inner
        if prefix is not None:
            cls.__prefix__ = prefix

        super().__init_subclass__(**kwargs)

    def pack(self) -> str:
        """
        Serialize to payload string using the class-level prefix and codec.

        :raises DeeplinkDataException: If prefix is missing or payload exceeds 64 bytes.
        """
        prefix = self.__prefix__
        if not prefix:
            raise DeeplinkDataException("prefix is required — set prefix= on the class")
        args = self.__codec__.encode(self)
        payload = f"{prefix}{args}" if args else prefix
        if re.search(r"[^A-Za-z0-9_\-]", payload):
            raise DeeplinkDataException(
                f"Payload {payload!r} contains characters not allowed in deeplink. "
                f"Use Base64Codec."
            )
        if len(payload.encode()) > PAYLOAD_MAX_LEN:
            raise DeeplinkDataException(
                f"Resulted payload is too long! len({payload!r}.encode()) > {PAYLOAD_MAX_LEN}. "
            )
        return payload

    @classmethod
    def unpack(cls, payload: str) -> Self:
        """
        Deserialize from payload string using the class-level prefix and codec.

        :param payload: Full payload string (e.g. ``"order42SALE"``).
        :raises DeeplinkDataException: If payload does not match expected prefix.
        """
        prefix = cls.__prefix__

        if prefix:
            if payload == prefix:
                raw = ""
            elif payload.startswith(prefix):
                raw = payload[len(prefix) :]
            else:
                raise DeeplinkDataException(
                    f"Bad prefix ({payload!r} does not start with {prefix!r})"
                )
        else:
            raw = payload

        return cls.__codec__.decode(raw, cls)
