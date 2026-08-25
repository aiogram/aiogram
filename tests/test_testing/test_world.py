import datetime

import pytest

from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.test import ApiRejection, Blueprint
from aiogram.test.world import (
    BASE_DATE,
    CHAT_TYPE_SCOPED_RIGHTS,
    ChatState,
    MemberState,
    UserState,
    World,
    WorldLookupError,
    administrator_rights,
    derive_message,
    mask,
    private_chat_shape,
    resolve_topic,
)
from aiogram.types import (
    ChatAdministratorRights,
    ChatMemberAdministrator,
    ChatMemberBanned,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberRestricted,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    MessageEntity,
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
        """One declaration, read in two chat types: each field follows the chat."""
        rights = administrator_rights(can_post_messages=True, can_manage_topics=False)

        assert self.as_admin(ChatType.SUPERGROUP, rights).can_post_messages is None
        assert self.as_admin(ChatType.CHANNEL, rights).can_post_messages is True
        # Unstated where it does exist is "not granted", never `None`.
        assert self.as_admin(ChatType.SUPERGROUP, rights).can_manage_topics is False

    def test_declaring_a_right_never_grants_fewer_rights_than_saying_nothing(self):
        """
        The factory is unscoped, so `scoped_rights` is the only thing that drops a field.

        Scoping at construction made `administrator_rights(can_post_messages=True)` read
        back as `False` in a channel — an explicit grant producing *less* than silence.
        """
        explicit = self.as_admin(
            ChatType.CHANNEL,
            administrator_rights(can_post_messages=True),
        )
        implicit = self.as_admin(ChatType.CHANNEL)

        assert explicit.can_post_messages is True
        assert implicit.can_post_messages is True

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

    def test_the_ordinary_rights_are_a_full_unscoped_mask(self):
        """Every right the Bot API knows carries a boolean; the chat type decides later."""
        rights = administrator_rights()

        assert rights.can_manage_topics is True
        assert rights.can_post_messages is True
        assert rights.can_promote_members is False
        assert None not in {getattr(rights, name) for name in type(rights).model_fields}


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

        with pytest.raises(ApiRejection, match="does not exist"):
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


class TestChatRegistration:
    """
    A chat learns which bot its messages belong to from the world that holds it.

    The owner used to be copied onto every chat — in bulk when the world was bound, and
    again defensively on every lookup — while three readers went straight to the mapping
    and saw whatever the last sweep had left. Registration is now the single wiring point,
    so a chat put into `world.chats` by any route is a working one.
    """

    def test_a_registered_chat_follows_the_worlds_owner(self, env):
        world = World(bot_user=UserState(id=42, is_bot=True))
        chat = ChatState(id=1)
        world.chats[1] = chat

        assert chat.bound_bot is None
        world.bind(env.bot)

        assert chat.bound_bot is env.bot

    def test_a_chat_registered_after_binding_is_wired_too(self, env):
        world = World(bot_user=UserState(id=42, is_bot=True))
        world.bind(env.bot)

        world.chats[1] = ChatState(id=1)

        assert world.chats[1].bound_bot is env.bot

    @pytest.mark.parametrize(
        "add",
        [
            pytest.param(lambda chats, chat: chats.update({1: chat}), id="update"),
            pytest.param(lambda chats, chat: chats.update([(1, chat)]), id="update-pairs"),
            pytest.param(lambda chats, chat: chats.setdefault(1, chat), id="setdefault"),
            pytest.param(lambda chats, chat: chats.__ior__({1: chat}), id="ior"),
        ],
    )
    def test_every_way_of_adding_a_chat_wires_it(self, env, add):
        """
        `dict` implements these in C, without going through `__setitem__`.

        So overriding that alone left three doors into the world that skipped the wiring
        and produced a chat whose messages were silently never bound.
        """
        world = World(bot_user=UserState(id=42, is_bot=True))
        world.bind(env.bot)
        chat = ChatState(id=1)

        add(world.chats, chat)

        assert world.chats[1] is chat
        assert chat.bound_bot is env.bot
        assert chat.add_message(make_message(chat)).bot is env.bot

    def test_setdefault_returns_the_chat_already_there(self, env):
        world = World(bot_user=UserState(id=42, is_bot=True))
        world.chats[1] = ChatState(id=1)

        assert world.chats.setdefault(1, ChatState(id=1)) is world.chats[1]

    def test_setdefault_without_a_chat_says_so(self):
        world = World(bot_user=UserState(id=42, is_bot=True))

        with pytest.raises(WorldLookupError, match="no chat was given"):
            world.chats.setdefault(1)

    def test_a_chat_read_straight_out_of_the_mapping_is_wired(self, env):
        """The readers that bypass `World.chat()` must not see a half-wired chat."""
        world = World(bot_user=UserState(id=42, is_bot=True))
        world.bind(env.bot)
        world.chats[1] = ChatState(id=1)

        stored = world.chats.get(1).add_message(make_message(world.chats[1]))

        assert stored.bot is env.bot
        assert stored.chat.bot is env.bot

    def test_chats_passed_to_the_constructor_are_registered(self, env):
        world = World(bot_user=UserState(id=42, is_bot=True), chats={1: ChatState(id=1)})
        world.bind(env.bot)

        assert world.chats[1].bound_bot is env.bot

    def test_a_chat_outside_any_world_stores_unbound_messages(self):
        """A world-less chat still works; it just has no owner to bind to."""
        chat = ChatState(id=1)

        assert chat.bound_bot is None
        assert chat.add_message(make_message(chat)).bot is None


class TestDerivedMessages:
    def test_a_derived_message_belongs_to_the_destination(self, env):
        world = World(bot_user=UserState(id=42, is_bot=True))
        world.bind(env.bot)
        world.chats[1] = ChatState(id=1)
        chat = world.chats[1]
        original = chat.add_message(make_message(chat))

        derived = derive_message(original, {"text": "edited"}, env.bot)

        assert original.bot is env.bot
        assert derived is not original
        assert derived.bot is env.bot
        assert derived.text == "edited"

    def test_what_the_change_did_not_touch_is_shared_with_the_original(self, env):
        world = World(bot_user=UserState(id=42, is_bot=True))
        world.bind(env.bot)
        world.chats[1] = ChatState(id=1)
        chat = world.chats[1]
        original = chat.add_message(make_message(chat))

        derived = derive_message(original, {"text": "edited"}, env.bot)

        assert derived.chat is original.chat

    def test_deriving_does_not_unbind_the_originals_children(self, env):
        """
        Regression: the derived copy used to be detached whole.

        `model_copy` shares every untouched child with the original, so unbinding the copy
        walked straight into the world's own message and unbound *its* keyboard. Inside a
        bound chat the mount that follows papered over it; deriving into a chat with no
        owner — a world built and inspected on its own — left the original corrupted.
        """
        world = World(bot_user=UserState(id=42, is_bot=True))
        world.bind(env.bot)
        world.chats[1] = ChatState(id=1)
        chat = world.chats[1]
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
        )
        original = chat.add_message(
            Message(
                message_id=chat.allocate_message_id(),
                date=BASE_DATE,
                chat=chat.as_chat(),
                text="hi",
                reply_markup=keyboard,
            ),
        )
        orphan = ChatState(id=2)

        orphan.add_derived(original, message_id=99)

        assert original.reply_markup.bot is env.bot
        assert original.reply_markup.inline_keyboard[0][0].bot is env.bot

    def test_the_changes_are_copied_in(self, env):
        """What an edit carries belongs to the caller until the world copies it."""
        world = World(bot_user=UserState(id=42, is_bot=True))
        world.bind(env.bot)
        world.chats[1] = ChatState(id=1)
        chat = world.chats[1]
        original = chat.add_message(make_message(chat))
        entity = MessageEntity(type="bold", offset=0, length=2)

        edited = chat.update_message(original.message_id, entities=[entity])

        assert edited.entities[0] is not entity
        assert entity.bot is None
        assert edited.entities[0].bot is env.bot


