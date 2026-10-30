import pytest

from aiogram import F
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.test import (
    Blueprint,
    BotTestEnvironment,
    WorldLookupError,
    administrator_rights,
    default_chat_permissions,
    rejections,
)
from aiogram.types import ChatPermissions, Message

from .conftest import refused_with

NO_TOPICS = default_chat_permissions().model_copy(update={"can_manage_topics": False})


@pytest.fixture
def forum(dp):
    blueprint = Blueprint()
    owner = blueprint.add_user("Owner")
    manager = blueprint.add_user("Manager")
    limited = blueprint.add_user("Limited")
    member = blueprint.add_user("Member")
    chat = blueprint.add_supergroup(
        "Team",
        members={
            owner: ChatMemberStatus.CREATOR,
            manager: ChatMemberStatus.ADMINISTRATOR,
            limited: ChatMemberStatus.ADMINISTRATOR,
            member: ChatMemberStatus.MEMBER,
        },
        is_forum=True,
        bot_status=ChatMemberStatus.ADMINISTRATOR,
        # A stricter group than the default: members open no topics.
        permissions=NO_TOPICS,
    )
    blueprint.set_member(chat, limited, rights=administrator_rights(can_manage_topics=False))
    topic = blueprint.add_topic(chat, "Game")
    environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
    try:
        yield {
            "env": environment,
            "chat": environment.chat(chat),
            "thread_id": topic.message_thread_id,
            "topic": topic,
            "owner": environment.user(owner).in_(chat),
            "manager": environment.user(manager).in_(chat),
            "limited": environment.user(limited).in_(chat),
            "member": environment.user(member).in_(chat),
        }
    finally:
        environment.dispose_sync()


@pytest.fixture
def seen(dp):
    messages: list[Message] = []

    @dp.message()
    async def collect(message: Message) -> None:
        messages.append(message)

    return messages


class TestCreateTopic:
    async def test_the_topic_exists_and_its_service_message_is_fed(self, forum, seen):
        chat, owner = forum["chat"], forum["owner"]

        topic = await owner.create_topic("Bugs")

        assert chat.topic(topic.message_thread_id) is topic
        assert topic.name == "Bugs"
        root = chat.messages[-1]
        assert root.forum_topic_created.name == "Bugs"
        assert root.message_id == topic.message_thread_id
        assert root.from_user.id == owner.user.id
        assert [m.message_id for m in seen] == [root.message_id]

    async def test_the_icon_is_kept(self, forum):
        topic = await forum["owner"].create_topic(
            "Bugs",
            icon_color=0xFB6F5F,
            icon_custom_emoji_id="5312241539987020022",
        )

        created = forum["chat"].messages[-1].forum_topic_created
        assert (created.icon_color, created.icon_custom_emoji_id) == (
            0xFB6F5F,
            "5312241539987020022",
        )
        assert topic.icon_color == 0xFB6F5F

    async def test_a_handler_filtering_on_the_service_message_runs(self, forum, dp):
        names = []

        @dp.message(F.forum_topic_created)
        async def on_created(message: Message, label: str) -> None:
            names.append((message.forum_topic_created.name, label))

        await forum["manager"].create_topic("Bugs", label="injected")

        assert names == [("Bugs", "injected")]

    async def test_it_matches_the_bot_methods_shape(self, forum):
        env, chat = forum["env"], forum["chat"]
        by_bot = await env.bot.create_forum_topic(chat_id=chat.id, name="A")
        by_user = await forum["owner"].create_topic("B")

        bots, users = (
            chat.topic(t).root_message
            for t in (by_bot.message_thread_id, by_user.message_thread_id)
        )
        assert bots.forum_topic_created.icon_color == users.forum_topic_created.icon_color
        assert bots.is_topic_message is users.is_topic_message is True
        assert bots.message_thread_id == bots.message_id

    async def test_an_administrator_with_the_right_may(self, forum):
        topic = await forum["manager"].create_topic("Ideas")

        assert topic.message_thread_id in forum["chat"].topics


