import pytest

from aiogram import Router
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.test import Blueprint, BotTestEnvironment, WorldLookupError, administrator_rights
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

        # `first` replies to the root, and a nested reply carries no
        # reply of its own, so it is a copy without one.
        replied = chat.messages[-1].reply_to_message
        assert replied.message_id == first.message_id
        assert replied.reply_to_message is None
        assert first.reply_to_message is chat.topic(thread_id).root_message

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


@pytest.fixture
def owned_forum(dp):
    blueprint = Blueprint()
    owner = blueprint.add_user("Owner")
    alice = blueprint.add_user("Alice")
    chat = blueprint.add_supergroup(
        "Team",
        members={owner: ChatMemberStatus.CREATOR, alice: ChatMemberStatus.MEMBER},
    )
    topic = blueprint.add_topic(chat, "Game")
    environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
    try:
        yield (
            environment,
            environment.chat(chat),
            topic.message_thread_id,
            environment.user(owner).in_(chat),
            environment.user(alice),
        )
    finally:
        environment.dispose_sync()


class TestForumToggle:
    async def test_the_owner_turns_topics_off(self, owned_forum):
        env, chat, thread_id, owner, _alice = owned_forum

        assert await owner.set_topics(False) is None

        assert chat.is_forum is False
        assert chat.as_chat().is_forum is None
        assert thread_id in chat.topics

    async def test_no_update_is_delivered(self, owned_forum, dp):
        env, chat, _thread_id, owner, _alice = owned_forum
        seen = []
        dp.message.register(seen.append)
        before = len(chat.messages)

        await owner.set_topics(False)

        assert seen == []
        assert len(chat.messages) == before

    async def test_a_stale_thread_id_lands_in_the_chat_untagged(self, owned_forum):
        env, chat, thread_id, owner, _alice = owned_forum
        await owner.set_topics(False)

        sent = await env.bot.send_message(chat_id=chat.id, text="x", message_thread_id=thread_id)

        assert sent.message_thread_id is None
        assert sent.is_topic_message is None
        assert sent.reply_to_message is None
        assert sent.chat.is_forum is None

    async def test_a_closed_topic_does_not_refuse_once_topics_are_off(self, owned_forum):
        env, chat, thread_id, owner, _alice = owned_forum
        chat.topic(thread_id).is_closed = True
        await owner.set_topics(False)

        sent = await env.bot.send_message(chat_id=chat.id, text="x", message_thread_id=thread_id)

        assert sent.message_thread_id is None

    async def test_a_move_with_a_stale_thread_id_lands_untagged(self, owned_forum):
        env, chat, thread_id, owner, _alice = owned_forum
        await owner.set_topics(False)
        sent = await env.bot.send_message(chat_id=chat.id, text="s")

        await env.bot.copy_message(
            chat_id=chat.id,
            from_chat_id=chat.id,
            message_id=sent.message_id,
            message_thread_id=thread_id,
        )

        assert chat.messages[-1].message_thread_id is None

    async def test_an_actor_bound_to_a_topic_posts_untagged(self, owned_forum):
        env, chat, thread_id, owner, alice = owned_forum
        member = alice.in_(chat, topic=thread_id)
        await owner.set_topics(False)

        await member.send("hello")

        assert chat.messages[-1].message_thread_id is None
        assert chat.messages[-1].reply_to_message is None

    @pytest.mark.parametrize(
        ("name", "kwargs"),
        [
            ("create_forum_topic", {"name": "New"}),
            ("close_forum_topic", {"message_thread_id": "thread"}),
            ("delete_forum_topic", {"message_thread_id": "thread"}),
            ("close_general_forum_topic", {}),
            ("hide_general_forum_topic", {}),
        ],
    )
    async def test_forum_methods_refuse_a_chat_with_topics_off(self, owned_forum, name, kwargs):
        env, chat, thread_id, owner, _alice = owned_forum
        await owner.set_topics(False)
        kwargs = {key: thread_id if value == "thread" else value for key, value in kwargs.items()}

        with pytest.raises(TelegramBadRequest, match="Bad Request: the chat is not a forum$"):
            await getattr(env.bot, name)(chat_id=chat.id, **kwargs)

    async def test_turning_topics_on_again_restores_them(self, owned_forum):
        env, chat, thread_id, owner, _alice = owned_forum
        await owner.set_topics(False)

        await owner.set_topics(True)
        sent = await env.bot.send_message(chat_id=chat.id, text="x", message_thread_id=thread_id)

        assert chat.is_forum is True
        assert chat.topic(thread_id).name == "Game"
        assert sent.message_thread_id == thread_id
        assert sent.reply_to_message is chat.topic(thread_id).root_message

    async def test_only_the_owner_can_turn_topics_off(self, owned_forum):
        _env, chat, _thread_id, _owner, alice = owned_forum

        with pytest.raises(WorldLookupError, match="Only the owner of chat"):
            await alice.in_(chat).set_topics(False)

        assert chat.is_forum is True

    async def test_topics_exist_in_supergroups_only(self, env, alice):
        with pytest.raises(WorldLookupError, match="supergroups only"):
            await alice.set_topics(True)

    async def test_a_supergroup_can_be_declared_a_forum_without_topics(self, dp):
        blueprint = Blueprint()
        chat = blueprint.add_supergroup(
            "Team",
            is_forum=True,
            bot_status=ChatMemberStatus.ADMINISTRATOR,
        )
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            state = env.chat(chat)
            assert state.is_forum is True
            assert state.topics == {}

            created = await env.bot.create_forum_topic(chat_id=chat.id, name="New")

            assert created.message_thread_id in state.topics
        finally:
            env.dispose_sync()

    async def test_a_plain_supergroup_has_no_topics_to_create(self, env, team):
        with pytest.raises(TelegramBadRequest, match="the chat is not a forum"):
            await env.bot.create_forum_topic(chat_id=team.id, name="New")


