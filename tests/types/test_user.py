from babel import Locale

from aiogram import types
from .dataset import USER

user = types.User(**USER)


def test_export():
    exported = user.to_python()
    assert isinstance(exported, dict)
    assert exported == USER


def test_id():
    assert isinstance(user.id, int)
    assert user.id == USER['id']
    # assert hash(user) == USER['id']


def test_bot():
    assert isinstance(user.is_bot, bool)
    assert user.is_bot == USER['is_bot']


def test_name():
    assert user.first_name == USER['first_name']
    assert user.last_name == USER['last_name']
    assert user.username == USER['username']


def test_language_code():
    assert user.language_code == USER['language_code']
    assert user.locale == Locale.parse(USER['language_code'], sep='-')


def test_full_name():
    assert user.full_name == f"{USER['first_name']} {USER['last_name']}"


def test_mention():
    assert user.mention == f"@{USER['username']}"
    assert user.get_mention('foo', as_html=False) == f"[foo](tg://user?id={USER['id']})"
    assert user.get_mention('foo', as_html=True) == f"<a href=\"tg://user?id={USER['id']}\">foo</a>"


def test_url():
    assert user.url == f"tg://user?id={USER['id']}"
