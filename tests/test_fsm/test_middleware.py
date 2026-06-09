from aiogram.fsm.middleware import FSMContextMiddleware
from aiogram.fsm.storage.memory import DisabledEventIsolation, MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from tests.mocked_bot import MockedBot

CHANNEL_ID = -1001234567890
THREAD_ID = 42


def create_middleware(strategy: FSMStrategy) -> FSMContextMiddleware:
    return FSMContextMiddleware(
        storage=MemoryStorage(),
        events_isolation=DisabledEventIsolation(),
        strategy=strategy,
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
