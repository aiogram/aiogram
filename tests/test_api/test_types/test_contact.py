import pytest

from aiogram.types import Contact


class TestContact:
    @pytest.mark.parametrize(
        "first,last,result",
        [
            ["User", None, "User"],
            ["", None, ""],
            [" ", None, " "],
            ["User", "Name", "User Name"],
            ["User", " ", "User  "],
            [" ", " ", "   "],
        ],
    )
    def test_full_name(self, first: str, last: str, result: bool):
        contact = Contact(phone_number="911", first_name=first, last_name=last)
        assert contact.full_name == result
