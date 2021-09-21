import io
import os
from tempfile import mkstemp

import aiofiles
import pytest
from aresponses import ResponsesMockServer

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.methods import GetFile, GetMe
from aiogram.types import File, PhotoSize
from tests.mocked_bot import MockedBot

try:
    from asynctest import CoroutineMock, patch
except ImportError:
    from unittest.mock import AsyncMock as CoroutineMock  # type: ignore
    from unittest.mock import patch

pytestmark = pytest.mark.asyncio


class TestBot:
    def test_init(self):
        bot = Bot("42:TEST")
        assert isinstance(bot.session, AiohttpSession)
        assert bot.id == 42

    def test_hashable(self):
        bot = Bot("42:TEST")
        assert hash(bot) == hash("42:TEST")

    def test_equals(self):
        bot = Bot("42:TEST")
        assert bot == Bot("42:TEST")
        assert bot != "42:TEST"

    async def test_emit(self):
        bot = Bot("42:TEST")

        method = GetMe()

        with patch(
            "aiogram.client.session.aiohttp.AiohttpSession.make_request",
            new_callable=CoroutineMock,
        ) as mocked_make_request:
            await bot(method)
            mocked_make_request.assert_awaited_with(bot, method, timeout=None)

    async def test_close(self):
        session = AiohttpSession()
        bot = Bot("42:TEST", session=session)
        await session.create_session()

        with patch(
            "aiogram.client.session.aiohttp.AiohttpSession.close", new_callable=CoroutineMock
        ) as mocked_close:
            await bot.session.close()
            mocked_close.assert_awaited()

    @pytest.mark.parametrize("close", [True, False])
    async def test_context_manager(self, close: bool):
        with patch(
            "aiogram.client.session.aiohttp.AiohttpSession.close", new_callable=CoroutineMock
        ) as mocked_close:
            async with Bot("42:TEST", session=AiohttpSession()).context(auto_close=close) as bot:
                assert isinstance(bot, Bot)
            if close:
                mocked_close.assert_awaited()
            else:
                mocked_close.assert_not_awaited()

    async def test_download_file(self, aresponses: ResponsesMockServer):
        aresponses.add(
            aresponses.ANY, aresponses.ANY, "get", aresponses.Response(status=200, body=b"\f" * 10)
        )

        # https://github.com/Tinche/aiofiles#writing-tests-for-aiofiles
        aiofiles.threadpool.wrap.register(CoroutineMock)(
            lambda *args, **kwargs: aiofiles.threadpool.AsyncBufferedIOBase(*args, **kwargs)
        )

        mock_file = CoroutineMock()

        bot = Bot("42:TEST")
        with patch("aiofiles.threadpool.sync_open", return_value=mock_file):
            await bot.download_file("TEST", "file.png")
            mock_file.write.assert_called_once_with(b"\f" * 10)

    async def test_download_file_default_destination(self, aresponses: ResponsesMockServer):
        bot = Bot("42:TEST")

        aresponses.add(
            aresponses.ANY, aresponses.ANY, "get", aresponses.Response(status=200, body=b"\f" * 10)
        )

        result = await bot.download_file("TEST")

        assert isinstance(result, io.BytesIO)
        assert result.read() == b"\f" * 10

    async def test_download_file_custom_destination(self, aresponses: ResponsesMockServer):
        bot = Bot("42:TEST")

        aresponses.add(
            aresponses.ANY, aresponses.ANY, "get", aresponses.Response(status=200, body=b"\f" * 10)
        )

        custom = io.BytesIO()

        result = await bot.download_file("TEST", custom)

        assert isinstance(result, io.BytesIO)
        assert result is custom
        assert result.read() == b"\f" * 10

    async def test_download(self, bot: MockedBot, aresponses: ResponsesMockServer):
        bot.add_result_for(
            GetFile, ok=True, result=File(file_id="file id", file_unique_id="file id")
        )
        bot.add_result_for(
            GetFile, ok=True, result=File(file_id="file id", file_unique_id="file id")
        )

        assert await bot.download(File(file_id="file id", file_unique_id="file id"))
        assert await bot.download("file id")

        with pytest.raises(TypeError):
            await bot.download(
                [PhotoSize(file_id="file id", file_unique_id="file id", width=123, height=123)]
            )

    async def test_download_local_file(self, bot: MockedBot):
        bot.session.api = TelegramAPIServer.from_base("http://localhost:8081", is_local=True)
        fd, tmp = mkstemp(prefix="test-", suffix=".txt")
        value = b"KABOOM"
        try:
            with open(fd, "wb") as f:
                f.write(value)
            content = await bot.download_file(tmp)
            assert content.getvalue() == value
        finally:
            os.unlink(tmp)
