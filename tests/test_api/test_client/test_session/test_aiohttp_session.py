import asyncio
from collections.abc import AsyncGenerator, AsyncIterable
from typing import (
    Any,
    AsyncContextManager,
)
from unittest.mock import AsyncMock, Mock, patch

import aiohttp_socks
import pytest
from aiohttp import (
    ClientConnectorError,
    ClientError,
    ClientOSError,
    ClientProxyConnectionError,
    ClientResponseError,
    ConnectionTimeoutError,
    InvalidURL,
    InvalidUrlRedirectClientError,
    NonHttpUrlClientError,
    RequestInfo,
    ServerDisconnectedError,
    SocketTimeoutError,
    TooManyRedirects,
)
from aresponses import ResponsesMockServer
from multidict import CIMultiDict, CIMultiDictProxy
from yarl import URL

from aiogram import Bot
from aiogram.client.default import Default
from aiogram.client.session import aiohttp
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.exceptions import TelegramNetworkError
from aiogram.methods import GetMe, TelegramMethod
from aiogram.types import InputFile, URLInputFile
from tests.mocked_bot import MockedBot
from tests.token_safety import FAKE_TOKEN, assert_token_absent


TOKEN = FAKE_TOKEN


def url_errors(url: str) -> list[ClientError]:
    headers = CIMultiDictProxy(CIMultiDict({"Location": url}))
    info = RequestInfo(URL(url), "GET", headers, URL(url))
    return [
        ClientOSError(2, f"Can not write request body for {url}"),
        ClientResponseError(info, (), status=404, message=f"Not Found {TOKEN}", headers=headers),
        TooManyRedirects(info, ()),
        ConnectionTimeoutError(f"Connection timeout to host {url}"),
        InvalidURL(url, f"bad {TOKEN}"),
        asyncio.TimeoutError(url),
    ]


def assert_wrapped(exc: BaseException) -> None:
    assert isinstance(exc, TelegramNetworkError)
    assert exc.__cause__ is None
    assert exc.__suppress_context__
    assert_token_absent(exc)
    # The raw error is kept, not chained, for code that needs it
    assert exc.original is exc.__context__


class BareInputFile(InputFile):
    async def read(self, chunk_size: int):
        yield b""


