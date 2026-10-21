from aiogram import Bot
from aiogram.client.session.middlewares.base import (
    BaseRequestMiddleware,
    NextRequestMiddlewareType,
)
from aiogram.client.session.middlewares.manager import RequestMiddlewareManager
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType


class TestMiddlewareManager:
    async def test_register(self):
        manager = RequestMiddlewareManager()

        @manager
        async def middleware(handler, event, data):
            await handler(event, data)

        assert middleware in manager._middlewares
        manager.unregister(middleware)
        assert middleware not in manager._middlewares

    async def test_wrap_middlewares(self):
        manager = RequestMiddlewareManager()

        class MyMiddleware(BaseRequestMiddleware):
            async def __call__(
                self,
                make_request: NextRequestMiddlewareType[TelegramType],
                bot: Bot,
                method: TelegramMethod[TelegramType],
            ) -> TelegramType:
                return await make_request(bot, method)

        manager.register(MyMiddleware())

        @manager()
        @manager
        async def middleware(make_request, bot, method):
            return await make_request(bot, method)

        async def target_call(bot, method, timeout: int = None):
            return timeout

        assert await manager.wrap_middlewares(target_call, timeout=42)(None, None) == 42
