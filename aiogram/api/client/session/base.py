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


class BaseSession(abc.ABC):
    def __init__(
        self,
        api: Optional[TelegramAPIServer] = None,
        json_loads: Optional[Callable[..., str]] = None,
        json_dumps: Optional[Callable[..., str]] = None,
    ) -> None:
        if api is None:
            api = PRODUCTION
        if json_loads is None:
            json_loads = json.loads
        if json_dumps is None:
            json_dumps = json.dumps

        self.api = api
        self.json_loads = json_loads
        self.json_dumps = json_dumps

    def raise_for_status(self, response: Response[T]) -> None:
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
