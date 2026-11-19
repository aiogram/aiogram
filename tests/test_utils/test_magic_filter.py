from dataclasses import dataclass
from re import Match

from aiogram import F
from aiogram.utils.magic_filter import MagicFilter


@dataclass
class MyObject:
    text: str


class TestMagicFilter:
    def test_operation_as(self):
        magic: MagicFilter = F.text.regexp(r"^(\d+)$").as_("match")

        assert not magic.resolve(MyObject(text="test"))

        result = magic.resolve(MyObject(text="123"))
        assert isinstance(result, dict)
        assert isinstance(result["match"], Match)

    def test_operation_as_not_none(self):
        # Issue: https://github.com/aiogram/aiogram/issues/1281
        magic = F.cast(int).as_("value")

        result = magic.resolve("0")
        assert result == {"value": 0}

    def test_operation_as_not_none_iterable(self):
        # Issue: https://github.com/aiogram/aiogram/issues/1281
        magic = F.as_("value")

        result = magic.resolve([])
        assert result is None

    def test_operation_as_false_is_a_match(self):
        # Documented: only `None` and empty collections are "no match" for `.as_()`
        magic = (F.text == "secret").as_("value")

        assert magic.resolve(MyObject(text="test")) == {"value": False}
        assert magic.resolve(MyObject(text="secret")) == {"value": True}

    def test_operation_as_false_rejected_explicitly(self):
        magic = (
            (F.text == "secret").func(lambda value: None if value is False else value).as_("value")
        )

        assert magic.resolve(MyObject(text="test")) is None
        assert magic.resolve(MyObject(text="secret")) == {"value": True}
