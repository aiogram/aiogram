from aiogram import types
from .dataset import DOCUMENT

document = types.Document(**DOCUMENT)


def test_export():
    exported = document.to_python()
    assert isinstance(exported, dict)
    assert exported == DOCUMENT


def test_file_name():
    assert isinstance(document.file_name, str)
    assert document.file_name == DOCUMENT['file_name']


def test_mime_type():
    assert isinstance(document.mime_type, str)
    assert document.mime_type == DOCUMENT['mime_type']


def test_file_id():
    assert isinstance(document.file_id, str)
    # assert hash(document) == DOCUMENT['file_id']
    assert document.file_id == DOCUMENT['file_id']


def test_file_size():
    assert isinstance(document.file_size, int)
    assert document.file_size == DOCUMENT['file_size']


def test_thumb():
    assert document.thumb is None
