from __future__ import annotations

import abc
import datetime
import json
from functools import partial
from http import HTTPStatus
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    ClassVar,
    List,
    Optional,
    Type,
    Union,
    cast,
)

from aiogram.exceptions import (
    RestartingTelegram,
    TelegramAPIError,
    TelegramBadRequest,
    TelegramConflictError,
    TelegramEntityTooLarge,
    TelegramForbiddenError,
    TelegramMigrateToChat,
    TelegramNotFound,
    TelegramRetryAfter,
    TelegramServerError,
    TelegramUnauthorizedError,
)
from aiogram.utils.helper import Default

from ...methods import Response, TelegramMethod
from ...methods.base import TelegramType
from ...types import UNSET, TelegramObject
from ..telegram import PRODUCTION, TelegramAPIServer

if TYPE_CHECKING:
    from ..bot import Bot

_JsonLoads = Callable[..., Any]
_JsonDumps = Callable[..., str]
NextRequestMiddlewareType = Callable[
    ["Bot", TelegramMethod[TelegramObject]], Awaitable[Response[TelegramObject]]
]
RequestMiddlewareType = Callable[
    [NextRequestMiddlewareType, "Bot", TelegramMethod[TelegramType]],
    Awaitable[Response[TelegramType]],
]


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

    def __init__(self) -> None:
        self.middlewares: List[RequestMiddlewareType[TelegramObject]] = []

    def check_response(
        self, method: TelegramMethod[TelegramType], status_code: int, content: str
    ) -> Response[TelegramType]:
        """
        Check response status
        """
        json_data = self.json_loads(content)
        response = method.build_response(json_data)
        if HTTPStatus.OK <= status_code <= HTTPStatus.IM_USED and response.ok:
            return response

        description = cast(str, response.description)

        if parameters := response.parameters:
            if parameters.retry_after:
                raise TelegramRetryAfter(
                    method=method, message=description, retry_after=parameters.retry_after
                )
            if parameters.migrate_to_chat_id:
                raise TelegramMigrateToChat(
                    method=method,
                    message=description,
                    migrate_to_chat_id=parameters.migrate_to_chat_id,
                )
        if status_code == HTTPStatus.BAD_REQUEST:
            raise TelegramBadRequest(method=method, message=description)
        if status_code == HTTPStatus.NOT_FOUND:
            raise TelegramNotFound(method=method, message=description)
        if status_code == HTTPStatus.CONFLICT:
            raise TelegramConflictError(method=method, message=description)
        if status_code == HTTPStatus.UNAUTHORIZED:
            raise TelegramUnauthorizedError(method=method, message=description)
        if status_code == HTTPStatus.FORBIDDEN:
            raise TelegramForbiddenError(method=method, message=description)
        if status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE:
            raise TelegramEntityTooLarge(method=method, message=description)
        if status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
            if "restart" in description:
                raise RestartingTelegram(method=method, message=description)
            raise TelegramServerError(method=method, message=description)

        raise TelegramAPIError(
            method=method,
            message=description,
        )

    @abc.abstractmethod
    async def close(self) -> None:  # pragma: no cover
        """
        Close client session
        """
        pass

    @abc.abstractmethod
    async def make_request(
        self, bot: Bot, method: TelegramMethod[TelegramType], timeout: Optional[int] = UNSET
    ) -> TelegramType:  # pragma: no cover
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

    def middleware(
        self, middleware: RequestMiddlewareType[TelegramObject]
    ) -> RequestMiddlewareType[TelegramObject]:
        self.middlewares.append(middleware)
        return middleware

    async def __call__(
        self, bot: Bot, method: TelegramMethod[TelegramType], timeout: Optional[int] = UNSET
    ) -> TelegramType:
        middleware = partial(self.make_request, timeout=timeout)
        for m in reversed(self.middlewares):
            middleware = partial(m, make_request=middleware)  # type: ignore
        return await middleware(bot, method)

    async def __aenter__(self) -> BaseSession:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()
