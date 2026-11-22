from __future__ import annotations

import abc
import datetime
import functools
import inspect
import json
import secrets
import sys
import warnings
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from enum import Enum
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Final, Self, cast

from pydantic import ValidationError

from aiogram.client.default import Default
from aiogram.client.telegram import PRODUCTION, TelegramAPIServer
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
from aiogram.methods import Response, TelegramMethod
from aiogram.methods.base import TelegramType
from aiogram.types import InputFile, TelegramObject

from .middlewares.manager import RequestMiddlewareManager

if TYPE_CHECKING:
    from types import TracebackType

    from aiogram.client.bot import Bot

_JsonLoads = Callable[..., Any]
_JsonDumps = Callable[..., str]

DEFAULT_TIMEOUT: Final[float] = 60.0


@dataclass(frozen=True, slots=True)
class DownloadTimeout:
    """
    Per-phase timeouts of a file download, in seconds; :code:`None` disables a phase.

    :param connect: getting a connection: pool wait, DNS, TCP and TLS
    :param sock_read: idle time between two reads, so a stalled transfer fails while a slow one
        keeps going
    :param total: cap on the whole download, off by default so large files on slow links finish
    """

    connect: float | None = 30.0
    sock_read: float | None = 60.0
    total: float | None = None

    @classmethod
    def of(cls, value: DownloadTimeout | float) -> DownloadTimeout:
        """A plain number is the 3.x total timeout: :code:`total=value` and nothing else."""
        if isinstance(value, DownloadTimeout):
            return value
        return cls(connect=None, sock_read=None, total=value)


DEFAULT_DOWNLOAD_TIMEOUT: Final[DownloadTimeout] = DownloadTimeout()
# What a `stream_content` override with the 3.x `timeout: int` signature gets without a total
LEGACY_DOWNLOAD_TIMEOUT: Final[int] = 30


@functools.cache
def _takes_download_timeout(cls: type[BaseSession]) -> bool:
    """
    Whether ``cls.stream_content`` accepts a :class:`DownloadTimeout`.

    It does when its ``timeout`` default is one, as in the built-in sessions. An override with
    the 3.x signature (``timeout: int = 30``) gets an int instead, with a warning once per class.
    """
    options: dict[str, Any] = {}
    if sys.version_info >= (3, 14):
        from annotationlib import Format

        # Only the default is read: an unresolvable annotation must not raise
        options["annotation_format"] = Format.FORWARDREF
    parameter = inspect.signature(cls.stream_content, **options).parameters.get("timeout")
    if parameter is None:
        # A forwarding override (`*args, **kwargs`) passes the value on unchanged
        return True
    if isinstance(parameter.default, DownloadTimeout):
        return True
    # ponytail: plain DeprecationWarning until the I-12 AiogramDeprecationWarning class lands
    warnings.warn(
        f"{cls.__module__}.{cls.__qualname__}.stream_content() takes the 3.x int timeout: it "
        f"gets the total timeout, or {LEGACY_DOWNLOAD_TIMEOUT}, instead of per-phase timeouts. "
        "Declare `timeout: DownloadTimeout | float = DEFAULT_DOWNLOAD_TIMEOUT` "
        "(aiogram.client.session.base) to receive a DownloadTimeout.",
        DeprecationWarning,
        stacklevel=3,
    )
    return False


