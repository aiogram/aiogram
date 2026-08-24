import datetime

import pytest

from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.test.world import (
    BASE_DATE,
    ChatState,
    MemberState,
    UserState,
    World,
    WorldLookupError,
)
from aiogram.types import (
    ChatMemberAdministrator,
    ChatMemberBanned,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberRestricted,
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

        member = MemberState(user_id=7, status=status).as_chat_member(user)

        assert isinstance(member, expected)
        assert member.user.id == 7

    def test_custom_title_is_kept(self):
        user = UserState(id=7).as_user()

        member = MemberState(
            user_id=7,
            status=ChatMemberStatus.ADMINISTRATOR,
            custom_title="Boss",
        ).as_chat_member(user)

        assert member.custom_title == "Boss"

    def test_until_date_is_used(self):
        user = UserState(id=7).as_user()
        until = BASE_DATE + datetime.timedelta(days=1)

        member = MemberState(
            user_id=7,
            status=ChatMemberStatus.KICKED,
            until_date=until,
        ).as_chat_member(user)

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
