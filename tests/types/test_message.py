import datetime

from aiogram import types

from .dataset import MESSAGE

message = types.Message(**MESSAGE)


def test_export():
    exported_chat = message.to_python()
    if not isinstance(exported_chat, dict):
        raise AssertionError
    if exported_chat != MESSAGE:
        raise AssertionError


def test_message_id():
    # assert hash(message) == MESSAGE['message_id']
    if message.message_id != MESSAGE['message_id']:
        raise AssertionError
    if message['message_id'] != MESSAGE['message_id']:
        raise AssertionError


def test_from():
    if not isinstance(message.from_user, types.User):
        raise AssertionError
    if message.from_user != message['from']:
        raise AssertionError


def test_chat():
    if not isinstance(message.chat, types.Chat):
        raise AssertionError
    if message.chat != message['chat']:
        raise AssertionError


def test_date():
    if not isinstance(message.date, datetime.datetime):
        raise AssertionError
    if int(message.date.timestamp()) != MESSAGE['date']:
        raise AssertionError
    if message.date != message['date']:
        raise AssertionError


def test_text():
    if message.text != MESSAGE['text']:
        raise AssertionError
    if message['text'] != MESSAGE['text']:
        raise AssertionError
