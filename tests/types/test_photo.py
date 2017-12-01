from aiogram import types
from .dataset import PHOTO

photo = types.PhotoSize(**PHOTO)


def test_export():
    exported = photo.to_python()
    assert isinstance(exported, dict)
    assert exported == PHOTO


def test_file_id():
    assert isinstance(photo.file_id, str)
    assert photo.file_id == PHOTO['file_id']


def test_file_size():
    assert isinstance(photo.file_size, int)
    assert photo.file_size == PHOTO['file_size']


def test_size():
    assert isinstance(photo.width, int)
    assert isinstance(photo.height, int)
    assert photo.width == PHOTO['width']
    assert photo.height == PHOTO['height']
