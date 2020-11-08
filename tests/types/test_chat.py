from aiogram import types

from .dataset import CHAT

chat = types.Chat(**CHAT)


def test_export():
    exported = chat.to_python()
    if not isinstance(exported, dict):
        raise AssertionError
    if exported != CHAT:
        raise AssertionError


def test_id():
    if not isinstance(chat.id, int):
        raise AssertionError
    if chat.id != CHAT['id']:
        raise AssertionError
    # assert hash(chat) == CHAT['id']


def test_name():
    if not isinstance(chat.first_name, str):
        raise AssertionError
    if chat.first_name != CHAT['first_name']:
        raise AssertionError

    if not isinstance(chat.last_name, str):
        raise AssertionError
    if chat.last_name != CHAT['last_name']:
        raise AssertionError

    if not isinstance(chat.username, str):
        raise AssertionError
    if chat.username != CHAT['username']:
        raise AssertionError


def test_type():
    if not isinstance(chat.type, str):
        raise AssertionError
    if chat.type != CHAT['type']:
        raise AssertionError


def test_chat_types():
    if types.ChatType.PRIVATE != 'private':
        raise AssertionError
    if types.ChatType.GROUP != 'group':
        raise AssertionError
    if types.ChatType.SUPER_GROUP != 'supergroup':
        raise AssertionError
    if types.ChatType.CHANNEL != 'channel':
        raise AssertionError


def test_chat_type_filters():
    from . import test_message
    if not types.ChatType.is_private(test_message.message):
        raise AssertionError
    if types.ChatType.is_group(test_message.message):
        raise AssertionError
    if types.ChatType.is_super_group(test_message.message):
        raise AssertionError
    if types.ChatType.is_group_or_super_group(test_message.message):
        raise AssertionError
    if types.ChatType.is_channel(test_message.message):
        raise AssertionError


def test_chat_actions():
    if types.ChatActions.TYPING != 'typing':
        raise AssertionError
    if types.ChatActions.UPLOAD_PHOTO != 'upload_photo':
        raise AssertionError
    if types.ChatActions.RECORD_VIDEO != 'record_video':
        raise AssertionError
    if types.ChatActions.UPLOAD_VIDEO != 'upload_video':
        raise AssertionError
    if types.ChatActions.RECORD_AUDIO != 'record_audio':
        raise AssertionError
    if types.ChatActions.UPLOAD_AUDIO != 'upload_audio':
        raise AssertionError
    if types.ChatActions.UPLOAD_DOCUMENT != 'upload_document':
        raise AssertionError
    if types.ChatActions.FIND_LOCATION != 'find_location':
        raise AssertionError
    if types.ChatActions.RECORD_VIDEO_NOTE != 'record_video_note':
        raise AssertionError
    if types.ChatActions.UPLOAD_VIDEO_NOTE != 'upload_video_note':
        raise AssertionError
