from aiogram import types

from .dataset import UPDATE

update = types.Update(**UPDATE)


def test_export():
    exported = update.to_python()
    if not isinstance(exported, dict):
        raise AssertionError
    if exported != UPDATE:
        raise AssertionError


def test_update_id():
    if not isinstance(update.update_id, int):
        raise AssertionError
    # assert hash(update) == UPDATE['update_id']
    if update.update_id != UPDATE["update_id"]:
        raise AssertionError


def test_message():
    if not isinstance(update.message, types.Message):
        raise AssertionError
