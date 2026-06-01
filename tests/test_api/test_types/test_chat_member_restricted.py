import datetime

import pytest

from aiogram.types import ChatMemberRestricted, User


class TestChatMemberRestricted:
    def _make_user(self) -> User:
        return User(id=42, is_bot=False, first_name="Test")

    def _base_kwargs(self, user: User) -> dict:
        return {
            "user": user,
            "is_member": True,
            "can_send_messages": True,
            "can_send_audios": True,
            "can_send_documents": True,
            "can_send_photos": True,
            "can_send_videos": True,
            "can_send_video_notes": True,
            "can_send_voice_notes": True,
            "can_send_polls": True,
            "can_send_other_messages": True,
            "can_add_web_page_previews": True,
            "can_change_info": True,
            "can_invite_users": True,
            "can_pin_messages": True,
            "can_manage_topics": True,
            "until_date": datetime.datetime(2099, 1, 1),
        }

    def test_full(self):
        """All fields including optional ones present."""
        user = self._make_user()
        member = ChatMemberRestricted(
            **self._base_kwargs(user),
            can_react_to_messages=True,
            can_edit_tag=False,
        )
        assert member.can_react_to_messages is True
        assert member.can_edit_tag is False

    def test_missing_can_react_to_messages(self):
        """Telegram sometimes omits can_react_to_messages — must not raise ValidationError."""
        user = self._make_user()
        member = ChatMemberRestricted(**self._base_kwargs(user))
        assert member.can_react_to_messages is None

    def test_missing_can_edit_tag(self):
        """Telegram sometimes omits can_edit_tag — must not raise ValidationError."""
        user = self._make_user()
        member = ChatMemberRestricted(**self._base_kwargs(user))
        assert member.can_edit_tag is None

    def test_missing_both_optional_fields(self):
        """Both new optional fields absent simultaneously — real-world scenario from issue #1812."""
        user = self._make_user()
        member = ChatMemberRestricted(**self._base_kwargs(user))
        assert member.can_react_to_messages is None
        assert member.can_edit_tag is None
        assert member.status == "restricted"
        assert member.is_member is True
