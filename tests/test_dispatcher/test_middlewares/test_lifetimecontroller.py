from unittest.mock import AsyncMock

from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware


async def test_no_skip():
    class Middleware(LifetimeControllerMiddleware):
        pre_process = AsyncMock()
        post_process = AsyncMock()

    m = Middleware()
    await m.trigger("pre_process_update_xxx", [1, 2, 3])
    m.pre_process.assert_called_once_with(1, 3, 2)
    m.post_process.assert_not_called()
    await m.trigger("post_process_update_xxx", [1, 2, 3])
    m.pre_process.reset_mock()
    m.pre_process.assert_not_called()
    m.post_process.assert_called_once_with(1, 3, 2)


async def test_skip_prefix():
    class Middleware(LifetimeControllerMiddleware):
        skip_patterns = ["update"]
        pre_process = AsyncMock()
        post_process = AsyncMock()

    m = Middleware()
    await m.trigger("pre_process_update_xxx", [1, 2, 3])
    m.pre_process.assert_called_once_with(1, 3, 2)
    m.post_process.assert_not_called()
    await m.trigger("post_process_update_xxx", [1, 2, 3])
    m.pre_process.reset_mock()
    m.pre_process.assert_not_called()
    m.post_process.assert_called_once_with(1, 3, 2)


async def test_skip():
    class Middleware(LifetimeControllerMiddleware):
        skip_patterns = ["update_xxx"]
        pre_process = AsyncMock()
        post_process = AsyncMock()

    m = Middleware()
    await m.trigger("pre_process_update_xxx", [1, 2, 3])
    m.pre_process.assert_not_called()
    m.post_process.assert_not_called()
    await m.trigger("post_process_update_xxx", [1, 2, 3])
    m.pre_process.reset_mock()
    m.pre_process.assert_not_called()
    m.post_process.assert_not_called()
