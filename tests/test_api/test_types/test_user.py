import pytest

from aiogram.types import User


class TestUser:
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
    def test_get_mention_html(self, first: str, last: str, result: bool):
        user = User(id=42, is_bot=False, first_name=first, last_name=last)
        assert user.mention_html()