class BaseSession(abc.ABC):
    """
    This is base class for all HTTP sessions in aiogram.

    If you want to create your own session, you must inherit from this class.
    """

    def __init__(
        self,
        api: TelegramAPIServer = PRODUCTION,
        json_loads: _JsonLoads | None = None,
        json_dumps: _JsonDumps = json.dumps,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """

        :param api: Telegram Bot API URL patterns
        :param json_loads: JSON loader; when omitted, pydantic reads the response body
            itself instead of decoding it into a dict first
        :param json_dumps: JSON dumper
        :param timeout: Session scope request timeout
        """
        self.api = api
        self.json_loads = json_loads
        self.json_dumps = json_dumps
        self.timeout = timeout

        self.middleware = RequestMiddlewareManager()

    def check_response(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        status_code: int,
        content: str,
    ) -> Response[TelegramType]:
        """
        Check response status
        """
        response_type = Response[method.__returning__]  # type: ignore
        try:
            if self.json_loads:
                try:
                    json_data = self.json_loads(content)
                except Exception as e:  # noqa: BLE001
                    # Handled error type can't be classified as specific error
                    # in due to decoder can be customized and raise any exception

                    msg = "Failed to decode object"
                    raise ClientDecodeError(msg, e, content) from e

                response = response_type.model_validate(json_data, context={"bot": bot})
            else:
                # Let pydantic read the payload straight into the model instead of
                # building an intermediate dict first.
                response = response_type.model_validate_json(content, context={"bot": bot})
        except ValidationError as e:
            msg = (
                "Failed to decode object"
                if any(error["type"].startswith("json_") for error in e.errors())
                else "Failed to deserialize object"
            )
            raise ClientDecodeError(msg, e, content) from e

        if HTTPStatus.OK <= status_code <= HTTPStatus.IM_USED and response.ok:
            return response

        description = cast(str, response.description)

        if parameters := response.parameters:
            if parameters.retry_after:
                raise TelegramRetryAfter(
                    method=method,
                    message=description,
                    retry_after=parameters.retry_after,
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
            raise TelegramEntityTooLarge(method=method, message=description, request_sent=True)
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

    @abc.abstractmethod
    async def make_request(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: int | None = None,
    ) -> TelegramType:  # pragma: no cover
        """
        Make request to Telegram Bot API

        :param bot: Bot instance
        :param method: Method instance
        :param timeout: Request timeout
        :return:
        :raise TelegramApiError:
        """

    @abc.abstractmethod
    async def stream_content(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: DownloadTimeout | float = DEFAULT_DOWNLOAD_TIMEOUT,
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes, None]:  # pragma: no cover
        """
        Stream reader

        :param timeout: per-phase timeouts; a plain number is a total timeout
            (:meth:`DownloadTimeout.of`)
        """
        yield b""

    def _download_stream(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: DownloadTimeout | float = DEFAULT_DOWNLOAD_TIMEOUT,
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes, None]:
        """
        Call :meth:`stream_content` with the timeout in the form the override accepts.

        aiogram downloads go through here, so a custom session that still declares the 3.x
        ``timeout: int`` keeps working (see :func:`_takes_download_timeout`).
        """
        timeout = DownloadTimeout.of(timeout)
        legacy: DownloadTimeout | float = timeout
        if not _takes_download_timeout(type(self)):
            legacy = LEGACY_DOWNLOAD_TIMEOUT if timeout.total is None else timeout.total
        return self.stream_content(
            url=url,
            headers=headers,
            timeout=legacy,
            chunk_size=chunk_size,
            raise_for_status=raise_for_status,
        )

    def prepare_value(
        self,
        value: Any,
        bot: Bot,
        files: dict[str, Any],
        _dumps_json: bool = True,
    ) -> Any:
        """
        Prepare value before send
        """
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, Default):
            default_value = bot.default[value.name]
            return self.prepare_value(default_value, bot=bot, files=files, _dumps_json=_dumps_json)
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
                        item,
                        bot=bot,
                        files=files,
                        _dumps_json=False,
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
                        item,
                        bot=bot,
                        files=files,
                        _dumps_json=False,
                    )
                )
                is not None
            ]
            if _dumps_json:
                return self.json_dumps(value)
            return value
        if isinstance(value, datetime.timedelta):
            now = datetime.datetime.now()  # noqa: DTZ005
            return str(round((now + value).timestamp()))
        if isinstance(value, datetime.datetime):
            return str(round(value.timestamp()))
        if isinstance(value, Enum):
            return self.prepare_value(value.value, bot=bot, files=files)
        if isinstance(value, TelegramObject):
            return self.prepare_value(
                value.model_dump(warnings=False),
                bot=bot,
                files=files,
                _dumps_json=_dumps_json,
            )
        if _dumps_json:
            return self.json_dumps(value)
        return value

    async def __call__(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: int | None = None,
    ) -> TelegramType:
        middleware = self.middleware.wrap_middlewares(self.make_request, timeout=timeout)
        return cast(TelegramType, await middleware(bot, method))

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()
