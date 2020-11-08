from aiogram import types

from .dataset import DOCUMENT

document = types.Document(**DOCUMENT)


def test_export():
    exported = document.to_python()
    if not isinstance(exported, dict):
        raise AssertionError
    if exported != DOCUMENT:
        raise AssertionError


def test_file_name():
    if not isinstance(document.file_name, str):
        raise AssertionError
    if document.file_name != DOCUMENT['file_name']:
        raise AssertionError


def test_mime_type():
    if not isinstance(document.mime_type, str):
        raise AssertionError
    if document.mime_type != DOCUMENT['mime_type']:
        raise AssertionError


def test_file_id():
    if not isinstance(document.file_id, str):
        raise AssertionError
    # assert hash(document) == DOCUMENT['file_id']
    if document.file_id != DOCUMENT['file_id']:
        raise AssertionError


def test_file_size():
    if not isinstance(document.file_size, int):
        raise AssertionError
    if document.file_size != DOCUMENT['file_size']:
        raise AssertionError


def test_thumb():
    if document.thumb is not None:
        raise AssertionError
