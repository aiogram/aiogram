from __future__ import annotations

import abc
import datetime
import json
import secrets
from enum import Enum
from http import HTTPStatus
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    Final,
    Optional,
    Type,
    cast,
)

from pydantic import ValidationError

from aiogram.exceptions import (
    ClientDecodeError,
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

from ...methods import Response, TelegramMethod
from ...methods.base import TelegramType
from ...types import UNSET_PARSE_MODE, InputFile
from ...types.base import UNSET_DISABLE_WEB_PAGE_PREVIEW, UNSET_PROTECT_CONTENT
from ..telegram import PRODUCTION, TelegramAPIServer
from .middlewares.manager import RequestMiddlewareManager

if TYPE_CHECKING:
    from ..bot import Bot

_JsonLoads = Callable[..., Any]
_JsonDumps = Callable[..., str]

DEFAULT_TIMEOUT: Final[float] = 60.0


class BaseSession(abc.ABC):
    """
    This is base class for all HTTP sessions in aiogram.

    If you want to create your own session, you must inherit from this class.
    """

    def __init__(
        self,
        api: TelegramAPIServer = PRODUCTION,
        json_loads: _JsonLoads = json.loads,
        json_dumps: _JsonDumps = json.dumps,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """

        :param api: Telegram Bot API URL patterns
        :param json_loads: JSON loader
        :param json_dumps: JSON dumper
        :param timeout: Session scope request timeout
        """
        self.api = api
        self.json_loads = json_loads
        self.json_dumps = json_dumps
        self.timeout = timeout

        self.middleware = RequestMiddlewareManager()

    def check_response(
        self, bot: Bot, method: TelegramMethod[TelegramType], status_code: int, content: str
    ) -> Response[TelegramType]:
        """
        Check response status
        """
        try:
            json_data = self.json_loads(content)
        except Exception as e:
            # Handled error type can't be classified as specific error
            # in due to decoder can be customized and raise any exception

            raise ClientDecodeError("Failed to decode object", e, content)

        try:
            response_type = Response[method.__returning__]  # type: ignore
            response = response_type.model_validate(json_data, context={"bot": bot})
        except ValidationError as e:
            raise ClientDecodeError("Failed to deserialize object", e, json_data)

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
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: Optional[int] = None,
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
        self,
        url: str,
        headers: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes, None]:  # pragma: no cover
        """
        Stream reader
        """
        yield b""

    def prepare_value(
        self,
        value: Any,
        bot: Bot,
        files: Dict[str, Any],
        _dumps_json: bool = True,
    ) -> Any:
        """
        Prepare value before send
        """
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if value is UNSET_PARSE_MODE:
            return self.prepare_value(
                bot.parse_mode, bot=bot, files=files, _dumps_json=_dumps_json
            )
        if value is UNSET_DISABLE_WEB_PAGE_PREVIEW:
            return self.prepare_value(
                bot.disable_web_page_preview, bot=bot, files=files, _dumps_json=_dumps_json
            )
        if value is UNSET_PROTECT_CONTENT:
            return self.prepare_value(
                bot.protect_content, bot=bot, files=files, _dumps_json=_dumps_json
            )
        if isinstance(value, InputFile):
            key = secrets.token_urlsafe(10)
            files[key] = value
            return f"attach://{key}"
        if isinstance(value, dict):
            value = {
                key: prepared_item
                for key, item in value.items()
                if (
                    prepared_item := self.prepare_value(
                        item, bot=bot, files=files, _dumps_json=False
                    )
                )
                is not None
            }
            if _dumps_json:
                return self.json_dumps(value)
            return value
        if isinstance(value, list):
            value = [
                prepared_item
                for item in value
                if (
                    prepared_item := self.prepare_value(
                        item, bot=bot, files=files, _dumps_json=False
                    )
                )
                is not None
            ]
            if _dumps_json:
                return self.json_dumps(value)
            return value
        if isinstance(value, datetime.timedelta):
            now = datetime.datetime.now()
            return str(round((now + value).timestamp()))
        if isinstance(value, datetime.datetime):
            return str(round(value.timestamp()))
        if isinstance(value, Enum):
            return self.prepare_value(value.value, bot=bot, files=files)

        if _dumps_json:
            return self.json_dumps(value)
        return value

    async def __call__(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: Optional[int] = None,
    ) -> TelegramType:
        middleware = self.middleware.wrap_middlewares(self.make_request, timeout=timeout)
        return cast(TelegramType, await middleware(bot, method))

    async def __aenter__(self) -> BaseSession:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()
