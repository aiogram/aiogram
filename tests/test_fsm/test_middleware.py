from datetime import datetime

import pytest

from aiogram import Dispatcher
from aiogram.dispatcher.middlewares.user_context import EVENT_CONTEXT_KEY, EventContext
from aiogram.fsm.middleware import FSMContextMiddleware
from aiogram.fsm.storage.memory import DisabledEventIsolation, MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram.types import Chat, Message, Update, User
from tests.mocked_bot import MockedBot

CHANNEL_ID = -1001234567890
THREAD_ID = 42
GROUP_ID = -1001
CHANNEL_BOT = User(id=136817688, is_bot=True, first_name="Channel", username="Channel_Bot")


def create_middleware(
    strategy: FSMStrategy, key_on_sender_chat: bool = False
) -> FSMContextMiddleware:
    return FSMContextMiddleware(
        storage=MemoryStorage(),
        events_isolation=DisabledEventIsolation(),
        strategy=strategy,
        key_on_sender_chat=key_on_sender_chat,
    )


class TestFSMContextMiddleware:
    def test_resolve_context_for_channel_in_chat_strategy(self):
        bot = MockedBot()
        middleware = create_middleware(FSMStrategy.CHAT)

        context = middleware.resolve_context(
            bot=bot,
            chat_id=CHANNEL_ID,
            user_id=None,
        )

        assert context is not None
        assert context.key.chat_id == CHANNEL_ID
        assert context.key.user_id == CHANNEL_ID

    def test_resolve_context_with_missing_user_in_chat_topic_strategy_uses_chat_id_for_user_id(
        self,
    ):
        """
        When user_id is absent (e.g., channel-like updates), chat-scoped strategies
        should still build a stable FSM key by mirroring chat_id into user_id.
        """
        bot = MockedBot()
        middleware = create_middleware(FSMStrategy.CHAT_TOPIC)

        context = middleware.resolve_context(
            bot=bot,
            chat_id=CHANNEL_ID,
            user_id=None,
            thread_id=THREAD_ID,
        )

        assert context is not None
        assert context.key.chat_id == CHANNEL_ID
        assert context.key.user_id == CHANNEL_ID
        assert context.key.thread_id == THREAD_ID

    def test_resolve_context_for_channel_in_user_in_chat_strategy(self):
        bot = MockedBot()
        middleware = create_middleware(FSMStrategy.USER_IN_CHAT)

        context = middleware.resolve_context(
            bot=bot,
            chat_id=CHANNEL_ID,
            user_id=None,
        )

        assert context is None

    def test_resolve_context_for_channel_in_global_user_strategy(self):
        bot = MockedBot()
        middleware = create_middleware(FSMStrategy.GLOBAL_USER)

        context = middleware.resolve_context(
            bot=bot,
            chat_id=CHANNEL_ID,
            user_id=None,
        )

        assert context is None

    def test_resolve_context_for_channel_in_user_in_topic_strategy(self):
        bot = MockedBot()
        middleware = create_middleware(FSMStrategy.USER_IN_TOPIC)

        context = middleware.resolve_context(
            bot=bot,
            chat_id=CHANNEL_ID,
            user_id=None,
            thread_id=THREAD_ID,
        )

        assert context is None

    def test_resolve_event_context_passes_is_guest(self):
        bot = MockedBot()
        middleware = create_middleware(FSMStrategy.CHAT)
        chat = Chat(id=200, type="private")
        user = User(id=100, is_bot=False, first_name="Test")

        guest = middleware.resolve_event_context(
            bot, {EVENT_CONTEXT_KEY: EventContext(chat=chat, user=user, is_guest=True)}
        )
        own = middleware.resolve_event_context(
            bot, {EVENT_CONTEXT_KEY: EventContext(chat=chat, user=user)}
        )

        assert guest is not None
        assert own is not None
        assert guest.key.is_guest is True
        assert own.key.is_guest is False
        assert guest.key != own.key

    def test_get_context_is_guest_keyword(self):
        bot = MockedBot()
        middleware = create_middleware(FSMStrategy.USER_IN_CHAT)

        assert middleware.get_context(bot, 1, 2).key.is_guest is False
        assert middleware.get_context(bot, 1, 2, is_guest=True).key.is_guest is True

    @pytest.mark.parametrize(
        "key_on_sender_chat,chat,sender_chat,expected_user_id",
        [
            # Disabled by default: the placeholder sender user is used
            [
                False,
                Chat(id=GROUP_ID, type="supergroup"),
                Chat(id=-2001, type="channel"),
                CHANNEL_BOT.id,
            ],
            [
                True,
                Chat(id=GROUP_ID, type="supergroup"),
                Chat(id=-2001, type="channel"),
                -2001,
            ],
            # Anonymous group administrator
            [
                True,
                Chat(id=GROUP_ID, type="supergroup"),
                Chat(id=GROUP_ID, type="supergroup"),
                GROUP_ID,
            ],
            # No sender chat
            [True, Chat(id=GROUP_ID, type="supergroup"), None, CHANNEL_BOT.id],
            # Channels are not affected
            [True, Chat(id=CHANNEL_ID, type="channel"), Chat(id=-2001, type="channel"), None],
        ],
    )
    def test_key_on_sender_chat(
        self,
        key_on_sender_chat: bool,
        chat: Chat,
        sender_chat: Chat | None,
        expected_user_id: int | None,
    ):
        bot = MockedBot()
        middleware = create_middleware(
            FSMStrategy.USER_IN_CHAT, key_on_sender_chat=key_on_sender_chat
        )
        user = None if chat.type == "channel" else CHANNEL_BOT
        event_context = EventContext(chat=chat, user=user, sender_chat=sender_chat)

        context = middleware.resolve_event_context(bot, {EVENT_CONTEXT_KEY: event_context})

        if expected_user_id is None:
            assert context is None
        else:
            assert context is not None
            assert context.key.chat_id == chat.id
            assert context.key.user_id == expected_user_id

    @pytest.mark.parametrize("fsm_key_on_sender_chat", [False, True])
    async def test_dispatcher_fsm_key_on_sender_chat(
        self, bot: MockedBot, fsm_key_on_sender_chat: bool
    ):
        dispatcher = Dispatcher(fsm_key_on_sender_chat=fsm_key_on_sender_chat)
        assert dispatcher.fsm.key_on_sender_chat is fsm_key_on_sender_chat
        assert "fsm_key_on_sender_chat" not in dispatcher.workflow_data
        keys = []

        @dispatcher.message()
        async def handler(message: Message, state):
            keys.append(state.key)

        for update_id, sender_chat_id in enumerate([-2001, -2002], start=1):
            update = Update(
                update_id=update_id,
                message=Message(
                    message_id=update_id,
                    date=datetime.now(),
                    chat=Chat(id=GROUP_ID, type="supergroup"),
                    from_user=CHANNEL_BOT,
                    sender_chat=Chat(id=sender_chat_id, type="channel"),
                    text="test",
                ),
            )
            await dispatcher.feed_update(bot, update)

        if fsm_key_on_sender_chat:
            assert [key.user_id for key in keys] == [-2001, -2002]
        else:
            assert [key.user_id for key in keys] == [CHANNEL_BOT.id, CHANNEL_BOT.id]
