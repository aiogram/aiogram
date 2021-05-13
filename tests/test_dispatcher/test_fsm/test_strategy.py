import pytest

from aiogram.dispatcher.fsm.strategy import FSMStrategy, apply_strategy


class TestStrategy:
    @pytest.mark.parametrize(
        "strategy,case,expected",
        [
            [FSMStrategy.USER_IN_CHAT, (-42, 42), (-42, 42)],
            [FSMStrategy.CHAT, (-42, 42), (-42, -42)],
            [FSMStrategy.GLOBAL_USER, (-42, 42), (42, 42)],
            [FSMStrategy.USER_IN_CHAT, (42, 42), (42, 42)],
            [FSMStrategy.CHAT, (42, 42), (42, 42)],
            [FSMStrategy.GLOBAL_USER, (42, 42), (42, 42)],
        ],
    )
    def test_strategy(self, strategy, case, expected):
        chat_id, user_id = case
        assert apply_strategy(chat_id=chat_id, user_id=user_id, strategy=strategy) == expected
