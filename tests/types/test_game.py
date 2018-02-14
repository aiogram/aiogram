from aiogram import types
from .dataset import GAME

game = types.Game(**GAME)


def test_export():
    exported = game.to_python()
    assert isinstance(exported, dict)
    assert exported == GAME


def test_title():
    assert isinstance(game.title, str)
    assert game.title == GAME['title']


def test_description():
    assert isinstance(game.description, str)
    assert game.description == GAME['description']


def test_photo():
    assert isinstance(game.photo, list)
    assert len(game.photo) == len(GAME['photo'])
    assert all(map(lambda t: isinstance(t, types.PhotoSize), game.photo))


def test_animation():
    assert isinstance(game.animation, types.Animation)
