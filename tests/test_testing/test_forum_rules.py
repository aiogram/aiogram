import pytest

from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.test import Blueprint, BotTestEnvironment, administrator_rights
from aiogram.types import InputMediaPhoto


def forum_world(bot_status=None, rights=None):
    blueprint = Blueprint()
    alice = blueprint.add_user("Alice")
    chat = blueprint.add_supergroup("Team", bot_status=bot_status)
    if rights is not None:
        blueprint.set_member(chat, blueprint.bot, rights=rights)
    blueprint.add_topic(chat, "Game")
    blueprint.add_private_chat(alice)
    return blueprint


@pytest.fixture
def make_env(dp):
    environments = []

    def make(**options):
        blueprint = forum_world(**options)
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        environments.append(environment)
        chat = environment.chat(blueprint.chats[0])
        return environment, chat, blueprint.topics[0].message_thread_id

    yield make
    for environment in environments:
        environment.dispose_sync()


async def _send_message(env, chat, thread_id):
    await env.bot.send_message(chat_id=chat.id, text="x", message_thread_id=thread_id)


async def _send_dice(env, chat, thread_id):
    await env.bot.send_dice(chat_id=chat.id, message_thread_id=thread_id)


async def _send_poll(env, chat, thread_id):
    await env.bot.send_poll(
        chat_id=chat.id,
        question="?",
        options=["a", "b"],
        message_thread_id=thread_id,
    )


async def _send_media_group(env, chat, thread_id):
    await env.bot.send_media_group(
        chat_id=chat.id,
        media=[InputMediaPhoto(media="a"), InputMediaPhoto(media="b")],
        message_thread_id=thread_id,
    )


async def _copy_message(env, chat, thread_id):
    sent = await env.bot.send_message(chat_id=chat.id, text="s")
    await env.bot.copy_message(
        chat_id=chat.id,
        from_chat_id=chat.id,
        message_id=sent.message_id,
        message_thread_id=thread_id,
    )


async def _forward_message(env, chat, thread_id):
    sent = await env.bot.send_message(chat_id=chat.id, text="s")
    await env.bot.forward_message(
        chat_id=chat.id,
        from_chat_id=chat.id,
        message_id=sent.message_id,
        message_thread_id=thread_id,
    )


async def _copy_messages(env, chat, thread_id):
    sent = await env.bot.send_message(chat_id=chat.id, text="s")
    await env.bot.copy_messages(
        chat_id=chat.id,
        from_chat_id=chat.id,
        message_ids=[sent.message_id],
        message_thread_id=thread_id,
    )


async def _forward_messages(env, chat, thread_id):
    sent = await env.bot.send_message(chat_id=chat.id, text="s")
    await env.bot.forward_messages(
        chat_id=chat.id,
        from_chat_id=chat.id,
        message_ids=[sent.message_id],
        message_thread_id=thread_id,
    )


SENDS = [
    _send_message,
    _send_dice,
    _send_poll,
    _send_media_group,
    _copy_message,
    _forward_message,
    _copy_messages,
    _forward_messages,
]


class TestClosedTopics:
    @pytest.mark.parametrize("send", SENDS, ids=lambda send: send.__name__.strip("_"))
    async def test_a_member_bot_cannot_post_into_a_closed_topic(self, make_env, send):
        env, chat, thread_id = make_env()
        chat.topic(thread_id).is_closed = True
        before = len(chat.topic(thread_id).messages)

        with pytest.raises(TelegramBadRequest, match="Bad Request: TOPIC_CLOSED$"):
            await send(env, chat, thread_id)

        assert len(chat.topic(thread_id).messages) == before

    @pytest.mark.parametrize("send", SENDS, ids=lambda send: send.__name__.strip("_"))
    async def test_an_admin_managing_topics_posts_into_a_closed_topic(self, make_env, send):
        env, chat, thread_id = make_env(bot_status=ChatMemberStatus.ADMINISTRATOR)
        chat.topic(thread_id).is_closed = True

        await send(env, chat, thread_id)

        assert chat.messages[-1].message_thread_id == thread_id

    async def test_an_admin_without_the_right_cannot(self, make_env):
        env, chat, thread_id = make_env(
            rights=administrator_rights(can_manage_topics=False),
        )
        chat.topic(thread_id).is_closed = True

        with pytest.raises(TelegramBadRequest, match="TOPIC_CLOSED"):
            await _send_message(env, chat, thread_id)

    async def test_the_owner_posts_into_a_closed_topic(self, make_env):
        env, chat, thread_id = make_env(bot_status=ChatMemberStatus.CREATOR)
        chat.topic(thread_id).is_closed = True

        await _send_message(env, chat, thread_id)

        assert chat.messages[-1].message_thread_id == thread_id

    async def test_a_reopened_topic_takes_messages_again(self, make_env):
        env, chat, thread_id = make_env()
        chat.topic(thread_id).is_closed = True
        chat.topic(thread_id).is_closed = False

        await _send_message(env, chat, thread_id)

        assert chat.messages[-1].message_thread_id == thread_id

    async def test_a_refused_send_uses_no_message_id(self, make_env):
        env, chat, thread_id = make_env()
        chat.topic(thread_id).is_closed = True
        before = chat.last_message_id

        with pytest.raises(TelegramBadRequest):
            await _send_message(env, chat, thread_id)

        assert chat.last_message_id == before

    async def test_a_bot_absent_from_the_chat_holds_no_right(self, make_env):
        env, chat, thread_id = make_env()
        del chat.members[env.world.bot_user.id]
        chat.topic(thread_id).is_closed = True

        with pytest.raises(TelegramBadRequest, match="TOPIC_CLOSED"):
            await _send_message(env, chat, thread_id)


class TestClosedGeneralTopic:
    @pytest.mark.parametrize("state", ["is_closed", "is_hidden"])
    async def test_a_member_bot_cannot_post_into_general(self, make_env, state):
        env, chat, _thread_id = make_env()
        setattr(chat.general_topic, state, True)

        with pytest.raises(TelegramBadRequest, match="TOPIC_CLOSED"):
            await env.bot.send_message(chat_id=chat.id, text="x")

    @pytest.mark.parametrize("state", ["is_closed", "is_hidden"])
    async def test_an_admin_posts_into_general(self, make_env, state):
        env, chat, _thread_id = make_env(bot_status=ChatMemberStatus.ADMINISTRATOR)
        setattr(chat.general_topic, state, True)

        await env.bot.send_message(chat_id=chat.id, text="x")

        assert chat.general_topic.messages[-1].text == "x"

    async def test_another_topic_is_open_while_general_is_closed(self, make_env):
        env, chat, thread_id = make_env()
        chat.general_topic.is_closed = True

        await _send_message(env, chat, thread_id)

        assert chat.messages[-1].message_thread_id == thread_id

    async def test_a_chat_that_is_not_a_forum_has_no_general_topic_to_close(self, env, team):
        team.general_topic.is_closed = True

        await env.bot.send_message(chat_id=team.id, text="x")

        assert team.messages[-1].text == "x"