class TestTheGeneralTopicIsThreadOne:
    """Message 1 of a supergroup is its creation, the General root."""

    async def test_no_topic_is_numbered_one(self, make_env):
        env, chat, thread_id = make_env(bot_status=ChatMemberStatus.ADMINISTRATOR)

        created = await env.bot.create_forum_topic(chat_id=chat.id, name="More")

        assert thread_id == 2
        assert created.message_thread_id == 3

    def test_a_supergroup_and_a_channel_start_after_it(self, dp):
        blueprint = Blueprint()
        group = blueprint.add_group("Group")
        supergroup = blueprint.add_supergroup("Supergroup")
        channel = blueprint.add_channel("Channel")
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            assert env.chat(group).allocate_message_id() == 1
            assert env.chat(supergroup).allocate_message_id() == 2
            assert env.chat(channel).allocate_message_id() == 2
        finally:
            env.dispose_sync()

    async def test_a_send_into_thread_one_is_refused(self, make_env):
        env, chat, _thread_id = make_env(bot_status=ChatMemberStatus.ADMINISTRATOR)
        before = chat.last_message_id

        with pytest.raises(TelegramBadRequest, match="Bad Request: message thread not found$"):
            await env.bot.send_message(chat_id=chat.id, text="x", message_thread_id=1)

        assert chat.last_message_id == before

    async def test_a_supergroup_that_is_no_forum_ignores_it(self, dp):
        blueprint = Blueprint()
        chat = blueprint.add_supergroup("Plain", bot_status=ChatMemberStatus.ADMINISTRATOR)
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            sent = await env.bot.send_message(chat_id=chat.id, text="x", message_thread_id=1)

            assert sent.message_thread_id is None
            assert sent.reply_to_message is None
        finally:
            env.dispose_sync()


class TestTheGeneralTopicsMessages:
    async def test_closing_and_reopening_it_post_service_messages(self, make_env):
        env, chat, _thread_id = make_env(bot_status=ChatMemberStatus.ADMINISTRATOR)

        await env.bot.close_general_forum_topic(chat_id=chat.id)
        closed = chat.messages[-1]
        await env.bot.reopen_general_forum_topic(chat_id=chat.id)
        reopened = chat.messages[-1]

        assert closed.forum_topic_closed is not None
        assert reopened.forum_topic_reopened is not None
        assert closed.message_thread_id is reopened.message_thread_id is None
        assert closed.reply_to_message is None


