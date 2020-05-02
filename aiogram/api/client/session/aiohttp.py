from __future__ import annotations

from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from aiohttp import BasicAuth, ClientSession, ClientTimeout, FormData, TCPConnector

from aiogram.api.methods import Request, TelegramMethod

from .base import PRODUCTION, BaseSession, TelegramAPIServer

T = TypeVar("T")
_ProxyBasic = Union[str, Tuple[str, BasicAuth]]
_ProxyChain = Iterable[_ProxyBasic]
_ProxyType = Union[_ProxyChain, _ProxyBasic]


def _retrieve_basic(basic: _ProxyBasic) -> Dict[str, Any]:
    from aiohttp_socks.utils import parse_proxy_url  # type: ignore

    proxy_auth: Optional[BasicAuth] = None

    if isinstance(basic, str):
        proxy_url = basic
    else:
        proxy_url, proxy_auth = basic

    proxy_type, host, port, username, password = parse_proxy_url(proxy_url)
    if isinstance(proxy_auth, BasicAuth):
        username = proxy_auth.login
        password = proxy_auth.password

    return dict(
        proxy_type=proxy_type,
        host=host,
        port=port,
        username=username,
        password=password,
        rdns=True,
    )


def _prepare_connector(chain_or_plain: _ProxyType) -> Tuple[Type["TCPConnector"], Dict[str, Any]]:
    from aiohttp_socks import ProxyInfo, ProxyConnector, ChainProxyConnector  # type: ignore

    # since tuple is Iterable(compatible with _ProxyChain) object, we assume that
    # user wants chained proxies if tuple is a pair of string(url) and BasicAuth
    if isinstance(chain_or_plain, str) or (
        isinstance(chain_or_plain, tuple) and len(chain_or_plain) == 2
    ):
        chain_or_plain = cast(_ProxyBasic, chain_or_plain)
        return ProxyConnector, _retrieve_basic(chain_or_plain)

    chain_or_plain = cast(_ProxyChain, chain_or_plain)
    infos: List[ProxyInfo] = []
    for basic in chain_or_plain:
        infos.append(ProxyInfo(**_retrieve_basic(basic)))

    return ChainProxyConnector, dict(proxy_infos=infos)


class AiohttpSession(BaseSession):
    def __init__(
        self,
        api: TelegramAPIServer = PRODUCTION,
        json_loads: Optional[Callable[..., Any]] = None,
        json_dumps: Optional[Callable[..., str]] = None,
        proxy: Optional[_ProxyType] = None,
    ):
        super(AiohttpSession, self).__init__(
            api=api, json_loads=json_loads, json_dumps=json_dumps, proxy=proxy
        )
        self._session: Optional[ClientSession] = None
        self._connector_type: Type[TCPConnector] = TCPConnector
        self._connector_init: Dict[str, Any] = {}

        if self.proxy:
            try:
                self._connector_type, self._connector_init = _prepare_connector(
                    cast(_ProxyType, self.proxy)
                )
            except ImportError as exc:  # pragma: no cover
                raise UserWarning(
                    "In order to use aiohttp client for proxy requests, install "
                    "https://pypi.org/project/aiohttp-socks/"
                ) from exc

    async def create_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            self._session = ClientSession(connector=self._connector_type(**self._connector_init))

        return self._session

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()

    def build_form_data(self, request: Request) -> FormData:
        form = FormData(quote_fields=False)
        for key, value in request.data.items():
            if value is None:
                continue
            form.add_field(key, self.prepare_value(value))
        if request.files:
            for key, value in request.files.items():
                form.add_field(key, value, filename=value.filename or key)
        return form

    async def make_request(self, token: str, call: TelegramMethod[T]) -> T:
        session = await self.create_session()

        request = call.build_request()
        url = self.api.api_url(token=token, method=request.method)
        form = self.build_form_data(request)

        async with session.post(url, data=form) as resp:
            raw_result = await resp.json(loads=self.json_loads)

        response = call.build_response(raw_result)
        self.raise_for_status(response)
        return cast(T, response.result)

    async def stream_content(
        self, url: str, timeout: int, chunk_size: int
    ) -> AsyncGenerator[bytes, None]:
        session = await self.create_session()
        client_timeout = ClientTimeout(total=timeout)

        async with session.get(url, timeout=client_timeout) as resp:
            async for chunk in resp.content.iter_chunked(chunk_size):
                yield chunk

    async def __aenter__(self) -> AiohttpSession:
        await self.create_session()
        return self
