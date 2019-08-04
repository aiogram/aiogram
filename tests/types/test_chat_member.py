from aiogram import types
from .dataset import CHAT_MEMBER

chat_member = types.ChatMember(**CHAT_MEMBER)


def test_export():
    exported = chat_member.to_python()
    assert isinstance(exported, dict)
    assert exported == CHAT_MEMBER


def test_user():
    assert isinstance(chat_member.user, types.User)


def test_status():
    assert isinstance(chat_member.status, str)
    assert chat_member.status == CHAT_MEMBER['status']


def test_privileges():
    assert isinstance(chat_member.can_be_edited, bool)
    assert chat_member.can_be_edited == CHAT_MEMBER['can_be_edited']

    assert isinstance(chat_member.can_change_info, bool)
    assert chat_member.can_change_info == CHAT_MEMBER['can_change_info']

    assert isinstance(chat_member.can_delete_messages, bool)
    assert chat_member.can_delete_messages == CHAT_MEMBER['can_delete_messages']

    assert isinstance(chat_member.can_invite_users, bool)
    assert chat_member.can_invite_users == CHAT_MEMBER['can_invite_users']

    assert isinstance(chat_member.can_restrict_members, bool)
    assert chat_member.can_restrict_members == CHAT_MEMBER['can_restrict_members']

    assert isinstance(chat_member.can_pin_messages, bool)
    assert chat_member.can_pin_messages == CHAT_MEMBER['can_pin_messages']

    assert isinstance(chat_member.can_promote_members, bool)
    assert chat_member.can_promote_members == CHAT_MEMBER['can_promote_members']


def test_int():
    assert int(chat_member) == chat_member.user.id
    assert isinstance(int(chat_member), int)


def test_chat_member_status():
    assert types.ChatMemberStatus.CREATOR == 'creator'
    assert types.ChatMemberStatus.ADMINISTRATOR == 'administrator'
    assert types.ChatMemberStatus.MEMBER == 'member'
    assert types.ChatMemberStatus.RESTRICTED == 'restricted'
    assert types.ChatMemberStatus.LEFT == 'left'
    assert types.ChatMemberStatus.KICKED == 'kicked'


def test_chat_member_status_filters():
    assert types.ChatMemberStatus.is_chat_admin(chat_member.status)
    assert types.ChatMemberStatus.is_chat_member(chat_member.status)

    assert types.ChatMemberStatus.is_chat_admin(types.ChatMemberStatus.CREATOR)
    assert types.ChatMemberStatus.is_chat_admin(types.ChatMemberStatus.ADMINISTRATOR)

    assert types.ChatMemberStatus.is_chat_member(types.ChatMemberStatus.CREATOR)
    assert types.ChatMemberStatus.is_chat_member(types.ChatMemberStatus.ADMINISTRATOR)
    assert types.ChatMemberStatus.is_chat_member(types.ChatMemberStatus.MEMBER)
    assert types.ChatMemberStatus.is_chat_member(types.ChatMemberStatus.RESTRICTED)

    assert not types.ChatMemberStatus.is_chat_member(types.ChatMemberStatus.LEFT)
    assert not types.ChatMemberStatus.is_chat_member(types.ChatMemberStatus.KICKED)


def test_chat_member_filters():
    assert chat_member.is_chat_admin()
    assert chat_member.is_chat_member()
