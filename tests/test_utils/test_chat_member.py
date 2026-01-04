from datetime import datetime

import pytest

from aiogram.types import (
    ChatMember,
    ChatMemberAdministrator,
    ChatMemberBanned,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberRestricted,
    User,
)
from aiogram.utils.chat_member import ChatMemberAdapter

USER = User(
    id=42,
    first_name="John Doe",
    is_bot=False,
).model_dump()

CHAT_MEMBER_ADMINISTRATOR = ChatMemberAdministrator(
    user=USER,
    can_be_edited=False,
    can_manage_chat=True,
    can_change_info=True,
    can_delete_messages=True,
    can_invite_users=True,
    can_restrict_members=True,
    can_pin_messages=True,
    can_manage_topics=False,
    can_promote_members=False,
    can_manage_video_chats=True,
    can_post_stories=True,
    can_edit_stories=True,
    can_delete_stories=True,
    is_anonymous=False,
    can_manage_voice_chats=False,
).model_dump()

CHAT_MEMBER_BANNED = ChatMemberBanned(
    user=USER,
    until_date=datetime.now(),
).model_dump()

CHAT_MEMBER_LEFT = ChatMemberLeft(
    user=USER,
).model_dump()

CHAT_MEMBER_MEMBER = ChatMemberMember(
    user=USER,
).model_dump()

CHAT_MEMBER_OWNER = ChatMemberOwner(
    user=USER,
    is_anonymous=True,
).model_dump()

CHAT_MEMBER_RESTRICTED = ChatMemberRestricted(
    user=USER,
    is_member=True,
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
    can_change_info=False,
    can_invite_users=False,
    can_pin_messages=False,
    can_manage_topics=False,
    until_date=datetime.now(),
).model_dump()


@pytest.mark.parametrize(
    ("data", "resolved_type"),
    [
        (CHAT_MEMBER_ADMINISTRATOR, ChatMemberAdministrator),
        (CHAT_MEMBER_BANNED, ChatMemberBanned),
        (CHAT_MEMBER_LEFT, ChatMemberLeft),
        (CHAT_MEMBER_MEMBER, ChatMemberMember),
        (CHAT_MEMBER_OWNER, ChatMemberOwner),
        (CHAT_MEMBER_RESTRICTED, ChatMemberRestricted),
    ],
)
def test_chat_member_resolution(data: dict, resolved_type: type[ChatMember]) -> None:
    chat_member = ChatMemberAdapter.validate_python(data)
    assert isinstance(chat_member, resolved_type)
