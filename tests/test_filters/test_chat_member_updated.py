from datetime import datetime

import pytest

from aiogram.filters.chat_member_updated import (
    ADMINISTRATOR,
    IS_MEMBER,
    JOIN_TRANSITION,
    LEAVE_TRANSITION,
    ChatMemberUpdatedFilter,
    _MemberStatusGroupMarker,
    _MemberStatusMarker,
    _MemberStatusTransition,
)
from aiogram.types import (
    Chat,
    ChatMember,
    ChatMemberAdministrator,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberRestricted,
    ChatMemberUpdated,
    User,
)


class ChatMemberCustom(ChatMember):
    status: str
    is_member: bool | None = None


class TestMemberStatusMarker:
    def test_str(self):
        marker = _MemberStatusMarker("test")
        assert str(marker) == "TEST"
        assert str(+marker) == "+TEST"
        assert str(-marker) == "-TEST"

    def test_pos(self):
        marker = _MemberStatusMarker("test")
        assert marker.is_member is None

        positive_marker = +marker
        assert positive_marker is not marker
        assert marker.is_member is None
        assert positive_marker.is_member is True

    def test_neg(self):
        marker = _MemberStatusMarker("test")
        assert marker.is_member is None

        negative_marker = -marker
        assert negative_marker is not marker
        assert marker.is_member is None
        assert negative_marker.is_member is False

    def test_or(self):
        marker1 = _MemberStatusMarker("test1")
        marker2 = _MemberStatusMarker("test2")

        combination = marker1 | marker2
        assert isinstance(combination, _MemberStatusGroupMarker)
        assert marker1 in combination.statuses
        assert marker2 in combination.statuses

        combination2 = marker1 | marker1
        assert isinstance(combination2, _MemberStatusGroupMarker)
        assert len(combination2.statuses) == 1

        marker3 = _MemberStatusMarker("test3")
        combination3 = marker3 | combination
        assert isinstance(combination3, _MemberStatusGroupMarker)
        assert marker3 in combination3.statuses
        assert len(combination3.statuses) == 3
        assert combination3 is not combination

        with pytest.raises(TypeError):
            marker1 | 42

    def test_rshift(self):
        marker1 = _MemberStatusMarker("test1")
        marker2 = _MemberStatusMarker("test2")
        marker3 = _MemberStatusMarker("test3")
        transition = marker1 >> marker2
        assert isinstance(transition, _MemberStatusTransition)
        assert marker1 in transition.old.statuses
        assert marker2 in transition.new.statuses

        transition2 = marker1 >> (marker2 | marker3)
        assert isinstance(transition2, _MemberStatusTransition)

        with pytest.raises(TypeError):
            marker1 >> 42

    def test_lshift(self):
        marker1 = _MemberStatusMarker("test1")
        marker2 = _MemberStatusMarker("test2")
        marker3 = _MemberStatusMarker("test3")
        transition = marker1 << marker2
        assert isinstance(transition, _MemberStatusTransition)
        assert marker2 in transition.old.statuses
        assert marker1 in transition.new.statuses

        transition2 = marker1 << (marker2 | marker3)
        assert isinstance(transition2, _MemberStatusTransition)

        with pytest.raises(TypeError):
            marker1 << 42

    def test_hash(self):
        marker1 = _MemberStatusMarker("test1")
        marker1_1 = _MemberStatusMarker("test1")
        marker2 = _MemberStatusMarker("test2")
        assert hash(marker1) != hash(marker2)
        assert hash(marker1) == hash(marker1_1)
        assert hash(marker1) != hash(-marker1)

    @pytest.mark.parametrize(
        "name,is_member,member,result",
        [
            ["test", None, ChatMemberCustom(status="member"), False],
            ["test", None, ChatMemberCustom(status="test"), True],
            ["test", True, ChatMemberCustom(status="test"), False],
            ["test", True, ChatMemberCustom(status="test", is_member=True), True],
            ["test", True, ChatMemberCustom(status="test", is_member=False), False],
        ],
    )
    def test_check(self, name, is_member, member, result):
        marker = _MemberStatusMarker(name, is_member=is_member)
        assert marker.check(member=member) == result


