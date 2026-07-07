import pytest

from aiogram.types import ReplyKeyboardRemove


class TestReplyKeyboardRemove:
    """
    This test is needed to prevent to override value by code generator
    """

    def test_remove_keyboard_default_is_true(self):
        assert ReplyKeyboardRemove.model_fields["remove_keyboard"].default is True, (
            "Remove keyboard has incorrect default value!"
        )

    @pytest.mark.parametrize(
        "kwargs,expected",
        [[{}, True], [{"remove_keyboard": True}, True]],
    )
    def test_remove_keyboard_values(self, kwargs: dict[str, bool], expected: bool):
        assert ReplyKeyboardRemove(**kwargs).remove_keyboard is expected
