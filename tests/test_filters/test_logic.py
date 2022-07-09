import pytest

from aiogram.filters import Text, and_f, invert_f, or_f
from aiogram.filters.logic import _AndFilter, _InvertFilter, _OrFilter


class TestLogic:
    @pytest.mark.parametrize(
        "obj,case,result",
        [
            [True, and_f(lambda t: t is True, lambda t: t is True), True],
            [True, and_f(lambda t: t is True, lambda t: t is False), False],
            [True, and_f(lambda t: t is False, lambda t: t is False), False],
            [True, and_f(lambda t: {"t": t}, lambda t: t is False), False],
            [True, and_f(lambda t: {"t": t}, lambda t: t is True), {"t": True}],
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
        "case,type_",
        [
            [Text(text="test") | Text(text="test"), _OrFilter],
            [Text(text="test") & Text(text="test"), _AndFilter],
            [~Text(text="test"), _InvertFilter],
        ],
    )
    def test_dunder_methods(self, case, type_):
        assert isinstance(case, type_)