class TestCloseAndReopen:
    async def test_close_closes_and_feeds_the_service_message(self, forum, seen):
        chat, thread_id = forum["chat"], forum["thread_id"]

        await forum["owner"].close_topic(thread_id)

        assert chat.topic(thread_id).is_closed
        closed = chat.messages[-1]
        assert closed.forum_topic_closed is not None
        assert closed.message_thread_id == thread_id
        assert closed.is_topic_message is True
        assert closed.from_user.id == forum["owner"].user.id
        assert closed.reply_to_message is chat.topic(thread_id).root_message
        assert seen == [closed]

    async def test_reopen_reopens_and_feeds_the_service_message(self, forum, seen):
        chat, thread_id = forum["chat"], forum["thread_id"]
        await forum["owner"].close_topic(thread_id)
        seen.clear()

        await forum["owner"].reopen_topic(thread_id)

        assert not chat.topic(thread_id).is_closed
        assert chat.messages[-1].forum_topic_reopened is not None
        assert seen == [chat.messages[-1]]

    async def test_a_bound_actor_acts_on_its_topic_by_default(self, forum):
        chat, thread_id = forum["chat"], forum["thread_id"]
        bound = forum["owner"].in_(chat, topic=thread_id)

        await bound.close_topic()

        assert chat.topic(thread_id).is_closed

    @pytest.mark.parametrize("how", ["spec", "state", "id"])
    async def test_a_topic_is_named_three_ways(self, forum, how):
        chat, thread_id = forum["chat"], forum["thread_id"]
        named = {
            "spec": forum["topic"],
            "state": chat.topic(thread_id),
            "id": thread_id,
        }[how]

        await forum["owner"].close_topic(named)

        assert chat.topic(thread_id).is_closed

    async def test_dispatcher_data_reaches_the_handler(self, forum, dp):
        got = []

        @dp.message(F.forum_topic_closed)
        async def handler(message: Message, flag: bool) -> None:
            got.append(flag)

        await forum["owner"].close_topic(forum["thread_id"], flag=True)

        assert got == [True]

    async def test_it_matches_what_the_bot_method_does(self, forum):
        env, chat, thread_id = forum["env"], forum["chat"], forum["thread_id"]
        other = await forum["owner"].create_topic("Other")

        await env.bot.close_forum_topic(chat_id=chat.id, message_thread_id=thread_id)
        await forum["owner"].close_topic(other)

        by_bot, by_user = chat.messages[-2], chat.messages[-1]
        assert by_bot.forum_topic_closed == by_user.forum_topic_closed
        assert by_bot.is_topic_message is by_user.is_topic_message is True
        assert chat.topic(thread_id).is_closed and other.is_closed

    async def test_no_topic_to_act_on_is_a_setup_error(self, forum):
        with pytest.raises(WorldLookupError, match="No topic to act on"):
            await forum["owner"].close_topic()

    async def test_an_unknown_topic_is_a_setup_error(self, forum):
        with pytest.raises(WorldLookupError, match="Topic 999 does not exist"):
            await forum["owner"].close_topic(999)

    async def test_the_general_topic_has_triggers_of_its_own(self, forum):
        general = forum["chat"].general_topic
        with pytest.raises(WorldLookupError, match=r"`close_general_topic\(\)`"):
            await forum["owner"].close_topic(general)
        with pytest.raises(WorldLookupError, match=r"`reopen_general_topic\(\)`"):
            await forum["owner"].reopen_topic(general)


class TestDeleteTopic:
    async def test_the_topic_goes_with_its_messages_and_feeds_nothing(self, forum, seen):
        env, chat, thread_id = forum["env"], forum["chat"], forum["thread_id"]
        await forum["member"].in_(chat, topic=thread_id).send("hello")
        seen.clear()

        assert await forum["owner"].delete_topic(thread_id) is None

        assert thread_id not in chat.topics
        assert all(m.message_thread_id != thread_id for m in chat.messages)
        assert seen == []
        with pytest.raises(TelegramBadRequest, match="message thread not found"):
            await env.bot.send_message(chat_id=chat.id, text="x", message_thread_id=thread_id)

    async def test_it_posts_no_service_message(self, forum):
        chat, thread_id = forum["chat"], forum["thread_id"]
        before = [m.message_id for m in chat.messages if m.message_thread_id != thread_id]

        await forum["owner"].delete_topic(thread_id)

        assert [m.message_id for m in chat.messages] == before

    async def test_the_general_topic_cannot_be_deleted(self, forum):
        with pytest.raises(WorldLookupError, match="General topic"):
            await forum["owner"].delete_topic(forum["chat"].general_topic)


class TestGeneralTopic:
    async def test_hiding_closes_and_feeds(self, forum, seen):
        chat = forum["chat"]

        await forum["owner"].hide_general_topic()

        assert chat.general_topic.is_hidden and chat.general_topic.is_closed
        hidden = chat.messages[-1]
        assert hidden.general_forum_topic_hidden is not None
        assert hidden.message_thread_id is None
        assert hidden.from_user.id == forum["owner"].user.id
        assert seen == [hidden]

    async def test_unhiding_feeds(self, forum, seen):
        chat = forum["chat"]
        await forum["owner"].hide_general_topic()
        seen.clear()

        await forum["owner"].unhide_general_topic()

        assert not chat.general_topic.is_hidden
        assert chat.messages[-1].general_forum_topic_unhidden is not None
        assert seen == [chat.messages[-1]]

    async def test_closing_and_reopening_feed_their_messages(self, forum, seen):
        general = forum["chat"].general_topic
        owner = forum["owner"]

        await owner.close_general_topic()
        assert general.is_closed
        await owner.hide_general_topic()
        await owner.reopen_general_topic()

        assert not general.is_closed and not general.is_hidden
        closed, hidden, reopened = seen
        assert closed.forum_topic_closed is not None
        assert hidden.general_forum_topic_hidden is not None
        # One message says it reopened, unhidden as well.
        assert reopened.forum_topic_reopened is not None
        assert {m.from_user.id for m in seen} == {owner.user.id}
        assert {m.message_thread_id for m in seen} == {None}

    async def test_it_matches_what_the_bot_methods_do(self, forum):
        env, chat = forum["env"], forum["chat"]

        await env.bot.hide_general_forum_topic(chat_id=chat.id)
        by_bot = chat.messages[-1]
        await forum["owner"].unhide_general_topic()
        await forum["owner"].hide_general_topic()
        by_user = chat.messages[-1]

        assert by_bot.general_forum_topic_hidden == by_user.general_forum_topic_hidden
        assert by_bot.message_thread_id == by_user.message_thread_id is None