class TestMemberStatusGroupMarker:
    def test_init_unique(self):
        marker1 = _MemberStatusMarker("test1")
        marker2 = _MemberStatusMarker("test2")
        marker3 = _MemberStatusMarker("test3")

        group = _MemberStatusGroupMarker(marker1, marker1, marker2, marker3)
        assert len(group.statuses) == 3

    def test_init_empty(self):
        with pytest.raises(ValueError):
            _MemberStatusGroupMarker()

    def test_or(self):
        marker1 = _MemberStatusMarker("test1")
        marker2 = _MemberStatusMarker("test2")
        marker3 = _MemberStatusMarker("test3")
        marker4 = _MemberStatusMarker("test4")

        group1 = _MemberStatusGroupMarker(marker1, marker2)
        group2 = _MemberStatusGroupMarker(marker3, marker4)

        group3 = group1 | marker3
        assert isinstance(group3, _MemberStatusGroupMarker)
        assert len(group3.statuses) == 3

        group4 = group1 | group2
        assert isinstance(group4, _MemberStatusGroupMarker)
        assert len(group4.statuses) == 4

        with pytest.raises(TypeError):
            group4 | 42

    def test_rshift(self):
        marker1 = _MemberStatusMarker("test1")
        marker2 = _MemberStatusMarker("test2")
        marker3 = _MemberStatusMarker("test3")

        group1 = _MemberStatusGroupMarker(marker1, marker2)
        group2 = _MemberStatusGroupMarker(marker1, marker3)

        transition1 = group1 >> marker1
        assert isinstance(transition1, _MemberStatusTransition)
        assert transition1.old is group1
        assert marker1 in transition1.new.statuses

        transition2 = group1 >> group2
        assert isinstance(transition2, _MemberStatusTransition)

        with pytest.raises(TypeError):
            group1 >> 42

    def test_lshift(self):
        marker1 = _MemberStatusMarker("test1")
        marker2 = _MemberStatusMarker("test2")
        marker3 = _MemberStatusMarker("test3")

        group1 = _MemberStatusGroupMarker(marker1, marker2)
        group2 = _MemberStatusGroupMarker(marker1, marker3)

        transition1 = group1 << marker1
        assert isinstance(transition1, _MemberStatusTransition)
        assert transition1.new is group1
        assert marker1 in transition1.old.statuses

        transition2 = group1 << group2
        assert isinstance(transition2, _MemberStatusTransition)

        with pytest.raises(TypeError):
            group1 << 42

    def test_str(self):
        marker1 = _MemberStatusMarker("test1")
        marker1_1 = +marker1
        marker2 = _MemberStatusMarker("test2")

        group1 = marker1 | marker1
        assert str(group1) == "TEST1"

        group2 = marker1 | marker2
        assert str(group2) == "(TEST1 | TEST2)"

        group3 = marker1 | marker1_1
        assert str(group3) == "(+TEST1 | TEST1)"

    @pytest.mark.parametrize(
        "status,result",
        [
            ["test", False],
            ["test1", True],
            ["test2", True],
        ],
    )
    def test_check(self, status, result):
        marker1 = _MemberStatusMarker("test1")
        marker2 = _MemberStatusMarker("test2")
        group = marker1 | marker2

        assert group.check(member=ChatMember(status=status)) is result


