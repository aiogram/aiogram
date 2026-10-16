import pytest

from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.test import (
    Blueprint,
    BotTestEnvironment,
    UserActor,
    WorldLookupError,
    default_chat_permissions,
)
from aiogram.types import ChatPermissions

MEMBER = ChatMemberStatus.MEMBER
ADMIN = ChatMemberStatus.ADMINISTRATOR


class TestAddUser:
    async def test_the_actor_is_the_one_user_returns(self, env, blueprint):
        bob = env.add_user("Bob", last_name="B", username="bob", language_code="de")

        assert isinstance(bob, UserActor)
        assert bob.user is env.world.user(bob.user.id)
        assert env.user(bob.user.id).user is bob.user
        state = bob.user
        assert (state.first_name, state.last_name, state.username, state.language_code) == (
            "Bob",
            "B",
            "bob",
            "de",
        )
        assert not state.is_bot

    async def test_ids_continue_after_the_declared_ones(self, env, blueprint):
        first = env.add_user("A")
        second = env.add_user("B")

        declared = blueprint.users[0].id
        assert (first.user.id, second.user.id) == (declared + 1, declared + 2)

    async def test_a_free_id_is_found_past_a_taken_one(self, env, blueprint):
        taken = blueprint.users[0].id + 1
        env.add_user("Pinned", id=taken)

        assert env.add_user("Next").user.id == taken + 1

    async def test_an_id_that_is_taken_is_refused(self, env, blueprint):
        with pytest.raises(ValueError, match="User .* already exists"):
            env.add_user("Twin", id=blueprint.users[0].id)
        with pytest.raises(ValueError, match="already exists"):
            env.add_user("Bot", id=env.world.bot_user.id)

    async def test_the_new_user_talks_to_the_bot(self, env, dp):
        seen = []
        dp.message.register(seen.append)
        bob = env.add_user("Bob")

        await bob.send("hello")

        chat = env.chat(bob.user.id)
        assert chat.type == ChatType.PRIVATE
        assert [m.from_user.id for m in seen] == [bob.user.id]
        assert chat.first_name == "Bob"

    async def test_the_blueprint_is_left_alone(self, dp, blueprint):
        users, chats = len(blueprint.users), len(blueprint.chats)
        first = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        second = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            added = first.add_user("Bob")
            first.add_supergroup("Extra")

            assert (len(blueprint.users), len(blueprint.chats)) == (users, chats)
            assert added.user.id not in second.world.users
            assert len(second.world.chats) <= chats
        finally:
            first.dispose_sync()
            second.dispose_sync()


