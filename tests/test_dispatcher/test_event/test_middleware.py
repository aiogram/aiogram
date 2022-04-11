from functools import partial

from aiogram.dispatcher.middlewares.manager import MiddlewareManager


class TestMiddlewareManager:
    async def test_register(self):
        manager = MiddlewareManager()

        @manager
        async def middleware(handler, event, data):
            await handler(event, data)

        assert middleware in manager._middlewares
        manager.unregister(middleware)
        assert middleware not in manager._middlewares

    async def test_wrap_middlewares(self):
        manager = MiddlewareManager()

        async def target(*args, **kwargs):
            kwargs["target"] = True
            kwargs["stack"].append(-1)
            return kwargs

        async def middleware1(handler, event, data):
            data["mw1"] = True
            data["stack"].append(1)
            return await handler(event, data)

        async def middleware2(handler, event, data):
            data["mw2"] = True
            data["stack"].append(2)
            return await handler(event, data)

        wrapped = manager.wrap_middlewares([middleware1, middleware2], target)

        assert isinstance(wrapped, partial)
        assert wrapped.func is middleware1

        result = await wrapped(None, {"stack": []})
        assert result == {"mw1": True, "mw2": True, "target": True, "stack": [1, 2, -1]}
