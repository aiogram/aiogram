import pytest

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.test.blueprint import (
    FALLBACK_BOT_ID,
    FIRST_USER_ID,
    Blueprint,
    default_blueprint,
)
from aiogram.test.world import administrator_rights
from aiogram.types import ChatPermissions


class TestDeclaration:
    def test_users_get_sequential_ids(self):
        blueprint = Blueprint()

        first = blueprint.add_user("Alice")
        second = blueprint.add_user("Bob")

        assert first.id == FIRST_USER_ID
        assert second.id == FIRST_USER_ID + 1

    def test_explicit_ids_are_kept(self):
        blueprint = Blueprint()

        user = blueprint.add_user("Alice", id=777)
        chat = blueprint.add_group("Team", id=-99)

        assert user.id == 777
        assert chat.id == -99

    def test_private_chat_mirrors_the_user(self):
        blueprint = Blueprint()
        user = blueprint.add_user("Alice", username="alice")

        chat = blueprint.add_private_chat(user)

        assert chat.id == user.id
        assert chat.type == ChatType.PRIVATE
        assert chat.first_name == "Alice"
        assert [member.user_id for member in chat.members] == [user.id]

    @pytest.mark.parametrize(
        ("factory", "chat_type"),
        [
            ("add_group", ChatType.GROUP),
            ("add_supergroup", ChatType.SUPERGROUP),
            ("add_channel", ChatType.CHANNEL),
        ],
    )
    def test_group_like_chats(self, factory, chat_type):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")

        chat = getattr(blueprint, factory)(
            "Team",
            members={alice: ChatMemberStatus.ADMINISTRATOR},
        )

        assert chat.type == chat_type
        assert chat.id < 0
        statuses = {member.user_id: member.status for member in chat.members}
        assert statuses[alice.id] == ChatMemberStatus.ADMINISTRATOR
        assert statuses[blueprint.bot.id] == ChatMemberStatus.MEMBER

    @pytest.mark.parametrize(
        "factory",
        ["add_group", "add_supergroup", "add_channel"],
    )
    def test_bot_status_defaults_to_member(self, factory):
        blueprint = Blueprint()

        chat = getattr(blueprint, factory)("Team")

        statuses = {member.user_id: member.status for member in chat.members}
        assert statuses[blueprint.bot.id] == ChatMemberStatus.MEMBER

    def test_bot_status_can_be_declared(self):
        blueprint = Blueprint()

        chat = blueprint.add_supergroup("Team", bot_status=ChatMemberStatus.ADMINISTRATOR)

        statuses = {member.user_id: member.status for member in chat.members}
        assert statuses[blueprint.bot.id] == ChatMemberStatus.ADMINISTRATOR
        bot_specs = [member for member in chat.members if member.user_id == blueprint.bot.id]
        assert len(bot_specs) == 1

    def test_bot_can_be_declared_via_members(self):
        blueprint = Blueprint()

        chat = blueprint.add_supergroup(
            "Team",
            members={blueprint.bot: ChatMemberStatus.ADMINISTRATOR},
        )

        bot_specs = [member for member in chat.members if member.user_id == blueprint.bot.id]
        assert len(bot_specs) == 1
        assert bot_specs[0].status == ChatMemberStatus.ADMINISTRATOR

    def test_bot_status_conflict_is_rejected(self):
        blueprint = Blueprint()

        with pytest.raises(ValueError, match="both"):
            blueprint.add_supergroup(
                "Team",
                members={blueprint.bot: ChatMemberStatus.ADMINISTRATOR},
                bot_status=ChatMemberStatus.CREATOR,
            )

    def test_bot_status_conflict_is_rejected_even_when_explicitly_member(self):
        # `bot_status=MEMBER` alongside a contradicting `members` entry used to pass
        # silently because MEMBER was indistinguishable from "not passed"; it must be
        # rejected just like any other explicit `bot_status`.
        blueprint = Blueprint()

        with pytest.raises(ValueError, match="both"):
            blueprint.add_supergroup(
                "Team",
                members={blueprint.bot: ChatMemberStatus.ADMINISTRATOR},
                bot_status=ChatMemberStatus.MEMBER,
            )

    def test_bot_status_member_alone_is_accepted(self):
        blueprint = Blueprint()

        chat = blueprint.add_supergroup("Team", bot_status=ChatMemberStatus.MEMBER)

        statuses = {member.user_id: member.status for member in chat.members}
        assert statuses[blueprint.bot.id] == ChatMemberStatus.MEMBER
        bot_specs = [member for member in chat.members if member.user_id == blueprint.bot.id]
        assert len(bot_specs) == 1

    def test_bot_id_is_taken_from_the_token(self):
        assert Blueprint(token="123456:ABC").bot.id == 123456

    def test_bot_id_falls_back_for_a_non_numeric_token(self):
        assert Blueprint(token="not-a-token").bot.id == FALLBACK_BOT_ID

    def test_defaults_are_stored(self):
        default = DefaultBotProperties(parse_mode="HTML")

        assert Blueprint(default=default).default is default

    def test_default_blueprint(self):
        blueprint = default_blueprint()

        assert len(blueprint.users) == 1
        assert len(blueprint.chats) == 1
        assert blueprint.chats[0].type == ChatType.PRIVATE


