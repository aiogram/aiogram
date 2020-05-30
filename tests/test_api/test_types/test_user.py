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

    @pytest.mark.parametrize(
        "user_id, expected_url",
        [
            [42, "tg://user?id=42"],
            [0, "tg://user?id=0"],
            [-9999999999999999, "tg://user?id=-9999999999999999"],
        ],
    )
    def test_url(self, user_id: int, expected_url: str):
        user = User(id=user_id, is_bot=False, first_name="User", last_name="Name")
        assert user.url == expected_url
