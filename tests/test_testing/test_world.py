import datetime

import pytest

from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.test.world import (
    BASE_DATE,
    CHAT_TYPE_SCOPED_RIGHTS,
    ChatState,
    MemberState,
    UserState,
    World,
    WorldLookupError,
    administrator_rights,
)
from aiogram.types import (
    ChatMemberAdministrator,
    ChatMemberBanned,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberRestricted,
    ChatPermissions,
    Message,
)


def make_message(chat: ChatState, text: str = "hi") -> Message:
    return Message(
        message_id=chat.allocate_message_id(),
        date=BASE_DATE,
        chat=chat.as_chat(),
        text=text,
    )


class TestUserState:
    def test_as_user(self):
        state = UserState(id=1, first_name="Alice", last_name="A", username="alice")

        user = state.as_user()

        assert user.id == 1
        assert user.full_name == "Alice A"
        assert user.username == "alice"
        assert not user.is_bot


class TestMemberState:
    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (ChatMemberStatus.CREATOR, ChatMemberOwner),
            (ChatMemberStatus.ADMINISTRATOR, ChatMemberAdministrator),
            (ChatMemberStatus.MEMBER, ChatMemberMember),
            (ChatMemberStatus.RESTRICTED, ChatMemberRestricted),
            (ChatMemberStatus.LEFT, ChatMemberLeft),
            (ChatMemberStatus.KICKED, ChatMemberBanned),
        ],
    )
    def test_as_chat_member(self, status, expected):
        user = UserState(id=7).as_user()

        member = MemberState(user_id=7, status=status).as_chat_member(user, ChatType.SUPERGROUP)

        assert isinstance(member, expected)
        assert member.user.id == 7

    def test_custom_title_is_kept(self):
        user = UserState(id=7).as_user()

        member = MemberState(
            user_id=7,
            status=ChatMemberStatus.ADMINISTRATOR,
            custom_title="Boss",
        ).as_chat_member(user, ChatType.SUPERGROUP)

        assert member.custom_title == "Boss"

    def test_until_date_is_used(self):
        user = UserState(id=7).as_user()
        until = BASE_DATE + datetime.timedelta(days=1)

        member = MemberState(
            user_id=7,
            status=ChatMemberStatus.KICKED,
            until_date=until,
        ).as_chat_member(user, ChatType.SUPERGROUP)

        assert member.until_date == until

    @pytest.mark.parametrize(
        ("status", "present"),
        [
            (ChatMemberStatus.MEMBER, True),
            (ChatMemberStatus.CREATOR, True),
            (ChatMemberStatus.LEFT, False),
            (ChatMemberStatus.KICKED, False),
        ],
    )
    def test_is_present(self, status, present):
        assert MemberState(user_id=1, status=status).is_present is present


class TestMemberRights:
    """What a membership allows is stored, not invented on conversion."""

    def as_admin(self, chat_type, rights=None):
        state = MemberState(user_id=7, status=ChatMemberStatus.ADMINISTRATOR, rights=rights)
        return state.as_chat_member(UserState(id=7).as_user(), chat_type)

    def test_declared_rights_are_reported_verbatim(self):
        member = self.as_admin(
            ChatType.SUPERGROUP,
            administrator_rights(can_delete_messages=False, can_restrict_members=False),
        )

        assert member.can_delete_messages is False
        assert member.can_restrict_members is False
        assert member.can_manage_chat is True

    def test_an_administrator_without_declared_rights_gets_the_ordinary_ones(self):
        member = self.as_admin(ChatType.SUPERGROUP)

        assert member.can_delete_messages is True
        assert member.can_promote_members is False

    @pytest.mark.parametrize(
        ("chat_type", "expected"),
        [
            (ChatType.SUPERGROUP, {"can_manage_topics", "can_pin_messages", "can_manage_tags"}),
            (ChatType.GROUP, {"can_pin_messages", "can_manage_tags"}),
            (
                ChatType.CHANNEL,
                {"can_post_messages", "can_edit_messages", "can_manage_direct_messages"},
            ),
            (ChatType.PRIVATE, set()),
        ],
    )
    def test_chat_type_decides_which_rights_exist_at_all(self, chat_type, expected):
        """A right the Bot API does not report for a chat type comes back unset here too."""
        member = self.as_admin(chat_type)

        scoped = {name for name in CHAT_TYPE_SCOPED_RIGHTS if getattr(member, name) is not None}
        assert scoped == expected

    def test_a_right_declared_where_it_cannot_exist_is_dropped(self):
        """Rights built for one chat type, read in another: each field follows the chat."""
        member = self.as_admin(
            ChatType.SUPERGROUP,
            administrator_rights(ChatType.CHANNEL, can_post_messages=True),
        )

        assert member.can_post_messages is None
        # Unstated where it does exist is "not granted", never `None`.
        assert member.can_manage_topics is False

    def test_an_owner_can_be_declared_anonymous(self):
        state = MemberState(
            user_id=7,
            status=ChatMemberStatus.CREATOR,
            rights=administrator_rights(is_anonymous=True),
        )

        member = state.as_chat_member(UserState(id=7).as_user(), ChatType.SUPERGROUP)

        assert member.is_anonymous is True

    def test_an_owner_without_rights_is_not_anonymous(self):
        state = MemberState(user_id=7, status=ChatMemberStatus.CREATOR)

        member = state.as_chat_member(UserState(id=7).as_user(), ChatType.SUPERGROUP)

        assert member.is_anonymous is False

    def test_declared_permissions_reach_a_restricted_member(self):
        state = MemberState(
            user_id=7,
            status=ChatMemberStatus.RESTRICTED,
            permissions=ChatPermissions(can_send_messages=True, can_send_polls=True),
        )

        member = state.as_chat_member(UserState(id=7).as_user(), ChatType.SUPERGROUP)

        assert member.can_send_messages is True
        assert member.can_send_polls is True
        assert member.can_send_photos is False

    def test_a_restriction_without_permissions_denies_everything(self):
        state = MemberState(user_id=7, status=ChatMemberStatus.RESTRICTED)

        member = state.as_chat_member(UserState(id=7).as_user(), ChatType.SUPERGROUP)

        assert member.can_send_messages is False
        assert member.can_manage_topics is False

    def test_ordinary_rights_are_built_for_supergroups_by_default(self):
        assert administrator_rights().can_manage_topics is True
        assert administrator_rights().can_post_messages is None


