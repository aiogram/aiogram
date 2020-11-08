from aiogram import types

from .dataset import CHAT_MEMBER

chat_member = types.ChatMember(**CHAT_MEMBER)


def test_export():
    exported = chat_member.to_python()
    if not isinstance(exported, dict):
        raise AssertionError
    if exported != CHAT_MEMBER:
        raise AssertionError


def test_user():
    if not isinstance(chat_member.user, types.User):
        raise AssertionError


def test_status():
    if not isinstance(chat_member.status, str):
        raise AssertionError
    if chat_member.status != CHAT_MEMBER["status"]:
        raise AssertionError


def test_privileges():
    if not isinstance(chat_member.can_be_edited, bool):
        raise AssertionError
    if chat_member.can_be_edited != CHAT_MEMBER["can_be_edited"]:
        raise AssertionError

    if not isinstance(chat_member.can_change_info, bool):
        raise AssertionError
    if chat_member.can_change_info != CHAT_MEMBER["can_change_info"]:
        raise AssertionError

    if not isinstance(chat_member.can_delete_messages, bool):
        raise AssertionError
    if chat_member.can_delete_messages != CHAT_MEMBER["can_delete_messages"]:
        raise AssertionError

    if not isinstance(chat_member.can_invite_users, bool):
        raise AssertionError
    if chat_member.can_invite_users != CHAT_MEMBER["can_invite_users"]:
        raise AssertionError

    if not isinstance(chat_member.can_restrict_members, bool):
        raise AssertionError
    if chat_member.can_restrict_members != CHAT_MEMBER["can_restrict_members"]:
        raise AssertionError

    if not isinstance(chat_member.can_pin_messages, bool):
        raise AssertionError
    if chat_member.can_pin_messages != CHAT_MEMBER["can_pin_messages"]:
        raise AssertionError

    if not isinstance(chat_member.can_promote_members, bool):
        raise AssertionError
    if chat_member.can_promote_members != CHAT_MEMBER["can_promote_members"]:
        raise AssertionError


def test_int():
    if int(chat_member) != chat_member.user.id:
        raise AssertionError
    if not isinstance(int(chat_member), int):
        raise AssertionError


def test_chat_member_status():
    if types.ChatMemberStatus.CREATOR != "creator":
        raise AssertionError
    if types.ChatMemberStatus.ADMINISTRATOR != "administrator":
        raise AssertionError
    if types.ChatMemberStatus.MEMBER != "member":
        raise AssertionError
    if types.ChatMemberStatus.RESTRICTED != "restricted":
        raise AssertionError
    if types.ChatMemberStatus.LEFT != "left":
        raise AssertionError
    if types.ChatMemberStatus.KICKED != "kicked":
        raise AssertionError


def test_chat_member_status_filters():
    if not types.ChatMemberStatus.is_chat_admin(chat_member.status):
        raise AssertionError
    if not types.ChatMemberStatus.is_chat_member(chat_member.status):
        raise AssertionError

    if not types.ChatMemberStatus.is_chat_admin(types.ChatMemberStatus.CREATOR):
        raise AssertionError
    if not types.ChatMemberStatus.is_chat_admin(types.ChatMemberStatus.ADMINISTRATOR):
        raise AssertionError

    if not types.ChatMemberStatus.is_chat_member(types.ChatMemberStatus.CREATOR):
        raise AssertionError
    if not types.ChatMemberStatus.is_chat_member(types.ChatMemberStatus.ADMINISTRATOR):
        raise AssertionError
    if not types.ChatMemberStatus.is_chat_member(types.ChatMemberStatus.MEMBER):
        raise AssertionError
    if not types.ChatMemberStatus.is_chat_member(types.ChatMemberStatus.RESTRICTED):
        raise AssertionError

    if types.ChatMemberStatus.is_chat_member(types.ChatMemberStatus.LEFT):
        raise AssertionError
    if types.ChatMemberStatus.is_chat_member(types.ChatMemberStatus.KICKED):
        raise AssertionError


def test_chat_member_filters():
    if not chat_member.is_chat_admin():
        raise AssertionError
    if not chat_member.is_chat_member():
        raise AssertionError