class TestADeletedTopicsActor:
    async def test_sending_is_a_setup_error(self, make_env):
        env, chat, thread_id = make_env(bot_status=ChatMemberStatus.ADMINISTRATOR)
        alice = env.user(env.blueprint.users[0]).in_(chat, topic=thread_id)
        await env.bot.delete_forum_topic(chat_id=chat.id, message_thread_id=thread_id)

        with pytest.raises(WorldLookupError, match=f"Topic {thread_id} was deleted"):
            await alice.send("hello")

    async def test_closing_it_is_a_setup_error(self, dp):
        blueprint = Blueprint()
        owner = blueprint.add_user("Owner")
        chat = blueprint.add_supergroup("Team", members={owner: ChatMemberStatus.CREATOR})
        topic = blueprint.add_topic(chat, "Game")
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            actor = env.user(owner).in_(chat, topic=topic)
            state = env.chat(chat).topic(topic.message_thread_id)
            await actor.delete_topic()

            with pytest.raises(WorldLookupError, match="was deleted"):
                await actor.close_topic()
            with pytest.raises(WorldLookupError, match="was deleted"):
                await env.user(owner).in_(chat).close_topic(state)
        finally:
            env.dispose_sync()


class TestPrivateChatTopics:
    """A bot's private chats have topics of their own."""

    @pytest.fixture
    def private(self, dp):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        chat = blueprint.add_private_chat(alice)
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            yield env, env.chat(chat)
        finally:
            env.dispose_sync()

    async def test_the_bot_creates_edits_and_deletes_one(self, private):
        env, chat = private

        topic = await env.bot.create_forum_topic(chat_id=chat.id, name="Ideas")
        thread_id = topic.message_thread_id
        assert await env.bot.edit_forum_topic(
            chat_id=chat.id,
            message_thread_id=thread_id,
            name="Plans",
        )
        assert chat.topic(thread_id).name == "Plans"
        assert await env.bot.delete_forum_topic(chat_id=chat.id, message_thread_id=thread_id)
        assert thread_id not in chat.topics

    async def test_a_message_in_one_is_tagged_and_replies_to_nothing(self, private):
        env, chat = private
        topic = await env.bot.create_forum_topic(chat_id=chat.id, name="Ideas")

        sent = await env.bot.send_message(
            chat_id=chat.id,
            text="x",
            message_thread_id=topic.message_thread_id,
        )

        assert sent.message_thread_id == topic.message_thread_id
        assert sent.is_topic_message is True
        assert sent.reply_to_message is None
        assert sent.chat.is_forum is None

    async def test_an_actor_in_one_replies_to_nothing(self, private):
        env, chat = private
        topic = await env.bot.create_forum_topic(chat_id=chat.id, name="Ideas")
        alice = env.user(chat.id).in_(chat, topic=topic.message_thread_id)

        await alice.send("hi")

        assert chat.messages[-1].message_thread_id == topic.message_thread_id
        assert chat.messages[-1].reply_to_message is None

    async def test_an_unknown_thread_is_refused(self, private):
        env, chat = private

        with pytest.raises(TelegramBadRequest, match="message thread not found"):
            await env.bot.send_message(chat_id=chat.id, text="x", message_thread_id=7)

    @pytest.mark.parametrize(
        "call",
        [
            lambda bot, chat_id: bot.close_forum_topic(chat_id=chat_id, message_thread_id=2),
            lambda bot, chat_id: bot.hide_general_forum_topic(chat_id=chat_id),
        ],
    )
    async def test_closing_is_a_supergroups(self, private, call):
        env, chat = private

        with pytest.raises(
            TelegramBadRequest,
            match="Bad Request: the chat is not a supergroup forum$",
        ):
            await call(env.bot, chat.id)