class TestAddChats:
    @pytest.mark.parametrize(
        ("kind", "kwargs"),
        [
            ("add_group", {}),
            ("add_supergroup", {}),
            ("add_supergroup", {"is_forum": True}),
            ("add_channel", {}),
        ],
    )
    async def test_it_is_shaped_as_a_declared_one(self, env, blueprint, kind, kwargs):
        added = getattr(env, kind)("Chat", bot_status=ADMIN, **kwargs)

        twin = Blueprint()
        getattr(twin, kind)("Chat", bot_status=ADMIN, id=added.id, **kwargs)
        assert added == twin.build().chat(added.id)

    async def test_members_are_named_by_spec_actor_or_id(self, env, blueprint):
        alice_spec = blueprint.users[0]
        bob = env.add_user("Bob")
        carol = env.add_user("Carol")

        chat = env.add_supergroup(
            "Team",
            members={alice_spec: ADMIN, bob: MEMBER, carol.user.id: ChatMemberStatus.CREATOR},
        )

        assert chat.member(alice_spec.id).status == ADMIN
        assert chat.member(bob.user.id).status == MEMBER
        assert chat.member(carol.user.id).status == ChatMemberStatus.CREATOR
        assert chat.member(env.world.bot_user.id).status == MEMBER

    async def test_the_bot_may_be_named_a_member(self, env, blueprint):
        bot = blueprint.bot

        chat = env.add_group("Group", members={bot: ADMIN})

        assert chat.member(bot.id).status == ADMIN

    async def test_the_bot_status_is_declared_as_in_a_blueprint(self, env):
        chat = env.add_channel("News", bot_status=ADMIN)

        assert chat.member(env.world.bot_user.id).status == ADMIN

    async def test_both_ways_of_stating_the_bot_status_are_refused(self, env, blueprint):
        with pytest.raises(ValueError, match="pass only one"):
            env.add_group("G", members={blueprint.bot: ADMIN}, bot_status=ADMIN)

    async def test_an_unknown_member_names_the_fix(self, env):
        with pytest.raises(WorldLookupError, match=r"User 999 .*env\.add_user"):
            env.add_group("G", members={999: MEMBER})

    async def test_ids_continue_the_declared_ones(self, env, blueprint):
        group = env.add_group("G")
        supergroup = env.add_supergroup("S")
        channel = env.add_channel("C")

        assert group.id < 0 > supergroup.id
        assert len({group.id, supergroup.id, channel.id, *blueprint_ids(blueprint)}) == (
            3 + len(blueprint_ids(blueprint))
        )
        assert supergroup.id < -(10**12) and channel.id < -(10**12)

    async def test_a_free_id_is_found_past_a_taken_one(self, env):
        next_id = -1001000000000 - len(env.world.chats) - 1
        env.add_supergroup("Pinned", id=next_id)

        assert env.add_supergroup("Next").id == next_id - 1

    async def test_an_explicit_id_is_kept_and_a_taken_one_refused(self, env):
        chat = env.add_supergroup("S", id=-100777)

        assert chat.id == -100777
        assert env.chat(-100777) is chat
        with pytest.raises(ValueError, match="Chat -100777 already exists"):
            env.add_group("again", id=-100777)

    async def test_permissions_and_forum_mode_are_declared(self, env):
        declared = ChatPermissions(can_send_messages=True, can_send_polls=False)

        chat = env.add_supergroup("S", permissions=declared, is_forum=True)

        assert chat.is_forum
        assert chat.permissions.can_send_polls is False
        assert env.add_group("G").permissions == default_chat_permissions()

    async def test_the_bot_works_in_it(self, env):
        chat = env.add_supergroup("S", bot_status=ADMIN)

        sent = await env.bot.send_message(chat_id=chat.id, text="hi")
        info = await env.bot.get_chat(chat_id=chat.id)

        assert chat.messages[-1].text == "hi"
        assert info.title == "S"
        assert sent.bot is env.bot

    async def test_an_actor_works_in_it(self, env, dp):
        seen = []
        dp.message.register(seen.append)
        bob = env.add_user("Bob")
        chat = env.add_supergroup("S", members={bob: MEMBER})

        await bob.in_(chat).send("hello")

        assert [m.chat.id for m in seen] == [chat.id]
        assert chat.messages[-1].from_user.id == bob.user.id

    async def test_the_owner_of_an_added_forum_creates_a_topic(self, env):
        owner = env.add_user("Owner")
        chat = env.add_supergroup(
            "S",
            members={owner: ChatMemberStatus.CREATOR},
            is_forum=True,
        )

        topic = await owner.in_(chat).create_topic("Bugs")

        assert chat.topic(topic.message_thread_id).name == "Bugs"

    async def test_rights_of_an_added_admin_are_the_ordinary_ones(self, env):
        admin = env.add_user("Admin")
        chat = env.add_supergroup("S", members={admin: ADMIN})

        member = await env.bot.get_chat_member(chat_id=chat.id, user_id=admin.user.id)

        assert member.can_delete_messages is True


class TestAddPrivateChat:
    async def test_the_chat_is_the_users(self, env):
        bob = env.add_user("Bob", username="bob")

        chat = env.add_private_chat(bob)

        assert chat is env.chat(bob.user.id)
        assert (chat.id, chat.type, chat.first_name, chat.username) == (
            bob.user.id,
            ChatType.PRIVATE,
            "Bob",
            "bob",
        )
        assert chat.member(bob.user.id).status == MEMBER

    async def test_it_matches_the_one_a_blueprint_declares(self, env):
        bob = env.add_user("Bob")

        twin = Blueprint()
        twin.add_private_chat(twin.add_user("Bob", id=bob.user.id))

        assert env.add_private_chat(bob.user.id) == twin.build().chat(bob.user.id)

    async def test_an_open_chat_is_refused(self, env):
        bob = env.add_user("Bob")
        env.chat(bob.user.id)

        with pytest.raises(ValueError, match="open already"):
            env.add_private_chat(bob)

    async def test_a_spec_names_the_user_too(self, env, blueprint):
        spec = blueprint.users[0]
        env.world.chats.pop(spec.id, None)

        assert env.add_private_chat(spec).id == spec.id

    async def test_an_unknown_user_is_refused(self, env):
        with pytest.raises(WorldLookupError, match="User 4242"):
            env.add_private_chat(4242)


def blueprint_ids(blueprint):
    return [chat.id for chat in blueprint.chats]
