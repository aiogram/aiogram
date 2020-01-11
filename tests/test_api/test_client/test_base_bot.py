import pytest

from aiogram.api.client.base import BaseBot
from aiogram.api.client.session.aiohttp import AiohttpSession
from aiogram.api.methods import GetMe

try:
    from asynctest import CoroutineMock, patch
except ImportError:
    from unittest.mock import AsyncMock as CoroutineMock, patch  # type: ignore


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
            await base_bot.emit(method)
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
