"""Who opened a declared topic, and what that lets them do."""

import pytest

from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.test import Blueprint, BotTestEnvironment, WorldLookupError


@pytest.fixture
def build(dp):
    environments = []

    def make(creator):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        chat = blueprint.add_supergroup("Forum", members={alice: ChatMemberStatus.MEMBER})
        opener = {"bot": blueprint.bot, "alice": alice, "no one": None}[creator]
        topic = blueprint.add_topic(chat, "Game", creator=opener)
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        environments.append(environment)
        state = environment.chat(chat)
        return (
            environment,
            state,
            state.topic(topic.message_thread_id),
            environment.user(alice).in_(chat),
        )

    yield make
    for environment in environments:
        environment.dispose_sync()


class TestDeclaredCreator:
    def test_without_one_the_topic_is_no_ones_and_announced_as_the_bots(self, build):
        env, _chat, topic, _alice = build("no one")

        assert topic.creator_id is None
        assert topic.root_message.from_user.id == env.world.bot_user.id

    @pytest.mark.parametrize("creator", ["bot", "alice"])
    def test_the_creator_is_stored_and_announced(self, build, creator):
        env, _chat, topic, alice = build(creator)
        opener = env.world.bot_user if creator == "bot" else alice.user

        assert topic.creator_id == opener.id
        assert topic.root_message.from_user.id == opener.id
        assert topic.root_message.forum_topic_created.name == "Game"

    def test_an_actor_or_an_id_names_the_creator_too(self, dp):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        chat = blueprint.add_supergroup("Forum")

        assert blueprint.add_topic(chat, creator=alice.id).creator_id == alice.id
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            actor = env.user(alice)
            assert blueprint.add_topic(chat, creator=actor).creator_id == alice.id
        finally:
            env.dispose_sync()

    def test_an_undeclared_creator_fails_the_build(self):
        blueprint = Blueprint()
        chat = blueprint.add_supergroup("Forum")
        blueprint.add_topic(chat, creator=999)

        with pytest.raises(WorldLookupError, match="User 999 is not declared"):
            blueprint.build()


class TestTheBotsExemptions:
    async def test_the_bot_posts_into_its_closed_topic(self, build):
        env, chat, topic, _alice = build("bot")
        topic.is_closed = True

        sent = await env.bot.send_message(
            chat_id=chat.id, text="x", message_thread_id=topic.message_thread_id
        )

        assert sent.message_thread_id == topic.message_thread_id

    @pytest.mark.parametrize("creator", ["alice", "no one"])
    async def test_someone_elses_closed_topic_refuses_it(self, build, creator):
        env, chat, topic, _alice = build(creator)
        topic.is_closed = True

        with pytest.raises(TelegramBadRequest):
            await env.bot.send_message(
                chat_id=chat.id, text="x", message_thread_id=topic.message_thread_id
            )

    async def test_the_bot_closes_its_topic_without_the_right(self, build):
        env, chat, topic, _alice = build("bot")

        assert await env.bot.close_forum_topic(
            chat_id=chat.id, message_thread_id=topic.message_thread_id
        )
        assert topic.is_closed

    async def test_it_needs_the_right_for_a_users_topic(self, build):
        env, chat, topic, _alice = build("alice")

        with pytest.raises(TelegramBadRequest):
            await env.bot.close_forum_topic(
                chat_id=chat.id, message_thread_id=topic.message_thread_id
            )


class TestAUsersExemptions:
    async def test_the_creator_closes_reopens_and_deletes_it(self, build):
        _env, chat, topic, alice = build("alice")

        await alice.close_topic(topic)
        assert topic.is_closed
        await alice.reopen_topic(topic)
        await alice.delete_topic(topic)
        assert topic.message_thread_id not in chat.topics

    @pytest.mark.parametrize("creator", ["bot", "no one"])
    async def test_anyone_elses_takes_the_right(self, build, creator):
        _env, _chat, topic, alice = build(creator)

        with pytest.raises(WorldLookupError, match="can_manage_topics"):
            await alice.close_topic(topic)