class TestChatState:
    def test_as_chat(self):
        chat = ChatState(id=-1, type=ChatType.GROUP, title="Team")

        assert chat.as_chat().title == "Team"
        assert chat.as_chat().type == ChatType.GROUP

    def test_message_ids_are_sequential_per_chat(self):
        first = ChatState(id=1)
        second = ChatState(id=2)

        assert [first.allocate_message_id(), first.allocate_message_id()] == [1, 2]
        assert second.allocate_message_id() == 1

    def test_add_and_find(self):
        chat = ChatState(id=1)
        message = chat.add_message(make_message(chat))

        assert chat.find_message(message.message_id) is message
        assert chat.find_message(404) is None
        assert chat.require_message(message.message_id) is message

    def test_require_missing_message(self):
        chat = ChatState(id=1)

        with pytest.raises(WorldLookupError, match="does not exist"):
            chat.require_message(1)

    def test_update_replaces_the_stored_message(self):
        chat = ChatState(id=1)
        message = chat.add_message(make_message(chat, "before"))

        edited = chat.update_message(message.message_id, text="after")

        assert edited.text == "after"
        assert len(chat.messages) == 1
        assert chat.find_message(message.message_id).text == "after"
        assert message.text == "before"

    def test_delete_removes_message_and_pin(self):
        chat = ChatState(id=1)
        message = chat.add_message(make_message(chat))
        chat.pinned_message_ids.append(message.message_id)

        chat.delete_message(message.message_id)

        assert chat.messages == []
        assert chat.pinned_message_ids == []
        assert message.message_id in chat.deleted_message_ids

    def test_member_is_created_as_left(self):
        chat = ChatState(id=1)

        member = chat.member(42)

        assert member.status == ChatMemberStatus.LEFT
        assert chat.member(42) is member


class TestWorld:
    def test_lookups(self):
        world = World(bot_user=UserState(id=42, is_bot=True))
        world.users[1] = UserState(id=1)
        world.chats[1] = ChatState(id=1)

        assert world.user(1).id == 1
        assert world.user(42) is world.bot_user
        assert world.chat(1).id == 1

    def test_unknown_user(self):
        world = World(bot_user=UserState(id=42, is_bot=True))

        with pytest.raises(WorldLookupError, match="not declared"):
            world.user(1)

    def test_unknown_chat(self):
        world = World(bot_user=UserState(id=42, is_bot=True))

        with pytest.raises(WorldLookupError, match="not declared"):
            world.chat(1)

    def test_counters(self):
        world = World(bot_user=UserState(id=42, is_bot=True))

        assert [world.next_update_id(), world.next_update_id()] == [1, 2]
        assert [world.next_query_id(), world.next_query_id()] == ["1", "2"]
        assert world.next_date() == BASE_DATE + datetime.timedelta(seconds=2)

    def test_ensure_private_chat_creates_one_shaped_like_a_declared_chat(self):
        world = World(bot_user=UserState(id=42, is_bot=True))
        world.users[1] = UserState(id=1, first_name="Alice", username="alice")

        chat = world.ensure_private_chat(world.user(1))

        assert chat.id == 1
        assert chat.type == ChatType.PRIVATE
        assert chat.username == "alice"
        assert chat.first_name == "Alice"
        assert chat.members[1].status == ChatMemberStatus.MEMBER

    def test_ensure_private_chat_returns_the_declared_one_when_there_is_one(self):
        world = World(bot_user=UserState(id=42, is_bot=True))
        world.users[1] = UserState(id=1)
        declared = ChatState(id=1, type=ChatType.PRIVATE, title="Declared")
        world.chats[1] = declared

        assert world.ensure_private_chat(world.user(1)) is declared
