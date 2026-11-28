import pytest

from aiogram.filters import Command, and_f, invert_f, or_f
from aiogram.filters.logic import _AndFilter, _InvertFilter, _OrFilter


class TestLogic:
    @pytest.mark.parametrize(
        "obj,case,result",
        [
            [True, and_f(lambda t: t is True, lambda t: t is True), True],
            [True, and_f(lambda t: t is True, lambda t: t is False), False],
            [True, and_f(lambda t: t is False, lambda t: t is False), False],
            [True, and_f(lambda t: {"r": t}, lambda t: t is False), False],
            [True, and_f(lambda t: {"r": t}, lambda t: t is True), {"r": True}],
            [True, or_f(lambda t: t is True, lambda t: t is True), True],
            [True, or_f(lambda t: t is True, lambda t: t is False), True],
            [True, or_f(lambda t: t is False, lambda t: t is False), False],
            [True, or_f(lambda t: t is False, lambda t: t is True), True],
            [True, or_f(lambda t: t is False, lambda t: {"t": t}), {"t": True}],
            [True, or_f(lambda t: {"t": t}, lambda t: {"a": 42}), {"t": True}],
            [True, invert_f(lambda t: t is False), True],
        ],
    )
    async def test_logic(self, obj, case, result):
        assert await case(obj) == result

    @pytest.mark.parametrize(
        "value,result",
        [
            ["admin", {"role": "admin"}],
            ["guest", False],
        ],
    )
    async def test_and_passes_result_to_next_targets(self, value, result):
        case = and_f(
            lambda event: {"role": event},
            invert_f(lambda event, role=None: role == "guest"),
        )
        assert await case(value) == result

    @pytest.mark.parametrize(
        "case,type_",
        [
            [or_f(Command("test"), Command("test")), _OrFilter],
            [and_f(Command("test"), Command("test")), _AndFilter],
            [invert_f(Command("test")), _InvertFilter],
            [~Command("test"), _InvertFilter],
        ],
    )
    def test_dunder_methods(self, case, type_):
        assert isinstance(case, type_)
