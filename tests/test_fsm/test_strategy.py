import pytest

from aiogram.fsm.strategy import FSMStrategy, apply_strategy

CHAT_ID = -42
USER_ID = 42
THREAD_ID = 1

PRIVATE = (USER_ID, USER_ID, None)
CHAT = (CHAT_ID, USER_ID, None)
THREAD = (CHAT_ID, USER_ID, THREAD_ID)


class TestStrategy:
    @pytest.mark.parametrize(
        "strategy,case,expected",
        [
            [FSMStrategy.USER_IN_CHAT, CHAT, CHAT],
            [FSMStrategy.USER_IN_CHAT, PRIVATE, PRIVATE],
            [FSMStrategy.USER_IN_CHAT, THREAD, CHAT],
            [FSMStrategy.CHAT, CHAT, (CHAT_ID, CHAT_ID, None)],
            [FSMStrategy.CHAT, PRIVATE, (USER_ID, USER_ID, None)],
            [FSMStrategy.CHAT, THREAD, (CHAT_ID, CHAT_ID, None)],
            [FSMStrategy.GLOBAL_USER, CHAT, PRIVATE],
            [FSMStrategy.GLOBAL_USER, PRIVATE, PRIVATE],
            [FSMStrategy.GLOBAL_USER, THREAD, PRIVATE],
            [FSMStrategy.USER_IN_TOPIC, CHAT, CHAT],
            [FSMStrategy.USER_IN_TOPIC, PRIVATE, PRIVATE],
            [FSMStrategy.USER_IN_TOPIC, THREAD, THREAD],
            [FSMStrategy.CHAT_TOPIC, CHAT, (CHAT_ID, CHAT_ID, None)],
            [FSMStrategy.CHAT_TOPIC, PRIVATE, PRIVATE],
            [FSMStrategy.CHAT_TOPIC, THREAD, (CHAT_ID, CHAT_ID, THREAD_ID)],
        ],
    )
    def test_strategy(self, strategy, case, expected):
        chat_id, user_id, thread_id = case
        assert (
            apply_strategy(
                chat_id=chat_id,
                user_id=user_id,
                thread_id=thread_id,
                strategy=strategy,
            )
            == expected
        )
