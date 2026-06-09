import asyncio
import time
from asyncio import Event
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import MultipartReader, web
from aiohttp.test_utils import TestClient
from aiohttp.web_app import Application

from aiogram import Dispatcher, F
from aiogram.methods import GetMe, Request
from aiogram.types import BufferedInputFile, Message, User
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    TokenBasedRequestHandler,
    ip_filter_middleware,
    setup_application,
)
from aiogram.webhook.security import IPFilter
from tests.mocked_bot import MockedBot


class TestAiohttpServer:
    def test_setup_application(self):
        app = Application()

        dp = Dispatcher()
        setup_application(app, dp)

        assert len(app.router.routes()) == 0
        assert len(app.on_startup) == 2
        assert len(app.on_shutdown) == 1

    async def test_middleware(self, aiohttp_client):
        app = Application()
        ip_filter = IPFilter.default()
        app.middlewares.append(ip_filter_middleware(ip_filter))

        async def handler(request: Request):
            return web.json_response({"ok": True})

        app.router.add_route("POST", "/webhook", handler)
        client: TestClient = await aiohttp_client(app)

        resp = await client.post("/webhook")
        assert resp.status == 401

        resp = await client.post("/webhook", headers={"X-Forwarded-For": "149.154.167.220"})
        assert resp.status == 200

        resp = await client.post(
            "/webhook", headers={"X-Forwarded-For": "149.154.167.220,10.111.0.2"}
        )
        assert resp.status == 200


class TestSimpleRequestHandler:
    async def make_reqest(self, client: TestClient, text: str = "test"):
        return await client.post(
            "/webhook",
            json={
                "update_id": 0,
                "message": {
                    "message_id": 0,
                    "from": {"id": 42, "first_name": "Test", "is_bot": False},
                    "chat": {"id": 42, "is_bot": False, "type": "private"},
                    "date": int(time.time()),
                    "text": text,
                },
            },
        )

    async def test_reply_into_webhook_file(self, bot: MockedBot, aiohttp_client):
        app = Application()
        dp = Dispatcher()

        @dp.message(F.text == "test")
        def handle_message(msg: Message):
            return msg.answer_document(
                caption="PASS",
                document=BufferedInputFile(b"test", filename="test.txt"),
            )

        handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            handle_in_background=False,
        )
        handler.register(app, path="/webhook")
        client: TestClient = await aiohttp_client(app)

        resp = await self.make_reqest(client=client)
        assert resp.status == 200
        assert resp.content_type == "multipart/form-data"
        result = {}
        reader = MultipartReader.from_response(resp)
        while part := await reader.next():
            value = await part.read()
            result[part.name] = value.decode()
        assert result["method"] == "sendDocument"
        assert result["caption"] == "PASS"
        assert result["document"].startswith("attach://")
        assert result[result["document"][9:]]

    async def test_reply_into_webhook_text(self, bot: MockedBot, aiohttp_client):
        app = Application()
        dp = Dispatcher()

        @dp.message(F.text == "test")
        def handle_message(msg: Message):
            return msg.answer(text="PASS")

        handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            handle_in_background=False,
        )
        handler.register(app, path="/webhook")
        client: TestClient = await aiohttp_client(app)

        resp = await self.make_reqest(client=client)
        assert resp.status == 200
        assert resp.content_type == "multipart/form-data"
        result = {}
        reader = MultipartReader.from_response(resp)
        while part := await reader.next():
            value = await part.read()
            result[part.name] = value.decode()
        assert result["method"] == "sendMessage"
        assert result["text"] == "PASS"

    async def test_reply_into_webhook_unhandled(self, bot: MockedBot, aiohttp_client):
        app = Application()
        dp = Dispatcher()

        @dp.message(F.text == "test")
        def handle_message(msg: Message):
            return msg.answer(text="PASS")

        handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            handle_in_background=False,
        )
        handler.register(app, path="/webhook")
        client: TestClient = await aiohttp_client(app)

        resp = await self.make_reqest(client=client, text="spam")
        assert resp.status == 200
        assert resp.content_type == "application/json"
        expected_result = {}
        assert await resp.json() == expected_result

    async def test_reply_into_webhook_background(self, bot: MockedBot, aiohttp_client):
        app = Application()
        dp = Dispatcher()

        handler_event = Event()

        @dp.message(F.text == "test")
        def handle_message(msg: Message):
            handler_event.set()
            return msg.answer(text="PASS")

        handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            handle_in_background=True,
        )
        handler.register(app, path="/webhook")
        client: TestClient = await aiohttp_client(app)

        with patch(
            "aiogram.dispatcher.dispatcher.Dispatcher.silent_call_request",
            new_callable=AsyncMock,
        ) as mocked_silent_call_request:
            method_called_event = asyncio.Event()
            mocked_silent_call_request.side_effect = lambda *args, **kwargs: (
                method_called_event.set()
            )

            handler_event.clear()
            resp = await self.make_reqest(client=client)
            assert resp.status == 200
            await asyncio.wait_for(handler_event.wait(), timeout=3)
            await asyncio.wait_for(method_called_event.wait(), timeout=3)
            # Python 3.12 had some changes to asyncio which make it quite a bit faster. But
            # probably because of that the assert_awaited call is consistently scheduled before the
            # silent_call_request call - failing the test. So we wait for the method to be called
            # before asserting if it has been awaited.
            mocked_silent_call_request.assert_awaited()
        result = await resp.json()
        assert not result

    async def test_verify_secret(self, bot: MockedBot, aiohttp_client):
        app = Application()
        dp = Dispatcher()
        handler = SimpleRequestHandler(
            dispatcher=dp, bot=bot, handle_in_background=False, secret_token="vasya228"
        )
        handler.register(app, path="/webhook")
        client: TestClient = await aiohttp_client(app)
        resp = await self.make_reqest(client=client)
        assert resp.status == 401


