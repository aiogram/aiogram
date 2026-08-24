import pytest

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.test.blueprint import (
    FALLBACK_BOT_ID,
    FIRST_USER_ID,
    Blueprint,
    default_blueprint,
)


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
