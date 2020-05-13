import pytest

from aiogram.api.types import ReplyKeyboardRemove


class TestReplyKeyboardRemove:
    """
    This test is needed to prevent to override value by code generator
    """

    def test_remove_keyboard_default_is_true(self):
        assert (
            ReplyKeyboardRemove.__fields__["remove_keyboard"].default is True
        ), "Remove keyboard has incorrect default value!"

    @pytest.mark.parametrize(
        "kwargs,expected",
        [[{}, True], [{"remove_keyboard": True}, True], [{"remove_keyboard": False}, False]],
    )
    def test_remove_keyboard_values(self, kwargs, expected):
        assert ReplyKeyboardRemove(**kwargs).remove_keyboard is expected