class TestMemberStatusTransition:
    def test_invert(self):
        marker1 = _MemberStatusMarker("test1")
        marker2 = _MemberStatusMarker("test2")

        transition1 = marker1 >> marker2
        transition2 = ~transition1

        assert transition1 is not transition2
        assert transition1.old == transition2.new
        assert transition1.new == transition2.old

        assert str(transition1) == "TEST1 >> TEST2"
        assert str(transition2) == "TEST2 >> TEST1"

    @pytest.mark.parametrize(
        "transition,old,new,result",
        [
            [
                JOIN_TRANSITION,
                ChatMemberCustom(status="left"),
                ChatMemberCustom(status="member"),
                True,
            ],
            [
                JOIN_TRANSITION,
                ChatMemberCustom(status="restricted", is_member=True),
                ChatMemberCustom(status="member"),
                False,
            ],
            [
                JOIN_TRANSITION,
                ChatMemberCustom(status="restricted", is_member=False),
                ChatMemberCustom(status="member"),
                True,
            ],
            [
                JOIN_TRANSITION,
                ChatMemberCustom(status="member"),
                ChatMemberCustom(status="restricted", is_member=False),
                False,
            ],
            [
                LEAVE_TRANSITION,
                ChatMemberCustom(status="member"),
                ChatMemberCustom(status="restricted", is_member=False),
                True,
            ],
        ],
    )
    def test_check(self, transition, old, new, result):
        assert transition.check(old=old, new=new) == result


class TestChatMemberUpdatedStatusFilter:
    USER = User(id=42, first_name="Test", is_bot=False)
    PARAMS = {
        "user": USER,
        "until_date": datetime.now(),
        "is_anonymous": True,
        "custom_title": "title",
        "can_be_edited": True,
        "can_manage_chat": True,
        "can_delete_messages": True,
        "can_manage_video_chats": True,
        "can_restrict_members": True,
        "can_promote_members": True,
        "can_change_info": True,
        "can_invite_users": True,
        "can_post_messages": True,
        "can_edit_messages": True,
        "can_pin_messages": True,
        "can_manage_topics": True,
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
        "can_post_stories": True,
        "can_edit_stories": True,
        "can_delete_stories": True,
    }

    @pytest.mark.parametrize(
        "transition,old,new,result",
        [
            [
                JOIN_TRANSITION,
                ChatMemberLeft(status="left", **PARAMS),
                ChatMemberMember(status="member", **PARAMS),
                True,
            ],
            [
                JOIN_TRANSITION,
                ChatMemberRestricted(status="restricted", is_member=True, **PARAMS),
                ChatMemberMember(status="member", **PARAMS),
                False,
            ],
            [
                JOIN_TRANSITION,
                ChatMemberRestricted(status="restricted", is_member=False, **PARAMS),
                ChatMemberMember(status="member", **PARAMS),
                True,
            ],
            [
                JOIN_TRANSITION,
                ChatMemberMember(status="member", **PARAMS),
                ChatMemberRestricted(status="restricted", is_member=False, **PARAMS),
                False,
            ],
            [
                LEAVE_TRANSITION,
                ChatMemberMember(status="member", **PARAMS),
                ChatMemberRestricted(status="restricted", is_member=False, **PARAMS),
                True,
            ],
            [
                ADMINISTRATOR,
                ChatMemberMember(status="member", **PARAMS),
                ChatMemberAdministrator(status="administrator", **PARAMS),
                True,
            ],
            [
                IS_MEMBER,
                ChatMemberRestricted(status="restricted", is_member=False, **PARAMS),
                ChatMemberMember(status="member", **PARAMS),
                True,
            ],
        ],
    )
    async def test_call(self, transition, old, new, result):
        updated_filter = ChatMemberUpdatedFilter(member_status_changed=transition)

        event = ChatMemberUpdated(
            chat=Chat(id=42, type="test"),
            from_user=self.USER,
            old_chat_member=old,
            new_chat_member=new,
            date=datetime.now(),
        )

        assert await updated_filter(event) is result

    def test_str(self):
        updated_filter = ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION)
        assert str(updated_filter).startswith("ChatMemberUpdatedFilter(member_status_changed=")
