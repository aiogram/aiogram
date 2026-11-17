from datetime import datetime
from unittest.mock import patch

import pytest

from aiogram.dispatcher.middlewares.user_context import (
    EventContext,
    UserContextMiddleware,
)
from aiogram.types import (
    Chat,
    ChatBoost,
    ChatBoostSourceGiftCode,
    ChatBoostSourceGiveaway,
    ChatBoostSourcePremium,
    ChatBoostUpdated,
    Message,
    MessageGenerationStopped,
    SharedWidgetQuery,
    Update,
    User,
    WidgetQuery,
    WidgetQueryTypeData,
)


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

    @pytest.mark.parametrize(
        "source, expected_user",
        [
            (
                ChatBoostSourcePremium(user=User(id=2, first_name="Test", is_bot=False)),
                User(id=2, first_name="Test", is_bot=False),
            ),
            (ChatBoostSourceGiftCode(user=User(id=2, first_name="Test", is_bot=False)), None),
            (
                ChatBoostSourceGiveaway(
                    giveaway_message_id=1, user=User(id=2, first_name="Test", is_bot=False)
                ),
                None,
            ),
        ],
    )
    async def test_resolve_event_context(self, source, expected_user):
        middleware = UserContextMiddleware()
        data = {}

        chat = Chat(id=1, type="private", title="Test")
        add_date = datetime.now()
        expiration_date = datetime.now()

        boost = ChatBoost(
            boost_id="Test", add_date=add_date, expiration_date=expiration_date, source=source
        )
        update = Update(update_id=42, chat_boost=ChatBoostUpdated(chat=chat, boost=boost))

        await middleware(next_handler, update, data)

        event_context = data["event_context"]
        assert isinstance(event_context, EventContext)
        assert event_context.user == expected_user

    async def test_stopped_message_generation_resolves_user(self):
        middleware = UserContextMiddleware()

        chat = Chat(
            id=42,
            type="private",
            first_name="Test",
            last_name="User",
            username="testuser",
        )
        update = Update(
            update_id=1,
            stopped_message_generation=MessageGenerationStopped(chat=chat, draft_id=7),
        )
        data = {}
        await middleware(next_handler, update, data)

        event_context = data["event_context"]
        assert isinstance(event_context, EventContext)
        assert event_context.chat is chat
        assert event_context.user == User(
            id=42,
            is_bot=False,
            first_name="Test",
            last_name="User",
            username="testuser",
        )
        assert event_context.user_id == 42
        assert data["event_from_user"] == event_context.user

    async def test_stopped_message_generation_resolves_user_without_chat_names(self):
        middleware = UserContextMiddleware()

        chat = Chat(id=42, type="private")
        update = Update(
            update_id=1,
            stopped_message_generation=MessageGenerationStopped(chat=chat, draft_id=7),
        )
        data = {}
        await middleware(next_handler, update, data)

        assert data["event_from_user"] == User(id=42, is_bot=False, first_name="")

    @pytest.mark.parametrize("chat", [Chat(id=42, type="private"), None])
    async def test_widget_query(self, chat: Chat | None):
        user = User(id=42, is_bot=False, first_name="Test")
        update = Update(
            update_id=1,
            widget_query=WidgetQuery(
                id="id",
                from_user=user,
                chat_instance="instance",
                type=WidgetQueryTypeData(),
                data="data",
                chat=chat,
            ),
        )
        data = {}
        await UserContextMiddleware()(next_handler, update, data)

        event_context = data["event_context"]
        assert event_context.chat is chat
        assert event_context.user is user

    async def test_shared_widget_query(self):
        user = User(id=42, is_bot=False, first_name="Test")
        update = Update(
            update_id=1,
            shared_widget_query=SharedWidgetQuery(
                id="id",
                from_user=user,
                type=WidgetQueryTypeData(),
                data="data",
                widget_id="widget",
            ),
        )
        data = {}
        await UserContextMiddleware()(next_handler, update, data)

        event_context = data["event_context"]
        assert event_context.chat is None
        assert event_context.user is user

    async def test_guest_message_is_guest(self):
        message = Message(
            message_id=1,
            date=datetime.now(),
            chat=Chat(id=200, type="private"),
            from_user=User(id=100, is_bot=False, first_name="Test"),
            guest_query_id="gq",
        )
        guest_context = UserContextMiddleware.resolve_event_context(
            Update(update_id=1, guest_message=message)
        )
        own_context = UserContextMiddleware.resolve_event_context(
            Update(update_id=2, message=message)
        )

        assert guest_context.is_guest is True
        assert own_context.is_guest is False

    @pytest.mark.parametrize(
        "update_type",
        ["message", "edited_message", "business_message", "edited_business_message"],
    )
    async def test_sender_chat(self, update_type: str):
        sender_chat = Chat(id=-2001, type="channel", title="Channel")
        message = Message(
            message_id=1,
            date=datetime.now(),
            chat=Chat(id=-1001, type="supergroup", title="Group"),
            from_user=User(id=136817688, is_bot=True, first_name="Channel"),
            sender_chat=sender_chat,
        )
        event_context = UserContextMiddleware.resolve_event_context(
            Update(update_id=1, **{update_type: message})
        )

        assert event_context.sender_chat is sender_chat
        assert event_context.user_id == 136817688
