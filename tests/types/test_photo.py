from aiogram import types

from .dataset import PHOTO

photo = types.PhotoSize(**PHOTO)


def test_export():
    exported = photo.to_python()
    if not isinstance(exported, dict):
        raise AssertionError
    if exported != PHOTO:
        raise AssertionError


def test_file_id():
    if not isinstance(photo.file_id, str):
        raise AssertionError
    if photo.file_id != PHOTO['file_id']:
        raise AssertionError


def test_file_size():
    if not isinstance(photo.file_size, int):
        raise AssertionError
    if photo.file_size != PHOTO['file_size']:
        raise AssertionError


def test_size():
    if not isinstance(photo.width, int):
        raise AssertionError
    if not isinstance(photo.height, int):
        raise AssertionError
    if photo.width != PHOTO['width']:
        raise AssertionError
    if photo.height != PHOTO['height']:
        raise AssertionError
