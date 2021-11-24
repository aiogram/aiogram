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
