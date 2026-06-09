from unittest.mock import patch

import pytest

from aiogram import F
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.dispatcher.flags import (
    check_flags,
    extract_flags,
    extract_flags_from_object,
    get_flag,
)


class TestGetters:
    def test_extract_flags_from_object(self):
        def func():
            pass

        assert extract_flags_from_object(func) == {}

        func.aiogram_flag = {"test": True}
        assert extract_flags_from_object(func) == func.aiogram_flag

    @pytest.mark.parametrize(
        "obj,result",
        [
            [None, {}],
            [{}, {}],
            [{"handler": None}, {}],
            [{"handler": HandlerObject(lambda: True, flags={"test": True})}, {"test": True}],
        ],
    )
    def test_extract_flags(self, obj, result):
        assert extract_flags(obj) == result

    @pytest.mark.parametrize(
        "obj,name,default,result",
        [
            [None, "test", None, None],
            [None, "test", 42, 42],
            [{}, "test", None, None],
            [{}, "test", 42, 42],
            [{"handler": None}, "test", None, None],
            [{"handler": None}, "test", 42, 42],
            [{"handler": HandlerObject(lambda: True, flags={"test": True})}, "test", None, True],
            [{"handler": HandlerObject(lambda: True, flags={"test": True})}, "test2", None, None],
            [{"handler": HandlerObject(lambda: True, flags={"test": True})}, "test2", 42, 42],
        ],
    )
    def test_get_flag(self, obj, name, default, result):
        assert get_flag(obj, name, default=default) == result

    @pytest.mark.parametrize(
        "flags,magic,result",
        [
            [{}, F.test, None],
            [{"test": True}, F.test, True],
            [{"test": True}, F.spam, None],
        ],
    )
    def test_check_flag(self, flags, magic, result):
        with patch("aiogram.dispatcher.flags.extract_flags", return_value=flags):
            assert check_flags(object(), magic) == result
