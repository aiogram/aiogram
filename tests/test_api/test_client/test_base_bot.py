import pytest
from asynctest import CoroutineMock, patch

from aiogram.api.client.base import BaseBot
from aiogram.api.client.session.aiohttp import AiohttpSession
from aiogram.api.methods import GetMe


class TestBaseBot:
    def test_init(self):
        base_bot = BaseBot("TOKEN")
        assert isinstance(base_bot.session, AiohttpSession)

    @pytest.mark.asyncio
    async def test_emit(self):
        base_bot = BaseBot("TOKEN")

        method = GetMe()

        with patch(
            "aiogram.api.client.session.aiohttp.AiohttpSession.make_request",
            new_callable=CoroutineMock,
        ) as mocked_make_request:
            await base_bot.emit(method)
            mocked_make_request.assert_awaited_with("TOKEN", method)