class TestAiohttpSession:
    async def test_create_session(self):
        session = AiohttpSession()
        assert session._session is None
        aiohttp_session = await session.create_session()
        assert session._session is not None
        assert isinstance(aiohttp_session, aiohttp.ClientSession)
        await session.close()

    async def test_create_proxy_session(self):
        auth = aiohttp.BasicAuth("login", "password", "encoding")
        async with AiohttpSession(proxy=("socks5://proxy.url:1080/", auth)) as session:
            assert session._connector_type == aiohttp_socks.ProxyConnector

            assert isinstance(session._connector_init, dict)
            assert session._connector_init["proxy_type"] is aiohttp_socks.ProxyType.SOCKS5

            aiohttp_session = await session.create_session()
            assert isinstance(aiohttp_session.connector, aiohttp_socks.ProxyConnector)

    async def test_create_proxy_session_proxy_url(self):
        async with AiohttpSession(proxy="socks4://proxy.url:1080/") as session:
            assert isinstance(session.proxy, str)

            assert isinstance(session._connector_init, dict)
            assert session._connector_init["proxy_type"] is aiohttp_socks.ProxyType.SOCKS4

            aiohttp_session = await session.create_session()
            assert isinstance(aiohttp_session.connector, aiohttp_socks.ProxyConnector)

    async def test_create_proxy_session_chained_proxies(self):
        proxy_chain = [
            "socks4://proxy.url:1080/",
            "socks5://proxy.url:1080/",
            "http://user:password@127.0.0.1:3128",
        ]
        async with AiohttpSession(proxy=proxy_chain) as session:
            assert isinstance(session.proxy, list)

            assert isinstance(session._connector_init, dict)

            proxy_infos = session._connector_init["proxy_infos"]
            assert isinstance(proxy_infos, list)
            assert isinstance(proxy_infos[0], aiohttp_socks.ProxyInfo)
            assert proxy_infos[0].proxy_type is aiohttp_socks.ProxyType.SOCKS4
            assert proxy_infos[1].proxy_type is aiohttp_socks.ProxyType.SOCKS5
            assert proxy_infos[2].proxy_type is aiohttp_socks.ProxyType.HTTP

            aiohttp_session = await session.create_session()
            assert isinstance(aiohttp_session.connector, aiohttp_socks.ChainProxyConnector)

    async def test_reset_connector(self):
        session = AiohttpSession()
        assert session._should_reset_connector
        await session.create_session()
        assert session._should_reset_connector is False
        await session.close()
        assert session._should_reset_connector is False

        assert session.proxy is None
        session.proxy = "socks5://auth:auth@proxy.url:1080/"
        assert session._should_reset_connector
        await session.create_session()
        assert session._should_reset_connector is False

        await session.close()

    async def test_close_session(self):
        session = AiohttpSession()
        await session.create_session()

        with patch("aiohttp.ClientSession.close", new=AsyncMock()) as mocked_close:
            await session.close()
            mocked_close.assert_called_once()

        await session.close()

    def test_build_form_data_with_data_only(self, bot: MockedBot):
        class TestMethod(TelegramMethod[bool]):
            __api_method__ = "test"
            __returning__ = bool

            str_: str
            int_: int
            bool_: bool
            unset_: str | Default = Default("parse_mode")
            null_: None
            list_: list[str]
            dict_: dict[str, Any]

        session = AiohttpSession()
        form = session.build_form_data(
            bot,
            TestMethod(
                str_="value",
                int_=42,
                bool_=True,
                unset_=Default("parse_mode"),
                null_=None,
                list_=["foo"],
                dict_={"bar": "baz"},
            ),
        )

        fields = form._fields
        assert len(fields) == 5
        assert all(isinstance(field[2], str) for field in fields)
        assert "null_" not in [item[0]["name"] for item in fields]

    def test_build_form_data_with_files(self, bot: Bot):
        class TestMethod(TelegramMethod[bool]):
            __api_method__ = "test"
            __returning__ = bool

            key: str
            document: InputFile

        session = AiohttpSession()
        form = session.build_form_data(
            bot,
            TestMethod(key="value", document=BareInputFile(filename="file.txt")),
        )

        fields = form._fields

        assert len(fields) == 3
        assert fields[1][0]["name"] == "document"
        assert fields[1][2].startswith("attach://")
        assert fields[2][0]["name"] == fields[1][2][9:]
        assert fields[2][0]["filename"] == "file.txt"
        assert isinstance(fields[2][2], AsyncIterable)

    async def test_make_request(self, bot: MockedBot, aresponses: ResponsesMockServer):
        aresponses.add(
            aresponses.ANY,
            "/bot42:TEST/method",
            "post",
            aresponses.Response(
                status=200,
                text='{"ok": true, "result": 42}',
                headers={"Content-Type": "application/json"},
            ),
        )

        async with AiohttpSession() as session:

            class TestMethod(TelegramMethod[int]):
                __returning__ = int
                __api_method__ = "method"

            call = TestMethod()

            result = await session.make_request(bot, call)
            assert isinstance(result, int)
            assert result == 42

    @pytest.mark.parametrize("error", [ClientError("mocked"), asyncio.TimeoutError()])
    async def test_make_request_network_error(self, error):
        async def side_effect(*args, **kwargs):
            raise error

        async with Bot("42:TEST").context() as bot:
            with patch(
                "aiohttp.client.ClientSession._request",
                new_callable=AsyncMock,
                side_effect=side_effect,
            ):
                with pytest.raises(TelegramNetworkError):
                    await bot.get_me()

    async def test_stream_content(self, aresponses: ResponsesMockServer):
        aresponses.add(
            aresponses.ANY, aresponses.ANY, "get", aresponses.Response(status=200, body=b"\f" * 10)
        )

        async with AiohttpSession() as session:
            stream = session.stream_content(
                "https://www.python.org/static/img/python-logo.png",
                timeout=5,
                chunk_size=1,
                raise_for_status=True,
            )
            assert isinstance(stream, AsyncGenerator)

            size = 0
            async for chunk in stream:
                assert isinstance(chunk, bytes)
                chunk_size = len(chunk)
                assert chunk_size == 1
                size += chunk_size
            assert size == 10

    async def test_stream_content_404(self, aresponses: ResponsesMockServer):
        aresponses.add(
            aresponses.ANY,
            aresponses.ANY,
            "get",
            aresponses.Response(
                status=404,
                body=b"File not found",
            ),
        )
        async with AiohttpSession() as session:
            stream = session.stream_content(
                "https://www.python.org/static/img/python-logo.png",
                timeout=5,
                chunk_size=1,
                raise_for_status=True,
            )

            with pytest.raises(TelegramNetworkError) as exc_info:
                async for _ in stream:
                    ...

        error = exc_info.value
        assert error.method is None
        assert error.request_sent is True
        assert isinstance(error.original, ClientResponseError)
        assert str(error) == (
            "HTTP Client says - ClientResponseError: GET https://www.python.org/... -> 404 Not Found"
        )

    @staticmethod
    def raising(index: int) -> Any:
        async def side_effect(method: str, url: str, *args: Any, **kwargs: Any):
            raise url_errors(url)[index]

        return patch(
            "aiohttp.client.ClientSession._request",
            new_callable=AsyncMock,
            side_effect=side_effect,
        )

    @pytest.mark.parametrize("index", range(len(url_errors(""))))
    async def test_make_request_network_error_hides_token(self, index: int):
        async with Bot(TOKEN).context() as bot:
            with self.raising(index), pytest.raises(TelegramNetworkError) as exc_info:
                await bot.get_me()

        error = exc_info.value
        assert_wrapped(error)
        assert isinstance(error.method, GetMe)
        assert str(error).startswith(
            f"HTTP Client says - {type(error.original).__name__}: "
            "POST https://api.telegram.org/bot123456:***/getMe"
        )

    @pytest.mark.parametrize("index", range(len(url_errors(""))))
    async def test_download_file_error_hides_token(self, index: int):
        async with Bot(TOKEN).context() as bot:
            with self.raising(index), pytest.raises(TelegramNetworkError) as exc_info:
                await bot.download_file("documents/file.pdf")

        error = exc_info.value
        assert_wrapped(error)
        assert error.method is None
        assert str(error).startswith(
            f"HTTP Client says - {type(error.original).__name__}: "
            "GET https://api.telegram.org/file/bot123456:***/documents/file.pdf"
        )

    @pytest.mark.parametrize("index", range(len(url_errors(""))))
    async def test_url_input_file_error_hides_token(self, index: int):
        # Users build such URLs themselves to re-send a file by its download link
        async with Bot(TOKEN).context() as bot:
            file = URLInputFile(bot.session.api.file_url(TOKEN, "photos/1.jpg"), bot=bot)
            with self.raising(index), pytest.raises(TelegramNetworkError) as exc_info:
                async for _ in file.read(bot):
                    ...

        assert_wrapped(exc_info.value)
        assert "/file/bot123456:***/photos/1.jpg" in str(exc_info.value)

    async def test_download_file_404_hides_token(self, aresponses: ResponsesMockServer):
        aresponses.add(
            aresponses.ANY,
            f"/file/bot{TOKEN}/documents/file.pdf",
            "get",
            aresponses.Response(status=404, reason=f"Not Found {TOKEN}"),
        )

        async with Bot(TOKEN).context() as bot:
            with pytest.raises(TelegramNetworkError) as exc_info:
                await bot.download_file("documents/file.pdf")

        error = exc_info.value
        assert_wrapped(error)
        assert error.original.status == 404
        # The server's reason phrase is not used, the standard one is
        assert str(error).endswith("/file/bot123456:***/documents/file.pdf -> 404 Not Found")

    async def test_make_request_real_connection_error(self):
        session = AiohttpSession(api=TelegramAPIServer.from_base("http://127.0.0.1:1"))
        async with Bot(TOKEN, session=session).context() as bot:
            with pytest.raises(TelegramNetworkError) as exc_info:
                await bot.get_me()

        assert_wrapped(exc_info.value)
        assert isinstance(exc_info.value.original, ClientConnectorError)
        assert exc_info.value.request_sent is False

    async def test_make_request_invalid_url(self):
        session = AiohttpSession(api=TelegramAPIServer.from_base("bad://api.example"))
        async with Bot(TOKEN, session=session).context() as bot:
            with pytest.raises(TelegramNetworkError) as exc_info:
                await bot.get_me()

        assert_wrapped(exc_info.value)
        assert exc_info.value.request_sent is False
        assert "bad://api.example/bot123456:***/getMe" in str(exc_info.value)

    @pytest.mark.parametrize(
        ("error", "sent"),
        [
            (ClientConnectorError(Mock(), OSError(111, "refused")), False),
            (ClientProxyConnectionError(Mock(), OSError(111, "refused")), False),
            (ConnectionTimeoutError("connect"), False),
            (InvalidURL("x"), False),
            (NonHttpUrlClientError("x"), False),
            (ClientResponseError(Mock(), (), status=502), True),
            (TooManyRedirects(Mock(), ()), True),
            (InvalidUrlRedirectClientError("x"), True),
            (asyncio.TimeoutError(), None),
            (SocketTimeoutError("read"), None),
            (ServerDisconnectedError(), None),
            (ClientOSError(32, "Broken pipe"), None),
        ],
    )
    def test_request_sent(self, error: BaseException, sent: bool | None):
        assert aiohttp._network_error(error, None, "GET", "u").request_sent is sent

    @pytest.mark.parametrize(
        ("status", "suffix"),
        [(404, " -> 404 Not Found"), (599, " -> 599"), (0, "")],
    )
    def test_network_error_status(self, status: int, suffix: str):
        error = ClientResponseError(Mock(), (), status=status, message="echo")
        assert aiohttp._network_error(error, None, "GET", "u").message == (
            f"ClientResponseError: GET u{suffix}"
        )

    async def test_context_manager(self):
        async with AiohttpSession() as session:
            assert isinstance(session, AsyncContextManager)

            with (
                patch(
                    "aiogram.client.session.aiohttp.AiohttpSession.create_session",
                    new_callable=AsyncMock,
                ) as mocked_create_session,
                patch(
                    "aiogram.client.session.aiohttp.AiohttpSession.close",
                    new_callable=AsyncMock,
                ) as mocked_close,
            ):
                async with session as ctx:
                    assert session == ctx
                mocked_close.assert_awaited_once()
                mocked_create_session.assert_awaited_once()
