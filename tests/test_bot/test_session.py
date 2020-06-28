import aiohttp
import aiohttp_socks
import pytest

from aiogram.bot.base import BaseBot

try:
    from asynctest import CoroutineMock, patch
except ImportError:
    from unittest.mock import AsyncMock as CoroutineMock, patch  # type: ignore


class TestAiohttpSession:
    @pytest.mark.asyncio
    async def test_create_bot(self):
        bot = BaseBot(token="42:correct")

        assert bot._session is None
        assert isinstance(bot._connector_init, dict)
        assert all(key in {"limit", "ssl", "loop"} for key in bot._connector_init)
        assert isinstance(bot._connector_class, type)
        assert issubclass(bot._connector_class, aiohttp.TCPConnector)

        assert bot._session is None

        assert isinstance(bot.session, aiohttp.ClientSession)
        assert bot.session == bot._session

    @pytest.mark.asyncio
    async def test_create_proxy_bot(self):
        socks_ver, host, port, username, password = (
            "socks5", "124.90.90.90", 9999, "login", "password"
        )

        bot = BaseBot(
            token="42:correct",
            proxy=f"{socks_ver}://{host}:{port}/",
            proxy_auth=aiohttp.BasicAuth(username, password, "encoding"),
        )

        assert bot._connector_class == aiohttp_socks.SocksConnector

        assert isinstance(bot._connector_init, dict)

        init_kwargs = bot._connector_init
        assert init_kwargs["username"] == username
        assert init_kwargs["password"] == password
        assert init_kwargs["host"] == host
        assert init_kwargs["port"] == port

    @pytest.mark.asyncio
    async def test_close_session(self):
        bot = BaseBot(token="42:correct",)
        aiohttp_client_0 = bot.session

        with patch("aiohttp.ClientSession.close", new=CoroutineMock()) as mocked_close:
            await aiohttp_client_0.close()
            mocked_close.assert_called_once()

        await aiohttp_client_0.close()
        assert aiohttp_client_0 != bot.session  # will create new session