class TestBuild:
    def test_world_matches_the_declaration(self):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        group = blueprint.add_supergroup("Team", members={alice: ChatMemberStatus.CREATOR})

        world = blueprint.build()

        assert world.bot_user.id == blueprint.bot.id
        assert world.user(alice.id).first_name == "Alice"
        assert world.chat(group.id).member(alice.id).status == ChatMemberStatus.CREATOR

    def test_worlds_are_independent(self):
        blueprint = default_blueprint()
        chat_id = blueprint.chats[0].id

        first = blueprint.build()
        second = blueprint.build()
        first.chat(chat_id).members[999] = first.chat(chat_id).member(999)
        first.chat(chat_id).last_message_id = 17

        assert 999 not in second.chat(chat_id).members
        assert second.chat(chat_id).last_message_id == 0

    def test_blueprint_is_not_mutated_by_building(self):
        blueprint = default_blueprint()
        before = [(chat.id, len(chat.members)) for chat in blueprint.chats]

        world = blueprint.build()
        world.chats[blueprint.chats[0].id].members.clear()

        assert [(chat.id, len(chat.members)) for chat in blueprint.chats] == before

    def test_declared_rights_and_permissions_reach_the_world(self):
        blueprint = Blueprint()
        admin = blueprint.add_user("Admin")
        quiet = blueprint.add_user("Quiet")
        team = blueprint.add_supergroup("Team")
        blueprint.set_member(team, admin, rights=administrator_rights(can_change_info=False))
        blueprint.set_member(team, quiet, permissions=ChatPermissions(can_send_messages=True))

        world = blueprint.build()

        chat = world.chat(team.id)
        assert chat.member(admin.id).status == ChatMemberStatus.ADMINISTRATOR
        assert chat.member(admin.id).rights.can_change_info is False
        assert chat.member(quiet.id).status == ChatMemberStatus.RESTRICTED
        assert chat.member(quiet.id).permissions.can_send_messages is True

    def test_declared_rights_are_not_shared_between_worlds(self):
        blueprint = Blueprint()
        admin = blueprint.add_user("Admin")
        team = blueprint.add_supergroup("Team")
        declared = administrator_rights()
        blueprint.set_member(team, admin, rights=declared)

        first = blueprint.build()
        second = blueprint.build()

        assert first.chat(team.id).member(admin.id).rights == declared
        assert first.chat(team.id).member(admin.id).rights is not declared
        assert (
            first.chat(team.id).member(admin.id).rights
            is not second.chat(team.id).member(admin.id).rights
        )
