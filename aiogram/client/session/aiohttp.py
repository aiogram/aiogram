from __future__ import annotations

import asyncio
import re
import ssl
from collections.abc import AsyncGenerator, Iterable
from typing import TYPE_CHECKING, Any, Self, TypeVar, cast

import certifi
from aiohttp import (
    BasicAuth,
    ClientError,
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    FormData,
    RequestInfo,
    TCPConnector,
)
from aiohttp.hdrs import USER_AGENT
from aiohttp.http import SERVER_SOFTWARE
from multidict import CIMultiDict, CIMultiDictProxy, MultiMapping
from yarl import URL

from aiogram.__meta__ import __version__
from aiogram.exceptions import TelegramNetworkError
from aiogram.methods.base import TelegramType

from .base import BaseSession

if TYPE_CHECKING:
    from aiogram.client.bot import Bot
    from aiogram.methods import TelegramMethod
    from aiogram.types import InputFile

_ProxyBasic = str | tuple[str, BasicAuth]
_ProxyChain = Iterable[_ProxyBasic]
_ProxyType = _ProxyChain | _ProxyBasic
_ClientErrorT = TypeVar("_ClientErrorT", bound=ClientError)

# The bot token in a Bot API URL path (`/bot<id>:<secret>/`) or a bare token anywhere
_TOKEN_RE = re.compile(r"(?<=/bot)(\d+):[^/?#\s'\"]+|\b(\d+):[\w-]{30,}", re.ASCII)


def _redact(text: str) -> str:
    return _TOKEN_RE.sub(lambda m: f"{m[1] or m[2]}:***", text)


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return _redact(value)
    if isinstance(value, URL):
        return URL(_redact(str(value)), encoded=True)
    if isinstance(value, MultiMapping):
        # Headers such as `Location` can hold a Bot API URL
        return CIMultiDictProxy(CIMultiDict((k, _redact_value(v)) for k, v in value.items()))
    if isinstance(value, RequestInfo):
        return value._replace(
            url=_redact_value(value.url),
            headers=_redact_value(value.headers),
            real_url=_redact_value(value.real_url),
        )
    return value


def _redact_error(error: _ClientErrorT) -> _ClientErrorT:
    """
    Copy an aiohttp error of the same type with the bot token removed from its text.

    Constructors differ between aiohttp error types, so the copy is built from
    ``args`` and ``__dict__`` instead. The untouched error is kept on ``.original``.
    """
    cls = type(error)
    args = tuple(_redact_value(arg) for arg in error.args)
    redacted = cls.__new__(cls, *args)
    redacted.__dict__.update(
        {key: _redact_value(value) for key, value in vars(error).items()},
        original=error,
    )
    redacted.args = args
    if isinstance(redacted, OSError) and isinstance(error, OSError) and error.errno is not None:
        # Only when set: assigning None turns a message-only error into "[Errno None] None"
        redacted.errno, redacted.strerror = error.errno, _redact_value(error.strerror)
    if isinstance(redacted, ClientResponseError):
        # Responses of the redirect history print their URLs
        redacted.history = ()
        redacted.args = (redacted.request_info, ())
    return redacted


def _retrieve_basic(basic: _ProxyBasic) -> dict[str, Any]:
    from aiohttp_socks.utils import parse_proxy_url

    proxy_auth: BasicAuth | None = None

    if isinstance(basic, str):
        proxy_url = basic
    else:
        proxy_url, proxy_auth = basic

    proxy_type, host, port, username, password = parse_proxy_url(proxy_url)
    if isinstance(proxy_auth, BasicAuth):
        username = proxy_auth.login
        password = proxy_auth.password

    return {
        "proxy_type": proxy_type,
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "rdns": True,
    }


def _prepare_connector(chain_or_plain: _ProxyType) -> tuple[type[TCPConnector], dict[str, Any]]:
    from aiohttp_socks import ChainProxyConnector, ProxyConnector, ProxyInfo

    # since tuple is Iterable(compatible with _ProxyChain) object, we assume that
    # user wants chained proxies if tuple is a pair of string(url) and BasicAuth
    if isinstance(chain_or_plain, str) or (
        isinstance(chain_or_plain, tuple) and len(chain_or_plain) == 2  # noqa: PLR2004
    ):
        chain_or_plain = cast(_ProxyBasic, chain_or_plain)
        return ProxyConnector, _retrieve_basic(chain_or_plain)

    chain_or_plain = cast(_ProxyChain, chain_or_plain)
    infos: list[ProxyInfo] = [ProxyInfo(**_retrieve_basic(basic)) for basic in chain_or_plain]

    return ChainProxyConnector, {"proxy_infos": infos}