class TestMask:
    def test_it_reads_every_field_by_name(self):
        rights = administrator_rights(can_delete_messages=False)

        values = mask(ChatAdministratorRights, rights)

        assert values.keys() == ChatAdministratorRights.model_fields.keys()
        assert values["can_delete_messages"] is False

    def test_coercing_turns_an_unstated_flag_into_a_denied_one(self):
        """A source that simply omits what it does not grant — a request, most of all."""
        values = mask(ChatPermissions, ChatPermissions(can_send_messages=True), coerce=True)

        assert values["can_send_messages"] is True
        assert values["can_send_polls"] is False
        assert None not in set(values.values())

    def test_without_coercion_an_unstated_flag_stays_unstated(self):
        values = mask(ChatPermissions, ChatPermissions(can_send_messages=True))

        assert values["can_send_polls"] is None


class TestPrivateChatShape:
    def test_a_declared_and_an_opened_private_chat_agree(self):
        """
        The two descriptions of a private chat are one description.

        A user whose chat the blueprint happened to declare must not live in a
        differently-shaped chat than one whose chat a deep link opened.
        """
        blueprint = Blueprint()
        declared_user = blueprint.add_user("Alice", username="alice", last_name="A")
        blueprint.add_private_chat(declared_user)
        opened_user = blueprint.add_user("Alice", username="alice", last_name="A")
        world = blueprint.build()

        opened = world.ensure_private_chat(world.user(opened_user.id))
        declared = world.chat(declared_user.id)

        assert private_chat_shape(declared_user) == {
            **private_chat_shape(opened_user),
            "id": declared_user.id,
        }
        assert opened.type == declared.type
        assert opened.username == declared.username
        assert opened.last_name == declared.last_name
        # Each is a chat with exactly its own user in it.
        assert list(opened.members) == [opened_user.id]
        assert list(declared.members) == [declared_user.id]
        assert opened.members[opened_user.id].status == declared.members[declared_user.id].status


class TestResolveTopic:
    @pytest.fixture
    def forum(self):
        blueprint = Blueprint()
        chat = blueprint.add_supergroup("Forum")
        topic = blueprint.add_topic(chat, "Support")
        world = blueprint.build()
        return world.chat(chat.id), topic

    def test_a_declaration_a_state_and_a_thread_id_all_resolve(self, forum):
        chat, spec = forum
        state = chat.topic(spec.message_thread_id)

        assert resolve_topic(chat, spec) is state
        assert resolve_topic(chat, state) is state
        assert resolve_topic(chat, spec.message_thread_id) is state

    def test_an_unknown_thread_id_fails(self, forum):
        chat, _spec = forum

        with pytest.raises(ApiRejection, match="Topic 999 does not exist"):
            resolve_topic(chat, 999)
