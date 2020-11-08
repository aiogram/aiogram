from aiogram import types

from .dataset import GAME

game = types.Game(**GAME)


def test_export():
    exported = game.to_python()
    if not isinstance(exported, dict):
        raise AssertionError
    if exported != GAME:
        raise AssertionError


def test_title():
    if not isinstance(game.title, str):
        raise AssertionError
    if game.title != GAME["title"]:
        raise AssertionError


def test_description():
    if not isinstance(game.description, str):
        raise AssertionError
    if game.description != GAME["description"]:
        raise AssertionError


def test_photo():
    if not isinstance(game.photo, list):
        raise AssertionError
    if len(game.photo) != len(GAME["photo"]):
        raise AssertionError
    if not all(map(lambda t: isinstance(t, types.PhotoSize), game.photo)):
        raise AssertionError


def test_animation():
    if not isinstance(game.animation, types.Animation):
        raise AssertionError
