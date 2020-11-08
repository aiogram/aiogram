from aiogram import types

from .dataset import ANIMATION

animation = types.Animation(**ANIMATION)


def test_export():
    exported = animation.to_python()
    if not isinstance(exported, dict):
        raise AssertionError
    if exported != ANIMATION:
        raise AssertionError


def test_file_name():
    if not isinstance(animation.file_name, str):
        raise AssertionError
    if animation.file_name != ANIMATION['file_name']:
        raise AssertionError


def test_mime_type():
    if not isinstance(animation.mime_type, str):
        raise AssertionError
    if animation.mime_type != ANIMATION['mime_type']:
        raise AssertionError


def test_file_id():
    if not isinstance(animation.file_id, str):
        raise AssertionError
    # assert hash(animation) == ANIMATION['file_id']
    if animation.file_id != ANIMATION['file_id']:
        raise AssertionError


def test_file_size():
    if not isinstance(animation.file_size, int):
        raise AssertionError
    if animation.file_size != ANIMATION['file_size']:
        raise AssertionError


def test_thumb():
    if not isinstance(animation.thumb, types.PhotoSize):
        raise AssertionError
    if animation.thumb.file_id != ANIMATION['thumb']['file_id']:
        raise AssertionError
    if animation.thumb.width != ANIMATION['thumb']['width']:
        raise AssertionError
    if animation.thumb.height != ANIMATION['thumb']['height']:
        raise AssertionError
    if animation.thumb.file_size != ANIMATION['thumb']['file_size']:
        raise AssertionError
