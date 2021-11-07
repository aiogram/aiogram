from typing import Any

import pytest
from aiohttp.web_app import Application

from aiogram import Dispatcher
from aiogram.dispatcher.webhook.aiohttp_server import ip_filter_middleware, setup_application
from aiogram.dispatcher.webhook.security import IPFilter
from aiogram.methods import Request


class TestAiohttpServer:
    def test_setup_application(self):
        app = Application()

        dp = Dispatcher()
        setup_application(app, dp)

        assert len(app.router.routes()) == 0
        assert len(app.on_startup) == 2
        assert len(app.on_shutdown) == 1

    async def test_middleware(self, aiohttp_client: Any):
        app = Application()
        app.middlewares.append(ip_filter_middleware(IPFilter.default()))

        async def handler1(request: Request):
            pass

        async def handler2(request: Request):
            pytest.fail()

        app.router.add_route("POST", "/good", handler1)
        app.router.add_route("POST", "/bad", handler2)
        client = await aiohttp_client(app)
        resp = await client.get("/bad")
        assert resp
