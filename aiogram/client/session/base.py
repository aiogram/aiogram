from __future__ import annotations

import abc
import datetime
import json
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Callable,
    ClassVar,
    Optional,
    Type,
    TypeVar,
    Union,
)

from aiogram.utils.exceptions import TelegramAPIError
from aiogram.utils.helper import Default

from ...methods import Response, TelegramMethod
from ...types import UNSET
from ..telegram import PRODUCTION, TelegramAPIServer

if TYPE_CHECKING:  # pragma: no cover
    from ..bot import Bot

T = TypeVar("T")
_JsonLoads = Callable[..., Any]
_JsonDumps = Callable[..., str]


class BaseSession(abc.ABC):
    api: Default[TelegramAPIServer] = Default(PRODUCTION)
    """Telegra Bot API URL patterns"""
    json_loads: Default[_JsonLoads] = Default(json.loads)
    """JSON loader"""
    json_dumps: Default[_JsonDumps] = Default(json.dumps)
    """JSON dumper"""
    default_timeout: ClassVar[float] = 60.0
    """Default timeout"""
    timeout: Default[float] = Default(fget=lambda self: float(self.__class__.default_timeout))
    """Session scope request timeout"""

    @classmethod
    def raise_for_status(cls, response: Response[T]) -> None:
        """
        Check response status

        :param response: Response instance
        """
        if response.ok:
            return
        raise TelegramAPIError(response.description)

    @abc.abstractmethod
    async def close(self) -> None:  # pragma: no cover
        """
        Close client session
        """
        pass

    @abc.abstractmethod
    async def make_request(
        self, bot: Bot, method: TelegramMethod[T], timeout: Optional[int] = UNSET
    ) -> T:  # pragma: no cover
        """
        Make request to Telegram Bot API

        :param bot: Bot instance
        :param method: Method instance
        :param timeout: Request timeout
        :return:
        :raise TelegramApiError:
        """
        pass

    @abc.abstractmethod
    async def stream_content(
        self, url: str, timeout: int, chunk_size: int
    ) -> AsyncGenerator[bytes, None]:  # pragma: no cover
        """
        Stream reader
        """
        yield b""

    def prepare_value(self, value: Any) -> Union[str, int, bool]:
        """
        Prepare value before send
        """
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
        """
        Clean data before send
        """
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