class AiohttpSession(BaseSession):
    def __init__(self, proxy: _ProxyType | None = None, limit: int = 100, **kwargs: Any) -> None:
        """
        Client session based on aiohttp.

        :param proxy: The proxy to be used for requests. Default is None.
        :param limit: The total number of simultaneous connections. Default is 100.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)

        self._session: ClientSession | None = None
        self._connector_type: type[TCPConnector] = TCPConnector
        self._connector_init: dict[str, Any] = {
            "ssl": ssl.create_default_context(cafile=certifi.where()),
            "limit": limit,
            "ttl_dns_cache": 3600,  # Workaround for https://github.com/aiogram/aiogram/issues/1500
        }
        self._should_reset_connector = True  # flag determines connector state
        self._proxy: _ProxyType | None = None

        if proxy is not None:
            try:
                self._setup_proxy_connector(proxy)
            except ImportError as exc:  # pragma: no cover
                msg = (
                    "In order to use aiohttp client for proxy requests, install "
                    "https://pypi.org/project/aiohttp-socks/"
                )
                raise RuntimeError(msg) from exc

    def _setup_proxy_connector(self, proxy: _ProxyType) -> None:
        self._connector_type, self._connector_init = _prepare_connector(proxy)
        self._proxy = proxy

    @property
    def proxy(self) -> _ProxyType | None:
        return self._proxy

    @proxy.setter
    def proxy(self, proxy: _ProxyType) -> None:
        self._setup_proxy_connector(proxy)
        self._should_reset_connector = True

    async def create_session(self) -> ClientSession:
        if self._should_reset_connector:
            await self.close()

        if self._session is None or self._session.closed:
            self._session = ClientSession(
                connector=self._connector_type(**self._connector_init),
                headers={
                    USER_AGENT: f"{SERVER_SOFTWARE} aiogram/{__version__}",
                },
            )
            self._should_reset_connector = False

        return self._session

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()

            # Wait 250 ms for the underlying SSL connections to close
            # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
            await asyncio.sleep(0.25)

    def build_form_data(self, bot: Bot, method: TelegramMethod[TelegramType]) -> FormData:
        form = FormData(quote_fields=False)
        files: dict[str, InputFile] = {}
        for key, value in method.model_dump(warnings=False).items():
            value = self.prepare_value(value, bot=bot, files=files)
            if not value:
                continue
            form.add_field(key, value)
        for key, value in files.items():
            form.add_field(
                key,
                value.read(bot),
                filename=value.filename or key,
            )
        return form

    async def make_request(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: int | None = None,
    ) -> TelegramType:
        session = await self.create_session()

        url = self.api.api_url(token=bot.token, method=method.__api_method__)
        form = self.build_form_data(bot=bot, method=method)

        try:
            async with session.post(
                url,
                data=form,
                timeout=ClientTimeout(total=self.timeout if timeout is None else timeout),
            ) as resp:
                raw_result = await resp.text(errors="replace")
        except (TimeoutError, ClientError) as e:
            # `from None`: a traceback prints the chained error, and its URL holds the token
            message = (
                "Request timeout error"
                if isinstance(e, TimeoutError)
                else _redact(f"{type(e).__name__}: {e}")
            )
            error = TelegramNetworkError(method=method, message=message)
            error.original = e
            raise error from None
        response = self.check_response(
            bot=bot,
            method=method,
            status_code=resp.status,
            content=raw_result,
        )
        return cast(TelegramType, response.result)

    async def stream_content(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes, None]:
        if headers is None:
            headers = {}

        session = await self.create_session()

        try:
            async with session.get(
                url,
                timeout=ClientTimeout(total=timeout),
                headers=headers,
                raise_for_status=raise_for_status,
            ) as resp:
                async for chunk in resp.content.iter_chunked(chunk_size):
                    yield chunk
        except ClientError as e:
            raise _redact_error(e) from None

    async def __aenter__(self) -> Self:
        await self.create_session()
        return self