class TestWhoMay:
    async def test_a_closed_topic_takes_the_owners_message_afterwards(self, forum):
        env, chat, thread_id = forum["env"], forum["chat"], forum["thread_id"]
        await forum["owner"].close_topic(thread_id)
        # A bot that may manage topics would post anyway.
        chat.member(env.world.bot_user.id).set_status(ChatMemberStatus.MEMBER)

        with refused_with(TelegramBadRequest, rejections.TOPIC_CLOSED):
            await env.bot.send_message(chat_id=chat.id, text="x", message_thread_id=thread_id)

    @pytest.mark.parametrize("who", ["limited", "member"])
    @pytest.mark.parametrize(
        "action",
        [
            lambda actor, t: actor.create_topic("New"),
            lambda actor, t: actor.close_topic(t),
            lambda actor, t: actor.reopen_topic(t),
            lambda actor, t: actor.delete_topic(t),
            lambda actor, t: actor.hide_general_topic(),
            lambda actor, t: actor.unhide_general_topic(),
            lambda actor, t: actor.close_general_topic(),
            lambda actor, t: actor.reopen_general_topic(),
        ],
    )
    async def test_without_the_right_it_is_a_setup_error(self, forum, who, action):
        chat, thread_id = forum["chat"], forum["thread_id"]
        before = (len(chat.messages), dict(chat.topics))

        with pytest.raises(WorldLookupError, match="can_manage_topics") as caught:
            await action(forum[who], thread_id)

        assert "administrator_rights" in str(caught.value)
        assert (len(chat.messages), dict(chat.topics)) == before
        assert not chat.topic(thread_id).is_closed
        assert not chat.general_topic.is_closed

    async def test_the_message_names_the_status(self, forum):
        with pytest.raises(WorldLookupError, match="their status is member"):
            await forum["member"].create_topic("New")

    async def test_a_chat_that_is_not_a_forum_is_a_setup_error(self, forum):
        await forum["owner"].set_topics(False)

        with pytest.raises(WorldLookupError, match=r"not a forum.*set_topics\(True\)"):
            await forum["owner"].create_topic("New")

    async def test_enforce_bot_rights_does_not_loosen_the_guard(self, dp):
        blueprint = Blueprint()
        member = blueprint.add_user("Member")
        chat = blueprint.add_supergroup(
            "Team",
            members={member: ChatMemberStatus.MEMBER},
            is_forum=True,
            permissions=NO_TOPICS,
        )
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp, enforce_bot_rights=False)
        try:
            with pytest.raises(WorldLookupError, match="can_manage_topics"):
                await env.user(member).in_(chat).create_topic("New")
        finally:
            env.dispose_sync()


class TestTheChatPermission:
    """``can_manage_topics`` on the chat lets members open topics."""

    GRANTED = ChatPermissions(can_send_messages=True, can_manage_topics=True)

    @pytest.mark.parametrize("who", ["member", "limited"])
    async def test_it_lets_a_user_create_a_topic(self, forum, who):
        forum["chat"].permissions = self.GRANTED

        topic = await forum[who].create_topic("Ideas")

        assert topic.creator_id == forum[who].user.id

    async def test_a_restriction_takes_it_away(self, forum):
        chat = forum["chat"]
        chat.permissions = self.GRANTED
        restricted = chat.member(forum["member"].user.id)
        restricted.set_status(ChatMemberStatus.RESTRICTED)
        restricted.permissions = ChatPermissions(can_send_messages=True)

        with pytest.raises(WorldLookupError, match="grant it on the chat's `permissions`"):
            await forum["member"].create_topic("Ideas")

    async def test_it_does_not_let_them_close_another_topic(self, forum):
        forum["chat"].permissions = self.GRANTED

        with pytest.raises(WorldLookupError, match="can_manage_topics"):
            await forum["member"].close_topic(forum["thread_id"])

    async def test_the_creator_manages_their_own_topic(self, forum):
        forum["chat"].permissions = self.GRANTED
        member = forum["member"]
        topic = await member.create_topic("Ideas")

        await member.close_topic(topic)
        await member.reopen_topic(topic)
        await member.delete_topic(topic)

        assert topic.message_thread_id not in forum["chat"].topics
