import datetime

from aiogram import types
from .dataset import MESSAGE

message = types.Message(**MESSAGE)


def test_export():
    exported_chat = message.to_python()
    assert isinstance(exported_chat, dict)
    assert exported_chat == MESSAGE


def test_message_id():
    # assert hash(message) == MESSAGE['message_id']
    assert message.message_id == MESSAGE['message_id']
    assert message['message_id'] == MESSAGE['message_id']


def test_from():
    assert isinstance(message.from_user, types.User)
    assert message.from_user == message['from']


def test_chat():
    assert isinstance(message.chat, types.Chat)
    assert message.chat == message['chat']


def test_date():
    assert isinstance(message.date, datetime.datetime)
    assert int(message.date.timestamp()) == MESSAGE['date']
    assert message.date == message['date']


def test_text():
    assert message.text == MESSAGE['text']
    assert message['text'] == MESSAGE['text']
