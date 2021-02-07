from typing import AsyncContextManager, AsyncGenerator

import aiohttp_socks
import pytest
from aresponses import ResponsesMockServer

from aiogram import Bot
from aiogram.client.session import aiohttp
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.methods import Request, TelegramMethod
from aiogram.types import UNSET, InputFile
from tests.mocked_bot import MockedBot

try:
    from asynctest import CoroutineMock, patch
except ImportError:
    from unittest.mock import AsyncMock as CoroutineMock  # type: ignore
    from unittest.mock import patch


class BareInputFile(InputFile):
    async def read(self, chunk_size: int):
        yield b""


class TestAiohttpSession:
    @pytest.mark.asyncio
    async def test_create_session(self):
        session = AiohttpSession()

        assert session._session is None
        aiohttp_session = await session.create_session()
        assert session._session is not None
        assert isinstance(aiohttp_session, aiohttp.ClientSession)

    @pytest.mark.asyncio
    async def test_create_proxy_session(self):
        session = AiohttpSession(
            proxy=("socks5://proxy.url/", aiohttp.BasicAuth("login", "password", "encoding"))
        )

        assert session._connector_type == aiohttp_socks.ProxyConnector

        assert isinstance(session._connector_init, dict)
        assert session._connector_init["proxy_type"] is aiohttp_socks.ProxyType.SOCKS5

        aiohttp_session = await session.create_session()
        assert isinstance(aiohttp_session.connector, aiohttp_socks.ProxyConnector)

    @pytest.mark.asyncio
    async def test_create_proxy_session_proxy_url(self):
        session = AiohttpSession(proxy="socks4://proxy.url/")

        assert isinstance(session.proxy, str)

        assert isinstance(session._connector_init, dict)
        assert session._connector_init["proxy_type"] is aiohttp_socks.ProxyType.SOCKS4

        aiohttp_session = await session.create_session()
        assert isinstance(aiohttp_session.connector, aiohttp_socks.ProxyConnector)

    @pytest.mark.asyncio
    async def test_create_proxy_session_chained_proxies(self):
        session = AiohttpSession(
            proxy=[
                "socks4://proxy.url/",
                "socks5://proxy.url/",
                "http://user:password@127.0.0.1:3128",
            ]
        )

        assert isinstance(session.proxy, list)

        assert isinstance(session._connector_init, dict)
        assert isinstance(session._connector_init["proxy_infos"], list)
        assert isinstance(session._connector_init["proxy_infos"][0], aiohttp_socks.ProxyInfo)

        assert (
            session._connector_init["proxy_infos"][0].proxy_type is aiohttp_socks.ProxyType.SOCKS4
        )
        assert (
            session._connector_init["proxy_infos"][1].proxy_type is aiohttp_socks.ProxyType.SOCKS5
        )
        assert session._connector_init["proxy_infos"][2].proxy_type is aiohttp_socks.ProxyType.HTTP

        aiohttp_session = await session.create_session()
        assert isinstance(aiohttp_session.connector, aiohttp_socks.ChainProxyConnector)

    @pytest.mark.asyncio
    async def test_reset_connector(self):
        session = AiohttpSession()
        assert session._should_reset_connector
        await session.create_session()
        assert session._should_reset_connector is False
        await session.close()
        assert session._should_reset_connector is False

        assert session.proxy is None
        session.proxy = "socks5://auth:auth@proxy.url/"
        assert session._should_reset_connector
        await session.create_session()
        assert session._should_reset_connector is False
        await session.close()

    @pytest.mark.asyncio
    async def test_close_session(self):
        session = AiohttpSession()
        await session.create_session()

        with patch("aiohttp.ClientSession.close", new=CoroutineMock()) as mocked_close:
            await session.close()
            mocked_close.assert_called_once()

    def test_build_form_data_with_data_only(self):
        request = Request(
            method="method",
            data={
                "str": "value",
                "int": 42,
                "bool": True,
                "unset": UNSET,
                "null": None,
                "list": ["foo"],
                "dict": {"bar": "baz"},
            },
        )

        session = AiohttpSession()
        form = session.build_form_data(request)

        fields = form._fields
        assert len(fields) == 5
        assert all(isinstance(field[2], str) for field in fields)
        assert "null" not in [item[0]["name"] for item in fields]

    def test_build_form_data_with_files(self):
        request = Request(
            method="method",
            data={"key": "value"},
            files={"document": BareInputFile(filename="file.txt")},
        )

        session = AiohttpSession()
        form = session.build_form_data(request)

        fields = form._fields

        assert len(fields) == 2
        assert fields[1][0]["name"] == "document"
        assert fields[1][0]["filename"] == "file.txt"
        assert isinstance(fields[1][2], BareInputFile)

    @pytest.mark.asyncio
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

        session = AiohttpSession()

        class TestMethod(TelegramMethod[int]):
            __returning__ = int

            def build_request(self, bot: Bot) -> Request:
                return Request(method="method", data={})

        call = TestMethod()
        with patch(
            "aiogram.client.session.base.BaseSession.raise_for_status"
        ) as patched_raise_for_status:
            result = await session.make_request(bot, call)
            assert isinstance(result, int)
            assert result == 42

            assert patched_raise_for_status.called_once()

    @pytest.mark.asyncio
    async def test_stream_content(self, aresponses: ResponsesMockServer):
        aresponses.add(
            aresponses.ANY, aresponses.ANY, "get", aresponses.Response(status=200, body=b"\f" * 10)
        )

        session = AiohttpSession()
        stream = session.stream_content(
            "https://www.python.org/static/img/python-logo.png", timeout=5, chunk_size=1
        )
        assert isinstance(stream, AsyncGenerator)

        size = 0
        async for chunk in stream:
            assert isinstance(chunk, bytes)
            chunk_size = len(chunk)
            assert chunk_size == 1
            size += chunk_size
        assert size == 10

    @pytest.mark.asyncio
    async def test_context_manager(self):
        session = AiohttpSession()
        assert isinstance(session, AsyncContextManager)

        with patch(
            "aiogram.client.session.aiohttp.AiohttpSession.create_session",
            new_callable=CoroutineMock,
        ) as mocked_create_session, patch(
            "aiogram.client.session.aiohttp.AiohttpSession.close", new_callable=CoroutineMock
        ) as mocked_close:
            async with session as ctx:
                assert session == ctx
            mocked_close.assert_awaited_once()
            mocked_create_session.assert_awaited_once()
