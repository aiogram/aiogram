import io

import aiofiles
import pytest
from aiofiles import threadpool
from aresponses import ResponsesMockServer

from aiogram.api.client.base import BaseBot
from aiogram.api.client.session.aiohttp import AiohttpSession
from aiogram.api.methods import GetMe

try:
    from asynctest import CoroutineMock, patch
except ImportError:
    from unittest.mock import AsyncMock as CoroutineMock, MagicMock, patch  # type: ignore


class TestBaseBot:
    def test_init(self):
        base_bot = BaseBot("42:TEST")
        assert isinstance(base_bot.session, AiohttpSession)
        assert base_bot.id == 42

    def test_hashable(self):
        base_bot = BaseBot("42:TEST")
        assert hash(base_bot) == hash("42:TEST")

    def test_equals(self):
        base_bot = BaseBot("42:TEST")
        assert base_bot == BaseBot("42:TEST")
        assert base_bot != "42:TEST"

    @pytest.mark.asyncio
    async def test_emit(self):
        base_bot = BaseBot("42:TEST")

        method = GetMe()

        with patch(
            "aiogram.api.client.session.aiohttp.AiohttpSession.make_request",
            new_callable=CoroutineMock,
        ) as mocked_make_request:
            await base_bot(method)
            mocked_make_request.assert_awaited_with("42:TEST", method)

    @pytest.mark.asyncio
    async def test_close(self):
        base_bot = BaseBot("42:TEST", session=AiohttpSession())
        await base_bot.session.create_session()

        with patch(
            "aiogram.api.client.session.aiohttp.AiohttpSession.close", new_callable=CoroutineMock
        ) as mocked_close:
            await base_bot.close()
            mocked_close.assert_awaited()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("close", [True, False])
    async def test_context_manager(self, close: bool):
        with patch(
            "aiogram.api.client.session.aiohttp.AiohttpSession.close", new_callable=CoroutineMock
        ) as mocked_close:
            async with BaseBot("42:TEST", session=AiohttpSession()).context(
                auto_close=close
            ) as bot:
                assert isinstance(bot, BaseBot)
            if close:
                mocked_close.assert_awaited()
            else:
                mocked_close.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_download_file(self, aresponses: ResponsesMockServer):
        aresponses.add(
            aresponses.ANY, aresponses.ANY, "get", aresponses.Response(status=200, body=b"\f" * 10)
        )

        # https://github.com/Tinche/aiofiles#writing-tests-for-aiofiles
        aiofiles.threadpool.wrap.register(MagicMock)(
            lambda *args, **kwargs: threadpool.AsyncBufferedIOBase(*args, **kwargs)
        )

        mock_file = MagicMock()

        base_bot = BaseBot("42:TEST")
        with patch("aiofiles.threadpool.sync_open", return_value=mock_file):
            await base_bot.download_file("TEST", "file.png")
            mock_file.write.assert_called_once_with(b"\f" * 10)

    @pytest.mark.asyncio
    async def test_download_file_default_destination(self, aresponses: ResponsesMockServer):
        base_bot = BaseBot("42:TEST")

        aresponses.add(
            aresponses.ANY, aresponses.ANY, "get", aresponses.Response(status=200, body=b"\f" * 10)
        )

        result = await base_bot.download_file("TEST")

        assert isinstance(result, io.BytesIO)
        assert result.read() == b"\f" * 10

    @pytest.mark.asyncio
    async def test_download_file_custom_destination(self, aresponses: ResponsesMockServer):
        base_bot = BaseBot("42:TEST")

        aresponses.add(
            aresponses.ANY, aresponses.ANY, "get", aresponses.Response(status=200, body=b"\f" * 10)
        )

        custom = io.BytesIO()

        result = await base_bot.download_file("TEST", custom)

        assert isinstance(result, io.BytesIO)
        assert result is custom
        assert result.read() == b"\f" * 10
