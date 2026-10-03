from aiogram import Bot
from aiogram.client.session.middlewares.base import (
    BaseRequestMiddleware,
    NextRequestMiddlewareType,
)
from aiogram.client.session.middlewares.manager import RequestMiddlewareManager
from aiogram.methods import TelegramMethod
from aiogram.types import TelegramObject


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
                make_request: NextRequestMiddlewareType,
                bot: Bot,
                method: TelegramMethod[TelegramObject],
            ) -> TelegramObject:
                return await make_request(bot, method)

        manager.register(MyMiddleware())

        @manager()
        @manager
        async def middleware(make_request, bot, method):
            return await make_request(bot, method)

        async def target_call(bot, method, timeout: int = None):
            return timeout

        assert await manager.wrap_middlewares(target_call, timeout=42)(None, None) == 42

    async def test_middleware_receives_decoded_result(self):
        # Session middlewares work with the decoded Bot API result,
        # not with the raw Response envelope (see #1723)
        manager = RequestMiddlewareManager()
        sentinel = object()

        async def target_call(bot, method):
            return sentinel

        seen = []

        @manager
        async def middleware(make_request, bot, method):
            result = await make_request(bot, method)
            seen.append(result)
            return result

        wrapped = manager.wrap_middlewares(target_call)
        assert await wrapped(None, None) is sentinel
        assert seen == [sentinel]
