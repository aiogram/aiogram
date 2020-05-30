import pytest

from aiogram.api.types import User


class TestUser:
    @pytest.mark.parametrize(
        "first_name, last_name, expected_full_name",
        [
            ["User", None, "User"],
            ["User", "", "User"],
            ["User", " ", "User  "],
            ["User", "Name", "User Name"],
            [" User", "Name", " User Name"],
            ["User ", "Name", "User  Name"],
            ["", None, ""],
            ["", "", ""],
            ["", " ", "  "],
            [" ", None, " "],
            [" ", "", " "],
            [" ", " ", "   "],
        ],
    )
    def test_full_name(self, first_name: str, last_name: str, expected_full_name: str):
        user = User(id=42, is_bot=False, first_name=first_name, last_name=last_name)
        assert user.full_name == expected_full_name
