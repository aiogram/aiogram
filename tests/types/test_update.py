from aiogram import types
from .dataset import UPDATE

update = types.Update(**UPDATE)


def test_export():
    exported = update.to_python()
    assert isinstance(exported, dict)
    assert exported == UPDATE


def test_update_id():
    assert isinstance(update.update_id, int)
    # assert hash(update) == UPDATE['update_id']
    assert update.update_id == UPDATE['update_id']


def test_message():
    assert isinstance(update.message, types.Message)
