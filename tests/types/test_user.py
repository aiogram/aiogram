from babel import Locale

from aiogram import types

from .dataset import USER

user = types.User(**USER)


def test_export():
    exported = user.to_python()
    if not isinstance(exported, dict):
        raise AssertionError
    if exported != USER:
        raise AssertionError


def test_id():
    if not isinstance(user.id, int):
        raise AssertionError
    if user.id != USER["id"]:
        raise AssertionError
    # assert hash(user) == USER['id']


def test_bot():
    if not isinstance(user.is_bot, bool):
        raise AssertionError
    if user.is_bot != USER["is_bot"]:
        raise AssertionError


def test_name():
    if user.first_name != USER["first_name"]:
        raise AssertionError
    if user.last_name != USER["last_name"]:
        raise AssertionError
    if user.username != USER["username"]:
        raise AssertionError


def test_language_code():
    if user.language_code != USER["language_code"]:
        raise AssertionError
    if user.locale != Locale.parse(USER["language_code"], sep="-"):
        raise AssertionError


def test_full_name():
    if user.full_name != f"{USER['first_name']} {USER['last_name']}":
        raise AssertionError


def test_mention():
    if user.mention != f"@{USER['username']}":
        raise AssertionError
    if user.get_mention("foo", as_html=False) != f"[foo](tg://user?id={USER['id']})":
        raise AssertionError
    if (
        user.get_mention("foo", as_html=True)
        != f"<a href=\"tg://user?id={USER['id']}\">foo</a>"
    ):
        raise AssertionError


def test_url():
    if user.url != f"tg://user?id={USER['id']}":
        raise AssertionError
