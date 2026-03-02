from datetime import datetime

from aiogram.types import (
    ChatAdministratorRights,
    ChatMemberAdministrator,
    ChatMemberMember,
    ChatMemberRestricted,
    ChatPermissions,
    User,
)


class TestChatMemberTagPermissions:
    def test_chat_administrator_rights_can_manage_tags(self):
        rights = ChatAdministratorRights(
            is_anonymous=False,
            can_manage_chat=True,
            can_delete_messages=True,
            can_manage_video_chats=True,
            can_restrict_members=True,
            can_promote_members=True,
            can_change_info=True,
            can_invite_users=True,
            can_post_stories=True,
            can_edit_stories=True,
            can_delete_stories=True,
            can_manage_tags=True,
        )
        assert rights.can_manage_tags is True

    def test_chat_member_administrator_can_manage_tags(self):
        admin = ChatMemberAdministrator(
            user=User(id=42, is_bot=False, first_name="User"),
            can_be_edited=True,
            is_anonymous=False,
            can_manage_chat=True,
            can_delete_messages=True,
            can_manage_video_chats=True,
            can_restrict_members=True,
            can_promote_members=True,
            can_change_info=True,
            can_invite_users=True,
            can_post_stories=True,
            can_edit_stories=True,
            can_delete_stories=True,
            can_manage_tags=True,
        )
        assert admin.can_manage_tags is True

    def test_chat_permissions_can_edit_tag(self):
        permissions = ChatPermissions(can_edit_tag=True)
        assert permissions.can_edit_tag is True

    def test_chat_member_member_tag(self):
        member = ChatMemberMember(
            user=User(id=42, is_bot=False, first_name="User"),
            tag="premium",
        )
        assert member.tag == "premium"

    def test_chat_member_restricted_can_edit_tag_and_tag(self):
        restricted = ChatMemberRestricted(
            user=User(id=42, is_bot=False, first_name="User"),
            is_member=True,
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_edit_tag=True,
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_manage_topics=True,
            until_date=datetime.now(),
            tag="premium",
        )
        assert restricted.can_edit_tag is True
        assert restricted.tag == "premium"
