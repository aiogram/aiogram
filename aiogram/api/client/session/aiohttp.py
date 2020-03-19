from __future__ import annotations

from typing import AsyncGenerator, Callable, Optional, TypeVar, Type, Tuple, Dict, Any, Union, cast

from aiohttp import ClientSession, ClientTimeout, FormData, BasicAuth, TCPConnector

from aiogram.api.methods import Request, TelegramMethod

from .base import PRODUCTION, BaseSession, TelegramAPIServer

T = TypeVar("T")
_ProxyType = Union[str, Tuple[str, BasicAuth]]


class AiohttpSession(BaseSession[_ProxyType]):
    def __init__(
        self,
        api: TelegramAPIServer = PRODUCTION,
        json_loads: Optional[Callable] = None,
        json_dumps: Optional[Callable] = None,
        proxy: Optional[_ProxyType] = None,
    ):
        super(AiohttpSession, self).__init__(
            api=api,
            json_loads=json_loads,
            json_dumps=json_dumps,
            proxy=proxy
        )
        self._session: Optional[ClientSession] = None
        self._connector_type: Type[TCPConnector] = TCPConnector
        self._connector_init: Dict[str, Any] = {}

        if self.proxy:
            try:
                from aiohttp_socks import ProxyConnector
                from aiohttp_socks.utils import parse_proxy_url
            except ImportError as exc:  # pragma: no cover
                raise UserWarning(
                    "In order to use aiohttp client for proxy requests, install "
                    "https://pypi.org/project/aiohttp-socks/"
                ) from exc

            if isinstance(self.proxy, str):
                proxy_url, proxy_auth = self.proxy, None
            else:
                proxy_url, proxy_auth = self.proxy

            self._connector_type = ProxyConnector

            proxy_type, host, port, username, password = parse_proxy_url(proxy_url)
            if proxy_auth:
                if not username:
                    username = proxy_auth.login
                if not password:
                    password = proxy_auth.password

            self._connector_init.update(
                dict(
                    proxy_type=proxy_type, host=host, port=port,
                    username=username, password=password,
                    rdns=True,
                )
            )

    async def create_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                connector=self._connector_type(**self._connector_init)
            )

        return self._session

    async def close(self):
        if self._session is not None and not self._session.closed:
            await self._session.close()

    def build_form_data(self, request: Request):
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
