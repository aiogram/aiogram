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
    # assert hash(chat) == CHAT['id']


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


def test_chat_actions():
    assert types.ChatActions.TYPING == 'typing'
    assert types.ChatActions.UPLOAD_PHOTO == 'upload_photo'
    assert types.ChatActions.RECORD_VIDEO == 'record_video'
    assert types.ChatActions.UPLOAD_VIDEO == 'upload_video'
    assert types.ChatActions.RECORD_AUDIO == 'record_audio'
    assert types.ChatActions.UPLOAD_AUDIO == 'upload_audio'
    assert types.ChatActions.UPLOAD_DOCUMENT == 'upload_document'
    assert types.ChatActions.FIND_LOCATION == 'find_location'
    assert types.ChatActions.RECORD_VIDEO_NOTE == 'record_video_note'
    assert types.ChatActions.UPLOAD_VIDEO_NOTE == 'upload_video_note'
