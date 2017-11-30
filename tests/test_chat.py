from aiogram import types
from .dataset import CHAT

chat = types.Chat(**CHAT)


def test_export():
    exported = chat.to_python()
    assert isinstance(exported, dict)
    assert exported == CHAT


def test_id():
    assert isinstance(chat.id, int)
    assert chat.id == CHAT['id']
    assert hash(chat) == CHAT['id']


def test_name():
    assert isinstance(chat.first_name, str)
    assert chat.first_name == CHAT['first_name']

    assert isinstance(chat.last_name, str)
    assert chat.last_name == CHAT['last_name']

    assert isinstance(chat.username, str)
    assert chat.username == CHAT['username']


def test_type():
    assert isinstance(chat.type, str)
    assert chat.type == CHAT['type']


def test_chat_types():
    assert types.ChatType.PRIVATE == 'private'
    assert types.ChatType.GROUP == 'group'
    assert types.ChatType.SUPER_GROUP == 'supergroup'
    assert types.ChatType.CHANNEL == 'channel'


def test_chat_type_filters():
    from . import test_message
    assert types.ChatType.is_private(test_message.message)
    assert not types.ChatType.is_group(test_message.message)
    assert not types.ChatType.is_super_group(test_message.message)
    assert not types.ChatType.is_group_or_super_group(test_message.message)
    assert not types.ChatType.is_channel(test_message.message)
