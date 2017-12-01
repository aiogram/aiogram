from aiogram import types
from .dataset import ANIMATION

animation = types.Animation(**ANIMATION)


def test_export():
    exported = animation.to_python()
    assert isinstance(exported, dict)
    assert exported == ANIMATION


def test_file_name():
    assert isinstance(animation.file_name, str)
    assert animation.file_name == ANIMATION['file_name']


def test_mime_type():
    assert isinstance(animation.mime_type, str)
    assert animation.mime_type == ANIMATION['mime_type']


def test_file_id():
    assert isinstance(animation.file_id, str)
    # assert hash(animation) == ANIMATION['file_id']
    assert animation.file_id == ANIMATION['file_id']


def test_file_size():
    assert isinstance(animation.file_size, int)
    assert animation.file_size == ANIMATION['file_size']


def test_thumb():
    assert isinstance(animation.thumb, types.PhotoSize)
    assert animation.thumb.file_id == ANIMATION['thumb']['file_id']
    assert animation.thumb.width == ANIMATION['thumb']['width']
    assert animation.thumb.height == ANIMATION['thumb']['height']
    assert animation.thumb.file_size == ANIMATION['thumb']['file_size']
