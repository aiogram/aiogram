from __future__ import annotations

import abc
import datetime
import json
from types import TracebackType
from typing import Any, AsyncGenerator, Callable, Optional, Type, TypeVar, Union

from aiogram.utils.exceptions import TelegramAPIError

from ...methods import Response, TelegramMethod
from ..telegram import PRODUCTION, TelegramAPIServer

T = TypeVar("T")
PT = TypeVar("PT")


class BaseSession(abc.ABC):
    _api: TelegramAPIServer
    _json_loads: Callable[..., Any]
    _json_dumps: Callable[..., str]

    @property
    def api(self) -> TelegramAPIServer:  # pragma: no cover
        if not hasattr(self, "_api"):
            return PRODUCTION
        return self._api

    @api.setter
    def api(self, value: TelegramAPIServer) -> None:  # pragma: no cover
        self._api = value

    @property
    def json_loads(self) -> Callable[..., Any]:  # pragma: no cover
        if not hasattr(self, "_json_loads"):
            return json.loads
        return self._json_loads

    @json_loads.setter
    def json_loads(self, value: Callable[..., Any]) -> None:  # pragma: no cover
        self._json_loads = value  # type: ignore

    @property
    def json_dumps(self) -> Callable[..., str]:  # pragma: no cover
        if not hasattr(self, "_json_dumps"):
            return json.dumps
        return self._json_dumps

    @json_dumps.setter
    def json_dumps(self, value: Callable[..., str]) -> None:  # pragma: no cover
        self._json_dumps = value  # type: ignore

    @classmethod
    def raise_for_status(cls, response: Response[T]) -> None:
        if response.ok:
            return
        raise TelegramAPIError(response.description)

    @abc.abstractmethod
    async def close(self) -> None:  # pragma: no cover
        pass

    @abc.abstractmethod
    async def make_request(self, token: str, method: TelegramMethod[T]) -> T:  # pragma: no cover
        pass

    @abc.abstractmethod
    async def stream_content(
        self, url: str, timeout: int, chunk_size: int
    ) -> AsyncGenerator[bytes, None]:  # pragma: no cover
        yield b""

    def prepare_value(self, value: Any) -> Union[str, int, bool]:
        if isinstance(value, str):
            return value
        if isinstance(value, (list, dict)):
            return self.json_dumps(self.clean_json(value))
        if isinstance(value, datetime.timedelta):
            now = datetime.datetime.now()
            return str(round((now + value).timestamp()))
        if isinstance(value, datetime.datetime):
            return str(round(value.timestamp()))
        else:
            return str(value)

    def clean_json(self, value: Any) -> Any:
        if isinstance(value, list):
            return [self.clean_json(v) for v in value if v is not None]
        elif isinstance(value, dict):
            return {k: self.clean_json(v) for k, v in value.items() if v is not None}
        return value

    async def __aenter__(self) -> BaseSession:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()
