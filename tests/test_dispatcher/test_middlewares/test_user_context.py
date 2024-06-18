from unittest.mock import patch

import pytest

from aiogram.dispatcher.middlewares.user_context import (
    EventContext,
    UserContextMiddleware,
)
from aiogram.types import Chat, Update, User


async def next_handler(*args, **kwargs):
    pass


class TestUserContextMiddleware:
    async def test_unexpected_event_type(self):
        with pytest.raises(RuntimeError):
            await UserContextMiddleware()(next_handler, object(), {})

    async def test_call(self):
        middleware = UserContextMiddleware()
        data = {}

        chat = Chat(id=1, type="private", title="Test")
        user = User(id=2, first_name="Test", is_bot=False)
        thread_id = 3

        with patch.object(
            UserContextMiddleware,
            "resolve_event_context",
            return_value=EventContext(user=user, chat=chat, thread_id=3),
        ):
            await middleware(next_handler, Update(update_id=42), data)

        event_context = data["event_context"]
        assert isinstance(event_context, EventContext)
        assert event_context.chat is chat
        assert event_context.user is user
        assert event_context.thread_id == thread_id
        assert data["event_chat"] is chat
        assert data["event_from_user"] is user
        assert data["event_thread_id"] == thread_id
