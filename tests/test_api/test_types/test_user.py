from unittest import mock
from unittest.mock import PropertyMock, _patch

import pytest

from aiogram import Bot
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

    @pytest.mark.parametrize(
        "name, as_html, bot_parse_mode, expected_mention",
        [
            ["Markdown User", False, None, "[Markdown User](tg://user?id=42)"],
            ["HTML User", True, None, '<a href="tg://user?id=42">HTML User</a>'],
            ["HTML Bot", None, "HTML", '<a href="tg://user?id=42">HTML Bot</a>'],
            ["Lowercase html", None, "html", '<a href="tg://user?id=42">Lowercase html</a>'],
            ["MarkdownV2 Bot", None, "MarkdownV2", "[MarkdownV2 Bot](tg://user?id=42)"],
            [None, True, "Markdown", '<a href="tg://user?id=42">User Name</a>'],
            [None, False, "Markdown", "[User Name](tg://user?id=42)"],
        ],
    )
    @mock.patch("aiogram.api.types.User.bot", new_callable=PropertyMock)
    def test_get_mention(
        self,
        mock_bot_property: _patch,
        name: str,
        as_html: bool,
        bot_parse_mode: str,
        expected_mention: str,
    ):
        user = User(id=42, is_bot=False, first_name="User", last_name="Name")
        mock_bot_property.return_value = Bot(token="42:TEST", parse_mode=bot_parse_mode)
        assert user.get_mention(name, as_html) == expected_mention
