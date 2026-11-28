"""
Regression tests for the key the environment resolves.

Before this change ``env.state()`` dropped the thread id and the business connection, so
under a topic-aware strategy it returned a context for a *different* key than the one the
dispatcher had just written to — an empty context instead of the stored data.
"""

import pytest

from aiogram import Dispatcher
from aiogram.fsm.strategy import FSMStrategy
from aiogram.test import Blueprint, BotTestEnvironment


@pytest.fixture
def forum_blueprint():
    blueprint = Blueprint()
    alice = blueprint.add_user("Alice")
    chat = blueprint.add_supergroup("Team")
    blueprint.add_topic(chat, "Support")
    blueprint.add_private_chat(alice)
    blueprint.add_business_connection(alice)
    return blueprint


def environment(blueprint, strategy):
    dispatcher = Dispatcher(fsm_strategy=strategy)

    @dispatcher.message()
    async def handler(message, state):
        await state.update_data(seen=message.text)
        return state.key

    @dispatcher.business_message()
    async def business_handler(message, state):
        await state.update_data(seen=message.text)
        return state.key

    return BotTestEnvironment(blueprint=blueprint, dispatcher=dispatcher)


@pytest.mark.parametrize(
    "strategy",
    [FSMStrategy.USER_IN_TOPIC, FSMStrategy.CHAT_TOPIC],
)
async def test_topic_strategies_resolve_the_dispatcher_key(forum_blueprint, strategy):
    env = environment(forum_blueprint, strategy)
    chat, topic = forum_blueprint.chats[0], forum_blueprint.topics[0]
    actor = env.user(forum_blueprint.users[0]).in_(chat, topic=topic)
    try:
        handler_key = await actor.send("hello")

        context = env.state(forum_blueprint.users[0], chat, topic=topic)

        assert context.key.thread_id == handler_key.thread_id == topic.message_thread_id
        assert await context.get_data() == {"seen": "hello"}
    finally:
        await env.dispose()


async def test_actor_state_uses_its_own_binding(forum_blueprint):
    env = environment(forum_blueprint, FSMStrategy.USER_IN_TOPIC)
    actor = env.user(forum_blueprint.users[0]).in_(
        forum_blueprint.chats[0],
        topic=forum_blueprint.topics[0],
    )
    try:
        await actor.send("hello")

        assert await actor.state().get_data() == {"seen": "hello"}
    finally:
        await env.dispose()


async def test_business_connection_is_part_of_the_key(forum_blueprint):
    env = environment(forum_blueprint, FSMStrategy.USER_IN_CHAT)
    connection = forum_blueprint.business_connections[0]
    actor = env.user(forum_blueprint.users[0]).in_(
        forum_blueprint.chats[1],
        business=connection,
    )
    try:
        handler_key = await actor.send("hello")

        context = env.state(
            forum_blueprint.users[0],
            forum_blueprint.chats[1],
            business_connection=connection,
        )

        assert context.key.business_connection_id == handler_key.business_connection_id
        assert await context.get_data() == {"seen": "hello"}
    finally:
        await env.dispose()


async def test_topic_can_be_given_as_a_thread_id(forum_blueprint):
    env = environment(forum_blueprint, FSMStrategy.USER_IN_TOPIC)
    chat, topic = forum_blueprint.chats[0], forum_blueprint.topics[0]
    try:
        context = env.state(
            forum_blueprint.users[0],
            chat,
            topic=topic.message_thread_id,
        )

        assert context.key.thread_id == topic.message_thread_id
    finally:
        await env.dispose()


async def test_chat_state_is_accepted_as_the_chat(forum_blueprint):
    env = environment(forum_blueprint, FSMStrategy.USER_IN_CHAT)
    try:
        chat = env.chat(forum_blueprint.chats[0])

        assert env.state(forum_blueprint.users[0], chat).key.chat_id == chat.id
    finally:
        await env.dispose()
