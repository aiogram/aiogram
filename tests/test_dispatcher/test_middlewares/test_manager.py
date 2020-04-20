import pytest

from aiogram import Router
from aiogram.api.types import Update
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.dispatcher.middlewares.manager import MiddlewareManager
from aiogram.dispatcher.middlewares.types import MiddlewareStep

try:
    from asynctest import CoroutineMock, patch
except ImportError:
    from unittest.mock import AsyncMock as CoroutineMock, patch  # type: ignore


@pytest.fixture("function")
def router():
    return Router()


@pytest.fixture("function")
def manager(router: Router):
    return MiddlewareManager(router)


class TestManager:
    def test_setup(self, manager: MiddlewareManager):
        middleware = BaseMiddleware()
        returned = manager.setup(middleware)
        assert returned is middleware
        assert middleware.configured
        assert middleware.manager is manager
        assert middleware in manager

    @pytest.mark.parametrize("obj", [object, object(), None, BaseMiddleware])
    def test_setup_invalid_type(self, manager: MiddlewareManager, obj):
        with pytest.raises(TypeError):
            assert manager.setup(obj)

    def test_configure_twice_different_managers(self, manager: MiddlewareManager, router: Router):
        middleware = BaseMiddleware()
        manager.setup(middleware)

        assert middleware.configured

        new_manager = MiddlewareManager(router)
        with pytest.raises(ValueError):
            new_manager.setup(middleware)
        with pytest.raises(ValueError):
            middleware.setup(new_manager)

    def test_configure_twice(self, manager: MiddlewareManager):
        middleware = BaseMiddleware()
        manager.setup(middleware)

        assert middleware.configured

        with pytest.warns(RuntimeWarning, match="is already configured for this Router"):
            manager.setup(middleware)

        with pytest.warns(RuntimeWarning, match="is already configured for this Router"):
            middleware.setup(manager)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("count", range(5))
    async def test_trigger(self, manager: MiddlewareManager, count: int):
        for _ in range(count):
            manager.setup(BaseMiddleware())

        with patch(
            "aiogram.dispatcher.middlewares.base.BaseMiddleware.trigger",
            new_callable=CoroutineMock,
        ) as mocked_call:
            await manager.trigger(
                step=MiddlewareStep.PROCESS,
                event_name="update",
                event=Update(update_id=42),
                data={},
                result=None,
                reverse=True,
            )

            assert mocked_call.await_count == count