class TestTokenBasedRequestHandler:
    async def test_verify_secret(self, bot: MockedBot):
        dispatcher = Dispatcher()
        handler = TokenBasedRequestHandler(dispatcher=dispatcher)
        assert handler.verify_secret("petro328", bot)

    async def test_register(self):
        dispatcher = Dispatcher()
        app = Application()

        handler = TokenBasedRequestHandler(dispatcher=dispatcher)

        assert len(app.router.routes()) == 0
        with pytest.raises(ValueError):
            handler.register(app, path="/webhook")

        assert len(app.router.routes()) == 0
        handler.register(app, path="/webhook/{bot_token}")
        assert len(app.router.routes()) == 1

    async def test_close(self):
        dispatcher = Dispatcher()

        handler = TokenBasedRequestHandler(dispatcher=dispatcher)

        bot1 = handler.bots["42:TEST"] = MockedBot(token="42:TEST")
        bot1.add_result_for(GetMe, ok=True, result=User(id=42, is_bot=True, first_name="Test"))
        assert await bot1.get_me()
        assert not bot1.session.closed
        bot2 = handler.bots["1337:TEST"] = MockedBot(token="1337:TEST")
        bot2.add_result_for(GetMe, ok=True, result=User(id=1337, is_bot=True, first_name="Test"))
        assert await bot2.get_me()
        assert not bot2.session.closed

        await handler.close()
        assert bot1.session.closed
        assert bot2.session.closed

    async def test_resolve_bot(self):
        dispatcher = Dispatcher()
        handler = TokenBasedRequestHandler(dispatcher=dispatcher)

        @dataclass
        class FakeRequest:
            match_info: dict[str, Any]

        bot1 = await handler.resolve_bot(request=FakeRequest(match_info={"bot_token": "42:TEST"}))
        assert bot1.id == 42

        bot2 = await handler.resolve_bot(
            request=FakeRequest(match_info={"bot_token": "1337:TEST"})
        )
        assert bot2.id == 1337

        bot3 = await handler.resolve_bot(
            request=FakeRequest(match_info={"bot_token": "1337:TEST"})
        )
        assert bot3.id == 1337

        assert bot2 == bot3
        assert len(handler.bots) == 2
