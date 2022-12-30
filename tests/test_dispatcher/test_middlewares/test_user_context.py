import pytest

from aiogram.dispatcher.middlewares.user_context import UserContextMiddleware


async def next_handler(*args, **kwargs):
    pass


class TestUserContextMiddleware:
    async def test_unexpected_event_type(self):
        with pytest.raises(RuntimeError):
            await UserContextMiddleware()(next_handler, object(), {})
