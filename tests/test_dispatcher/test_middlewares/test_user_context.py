from unittest.mock import patch

import pytest

from aiogram.dispatcher.middlewares.user_context import UserContextMiddleware
from aiogram.types import Update


async def next_handler(*args, **kwargs):
    pass


class TestUserContextMiddleware:
    async def test_unexpected_event_type(self):
        with pytest.raises(RuntimeError):
            await UserContextMiddleware()(next_handler, object(), {})

    async def test_call(self):
        middleware = UserContextMiddleware()
        data = {}
        with patch.object(UserContextMiddleware, "resolve_event_context", return_value=[1, 2, 3]):
            await middleware(next_handler, Update(update_id=42), data)

        assert data["event_chat"] == 1
        assert data["event_from_user"] == 2
        assert data["event_thread_id"] == 3
