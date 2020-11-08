import aiohttp
import aiohttp_socks
import pytest

from aiogram.bot.base import BaseBot

try:
    from asynctest import CoroutineMock, patch
except ImportError:
    from unittest.mock import AsyncMock as CoroutineMock  # type: ignore
    from unittest.mock import patch


class TestAiohttpSession:
    @pytest.mark.asyncio
    async def test_create_bot(self):
        bot = BaseBot(token="42:correct")

        if bot._session is not None:
            raise AssertionError
        if not isinstance(bot._connector_init, dict):
            raise AssertionError
        if not all(key in {"limit", "ssl", "loop"} for key in bot._connector_init):
            raise AssertionError
        if not isinstance(bot._connector_class, type):
            raise AssertionError
        if not issubclass(bot._connector_class, aiohttp.TCPConnector):
            raise AssertionError

        if bot._session is not None:
            raise AssertionError

        if not isinstance(bot.session, aiohttp.ClientSession):
            raise AssertionError
        if bot.session != bot._session:
            raise AssertionError

    @pytest.mark.asyncio
    async def test_create_proxy_bot(self):
        socks_ver, host, port, username, password = (
            "socks5",
            "124.90.90.90",
            9999,
            "login",
            "password",
        )

        bot = BaseBot(
            token="42:correct",
            proxy=f"{socks_ver}://{host}:{port}/",
            proxy_auth=aiohttp.BasicAuth(username, password, "encoding"),
        )

        if bot._connector_class != aiohttp_socks.SocksConnector:
            raise AssertionError

        if not isinstance(bot._connector_init, dict):
            raise AssertionError

        init_kwargs = bot._connector_init
        if init_kwargs["username"] != username:
            raise AssertionError
        if init_kwargs["password"] != password:
            raise AssertionError
        if init_kwargs["host"] != host:
            raise AssertionError
        if init_kwargs["port"] != port:
            raise AssertionError

    @pytest.mark.asyncio
    async def test_close_session(self):
        bot = BaseBot(
            token="42:correct",
        )
        aiohttp_client_0 = bot.session

        with patch("aiohttp.ClientSession.close", new=CoroutineMock()) as mocked_close:
            await aiohttp_client_0.close()
            mocked_close.assert_called_once()

        await aiohttp_client_0.close()
        if aiohttp_client_0 == bot.session:
            raise AssertionError
