import pytest

from aiogram.dispatcher.filters.builtin import Text


class TestText:
    @pytest.mark.parametrize(
        "param, key",
        [
            ("text", "equals"),
            ("text_contains", "contains"),
            ("text_startswith", "startswith"),
            ("text_endswith", "endswith"),
        ],
    )
    def test_validate(self, param, key):
        value = "spam and eggs"
        config = {param: value}
        res = Text.validate(config)
        assert res == {key: value}
