import pytest

from aiogram import Router
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.test import Blueprint, BotTestEnvironment, administrator_rights
from aiogram.types import InputMediaPhoto, Message, ReplyParameters


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


class TestTopicRoot:
    async def test_a_bot_message_in_a_topic_replies_to_its_root(self, make_env):
        env, chat, thread_id = make_env()

        sent = await env.bot.send_message(chat_id=chat.id, text="x", message_thread_id=thread_id)

        root = chat.topic(thread_id).root_message
        assert sent.is_topic_message is True
        assert sent.reply_to_message is root
        assert root.forum_topic_created.name == "Game"
        assert root.reply_to_message is None

    async def test_a_bot_message_in_general_replies_to_nothing(self, make_env):
        env, chat, _thread_id = make_env()

        sent = await env.bot.send_message(chat_id=chat.id, text="x")

        assert sent.reply_to_message is None
        assert chat.general_topic.root_message is None

    async def test_an_explicit_reply_wins_over_the_root(self, make_env):
        env, chat, thread_id = make_env()
        first = await env.bot.send_message(chat_id=chat.id, text="a", message_thread_id=thread_id)

        second = await env.bot.send_message(
            chat_id=chat.id,
            text="b",
            message_thread_id=thread_id,
            reply_parameters=ReplyParameters(message_id=first.message_id),
        )

        assert second.reply_to_message.message_id == first.message_id

    async def test_a_reply_in_another_chat_still_gets_the_root(self, make_env):
        env, chat, thread_id = make_env()
        private = env.chat(env.blueprint.chats[1])
        elsewhere = await env.bot.send_message(chat_id=private.id, text="elsewhere")

        sent = await env.bot.send_message(
            chat_id=chat.id,
            text="x",
            message_thread_id=thread_id,
            reply_parameters=ReplyParameters(chat_id=private.id, message_id=elsewhere.message_id),
        )

        assert sent.external_reply is not None
        assert sent.reply_to_message is chat.topic(thread_id).root_message

    @pytest.mark.parametrize("move", ["copy_message", "forward_message"])
    async def test_a_move_into_a_topic_replies_to_its_root(self, make_env, move):
        env, chat, thread_id = make_env()
        sent = await env.bot.send_message(chat_id=chat.id, text="s")

        await getattr(env.bot, move)(
            chat_id=chat.id,
            from_chat_id=chat.id,
            message_id=sent.message_id,
            message_thread_id=thread_id,
        )

        assert chat.messages[-1].reply_to_message is chat.topic(thread_id).root_message

    async def test_a_copy_with_its_own_reply_keeps_it(self, make_env):
        env, chat, thread_id = make_env()
        target = await env.bot.send_message(chat_id=chat.id, text="t", message_thread_id=thread_id)
        sent = await env.bot.send_message(chat_id=chat.id, text="s")

        await env.bot.copy_message(
            chat_id=chat.id,
            from_chat_id=chat.id,
            message_id=sent.message_id,
            message_thread_id=thread_id,
            reply_parameters=ReplyParameters(message_id=target.message_id),
        )

        assert chat.messages[-1].reply_to_message.message_id == target.message_id

    async def test_a_move_out_of_a_topic_replies_to_nothing(self, make_env):
        env, chat, thread_id = make_env()
        sent = await env.bot.send_message(chat_id=chat.id, text="s", message_thread_id=thread_id)

        await env.bot.forward_message(
            chat_id=chat.id, from_chat_id=chat.id, message_id=sent.message_id
        )

        assert chat.messages[-1].reply_to_message is None

    async def test_a_topic_service_message_replies_to_the_root(self, make_env):
        env, chat, thread_id = make_env(bot_status=ChatMemberStatus.ADMINISTRATOR)

        await env.bot.close_forum_topic(chat_id=chat.id, message_thread_id=thread_id)

        assert chat.messages[-1].forum_topic_closed is not None
        assert chat.messages[-1].reply_to_message is chat.topic(thread_id).root_message

    async def test_an_actor_message_in_a_topic_replies_to_its_root(self, make_env):
        env, chat, thread_id = make_env()
        alice = env.user(env.blueprint.users[0]).in_(chat, topic=thread_id)

        await alice.send("hello")

        assert chat.messages[-1].reply_to_message is chat.topic(thread_id).root_message

    async def test_an_actor_reply_in_a_topic_keeps_its_target(self, make_env):
        env, chat, thread_id = make_env()
        alice = env.user(env.blueprint.users[0]).in_(chat, topic=thread_id)
        await alice.send("first")
        first = chat.messages[-1]

        await alice.reply(first, "second")

        assert chat.messages[-1].reply_to_message is first

    async def test_an_actor_message_in_general_replies_to_nothing(self, make_env):
        env, chat, _thread_id = make_env()
        alice = env.user(env.blueprint.users[0]).in_(chat, topic=chat.general_topic)

        await alice.send("hello")

        assert chat.messages[-1].reply_to_message is None

    async def test_a_handler_reads_the_topic_name_from_the_root(self, make_env, dp):
        router = Router()

        @router.message()
        async def name_the_topic(message: Message) -> None:
            await message.answer(f"in {message.reply_to_message.forum_topic_created.name}")

        dp.include_router(router)
        env, chat, thread_id = make_env()

        await env.user(env.blueprint.users[0]).in_(chat, topic=thread_id).send("hi")

        assert chat.messages[-1].text == "in Game"
        assert chat.messages[-1].message_thread_id == thread_id
