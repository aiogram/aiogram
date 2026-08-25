import pytest

from aiogram.test import Blueprint, BotTestEnvironment
from aiogram.test.world import WorldLookupError


@pytest.fixture
def community_blueprint():
    blueprint = Blueprint()
    alice = blueprint.add_user("Alice")
    blueprint.add_private_chat(alice)
    chat = blueprint.add_supergroup("Team")
    blueprint.add_community("Guild", chats=[chat])
    blueprint.add_supergroup("Unattached")
    return blueprint


@pytest.fixture
def community_env(community_blueprint, dp):
    environment = BotTestEnvironment(blueprint=community_blueprint, dispatcher=dp)
    try:
        yield environment
    finally:
        environment.dispose_sync()


@pytest.fixture
def guild(community_blueprint):
    return community_blueprint.communities[0]


class TestDeclaration:
    def test_community_is_materialized(self, community_env, guild, community_blueprint):
        state = community_env.community(guild)

        assert state.name == "Guild"
        assert state.chat_ids == [community_blueprint.chats[1].id]

    def test_attached_chat_knows_its_community(self, community_env, guild, community_blueprint):
        chat = community_env.chat(community_blueprint.chats[1])

        assert chat.community_id == guild.id

    def test_unknown_community(self, community_env):
        with pytest.raises(WorldLookupError, match="not declared"):
            community_env.community(999)

    def test_state_and_id_are_accepted(self, community_env, guild):
        state = community_env.community(guild)

        assert community_env.community(state) is state
        assert community_env.community(guild.id) is state

    def test_communities_do_not_leak_between_environments(self, community_blueprint, dp):
        first = BotTestEnvironment(blueprint=community_blueprint, dispatcher=dp)
        community_id = community_blueprint.communities[0].id
        first.community(community_id).chat_ids.clear()
        first.dispose_sync()

        second = BotTestEnvironment(blueprint=community_blueprint, dispatcher=dp)
        try:
            assert second.community(community_id).chat_ids
        finally:
            second.dispose_sync()


class TestChatInfo:
    async def test_get_chat_exposes_the_community(self, community_env, community_blueprint, guild):
        full = await community_env.bot.get_chat(chat_id=community_blueprint.chats[1].id)

        assert full.community.id == guild.id
        assert full.community.name == "Guild"

    async def test_unattached_chat_has_no_community(self, community_env, community_blueprint):
        full = await community_env.bot.get_chat(chat_id=community_blueprint.chats[2].id)

        assert full.community is None


class TestServiceMessages:
    async def test_chat_added_to_community(self, community_env, dp, community_blueprint, guild):
        @dp.message()
        async def handler(message):
            return message.community_chat_added.community.name

        target = community_blueprint.chats[2]
        actor = community_env.user(community_blueprint.users[0]).in_(target)

        assert await actor.add_chat_to_community(guild) == "Guild"

        chat = community_env.chat(target)
        assert chat.community_id == guild.id
        assert target.id in community_env.community(guild).chat_ids
        assert chat.messages[-1].community_chat_added is not None

    async def test_chat_removed_from_community(
        self, community_env, dp, community_blueprint, guild
    ):
        @dp.message()
        async def handler(message):
            return "removed" if message.community_chat_removed is not None else None

        attached = community_blueprint.chats[1]
        actor = community_env.user(community_blueprint.users[0]).in_(attached)

        assert await actor.remove_chat_from_community(guild) == "removed"

        chat = community_env.chat(attached)
        assert chat.community_id is None
        assert attached.id not in community_env.community(guild).chat_ids

    async def test_adding_an_already_attached_chat_is_idempotent(
        self,
        community_env,
        dp,
        community_blueprint,
        guild,
    ):
        @dp.message()
        async def handler(message):
            return None

        attached = community_blueprint.chats[1]
        actor = community_env.user(community_blueprint.users[0]).in_(attached)

        await actor.add_chat_to_community(guild)

        assert community_env.community(guild).chat_ids.count(attached.id) == 1

    async def test_removing_an_unattached_chat_is_tolerated(
        self,
        community_env,
        dp,
        community_blueprint,
        guild,
    ):
        @dp.message()
        async def handler(message):
            return "seen"

        target = community_blueprint.chats[2]
        actor = community_env.user(community_blueprint.users[0]).in_(target)

        assert await actor.remove_chat_from_community(guild) == "seen"
