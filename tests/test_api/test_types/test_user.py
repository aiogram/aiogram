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
    def test_full_name(self, first: str, last: str, result: bool):
        user = User(id=42, is_bot=False, first_name=first, last_name=last)
        assert user.full_name == result

    @pytest.mark.parametrize(
        "first,last,name",
        [
            ["User", None, "bebra"],
            ["", None, "telegram"],
            [" ", None, "queue🤬"],
            ["User", "Name", "Alex"],
            ["User", " ", "aslo "],
            [" ", " ", "telebot"],
        ],
    )
    def test_get_mention_markdown(self, first: str, last: str, name: str):
        user = User(id=42, is_bot=False, first_name=first, last_name=last)
        assert user.mention_markdown() == f"[{user.full_name}](tg://user?id=42)"
        assert user.mention_markdown(name=name) == f"[{name}](tg://user?id=42)"

    @pytest.mark.parametrize(
        "first,last,name",
        [
            ["User", None, "bebra"],
            ["", None, "telegram"],
            [" ", None, "queue🤬"],
            ["User", "Name", "Alex"],
            ["User", " ", "aslo "],
            [" ", " ", "telebot"],
        ],
    )
    def test_get_mention_html(self, first: str, last: str, name: str):
        user = User(id=42, is_bot=False, first_name=first, last_name=last)
        assert user.mention_html() == f'<a href="tg://user?id=42">{user.full_name}</a>'
        assert user.mention_html(name=name) == f'<a href="tg://user?id=42">{name}</a>'

    def test_get_profile_photos(self):
        user = User(id=42, is_bot=False, first_name="Test", last_name="User")

        method = user.get_profile_photos(description="test")
        assert method.user_id == user.id

    def test_get_profile_audios(self):
        user = User(id=42, is_bot=False, first_name="Test", last_name="User")

        method = user.get_profile_audios(description="test")
        assert method.user_id == user.id
