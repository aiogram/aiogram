import pytest

from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import GetForumTopicIconStickers
from aiogram.test import Blueprint, BotTestEnvironment
from aiogram.test.world import (
    BASE_DATE,
    DEFAULT_TOPIC_ICON_COLOR,
    ChatState,
    WorldLookupError,
    create_topic,
)
from aiogram.types import ForumTopic


@pytest.fixture
def forum_blueprint():
    blueprint = Blueprint()
    alice = blueprint.add_user("Alice")
    chat = blueprint.add_supergroup("Team")
    blueprint.add_topic(chat, "Support")
    blueprint.add_topic(chat, "Random")
    blueprint.add_private_chat(alice)
    return blueprint


@pytest.fixture
def forum_env(forum_blueprint, dp):
    environment = BotTestEnvironment(blueprint=forum_blueprint, dispatcher=dp)
    try:
        yield environment
    finally:
        environment.dispose_sync()


@pytest.fixture
def forum(forum_env, forum_blueprint):
    return forum_env.chat(forum_blueprint.chats[0])


@pytest.fixture
def support(forum_blueprint):
    return forum_blueprint.topics[0]


class TestTopicWorldState:
    def test_creating_a_topic_numbers_it_by_its_service_message(self):
        chat = ChatState(id=-100)

        topic = create_topic(chat, name="Support", date=BASE_DATE)

        assert chat.is_forum
        assert topic.message_thread_id == chat.messages[-1].message_id
        assert chat.messages[-1].forum_topic_created.name == "Support"

    def test_topic_messages_are_a_filtered_view(self, forum_env, forum, forum_blueprint):
        first, second = forum_blueprint.topics
        first_topic = forum.topic(first.message_thread_id)
        second_topic = forum.topic(second.message_thread_id)
        before = len(first_topic.messages)

        forum.add_message(
            first_topic.messages[0].model_copy(
                update={"message_id": forum.allocate_message_id(), "text": "in support"},
            ),
        )

        assert len(first_topic.messages) == before + 1
        assert len(second_topic.messages) == 1
        assert first_topic.messages[-1].text == "in support"

    def test_general_topic_holds_untagged_messages(self, forum_env, forum):
        forum.add_message(
            forum.messages[0].model_copy(
                update={
                    "message_id": forum.allocate_message_id(),
                    "message_thread_id": None,
                    "is_topic_message": None,
                    "forum_topic_created": None,
                    "text": "general",
                },
            ),
        )

        assert [item.text for item in forum.general_topic.messages] == ["general"]
        assert forum.general_topic.is_general

    def test_unknown_topic_lookup(self, forum):
        with pytest.raises(WorldLookupError, match="does not exist"):
            forum.topic(999)

    def test_general_topic_is_not_a_forum_topic(self, forum):
        with pytest.raises(WorldLookupError, match="not represented as a ForumTopic"):
            forum.general_topic.as_forum_topic()

    def test_lookup_by_none_returns_general(self, forum):
        assert forum.topic(None) is forum.general_topic


class TestTopicDeclaration:
    def test_declared_topics_exist_in_every_environment(self, forum_env, forum, forum_blueprint):
        assert sorted(forum.topics) == [
            topic.message_thread_id for topic in forum_blueprint.topics
        ]
        assert forum.is_forum

    def test_chat_reports_itself_as_a_forum_to_handlers(self, forum_env, forum):
        assert forum.as_chat().is_forum is True

    def test_environments_do_not_share_topic_state(self, forum_blueprint, dp):
        first = BotTestEnvironment(blueprint=forum_blueprint, dispatcher=dp)
        chat_id = forum_blueprint.chats[0].id
        thread_id = forum_blueprint.topics[0].message_thread_id
        first.chat(chat_id).topic(thread_id).is_closed = True
        first.dispose_sync()

        second = BotTestEnvironment(blueprint=forum_blueprint, dispatcher=dp)
        try:
            assert second.chat(chat_id).topic(thread_id).is_closed is False
        finally:
            second.dispose_sync()


class TestForumMethods:
    async def test_create(self, forum_env, forum):
        topic = await forum_env.bot.create_forum_topic(chat_id=forum.id, name="Bugs")

        assert isinstance(topic, ForumTopic)
        assert forum.topic(topic.message_thread_id).name == "Bugs"
        assert forum.messages[-1].forum_topic_created.name == "Bugs"
        assert forum.topic(topic.message_thread_id).icon_color == DEFAULT_TOPIC_ICON_COLOR

    async def test_create_with_an_icon(self, forum_env, forum):
        topic = await forum_env.bot.create_forum_topic(
            chat_id=forum.id,
            name="Bugs",
            icon_color=0x6FB9F0,
            icon_custom_emoji_id="emoji",
        )

        assert forum.topic(topic.message_thread_id).icon_custom_emoji_id == "emoji"

    async def test_edit(self, forum_env, forum, support):
        assert await forum_env.bot.edit_forum_topic(
            chat_id=forum.id,
            message_thread_id=support.message_thread_id,
            name="Helpdesk",
        )

        assert forum.topic(support.message_thread_id).name == "Helpdesk"
        assert forum.messages[-1].forum_topic_edited.name == "Helpdesk"

    async def test_edit_only_the_icon(self, forum_env, forum, support):
        await forum_env.bot.edit_forum_topic(
            chat_id=forum.id,
            message_thread_id=support.message_thread_id,
            icon_custom_emoji_id="emoji",
        )

        topic = forum.topic(support.message_thread_id)
        assert topic.icon_custom_emoji_id == "emoji"
        assert topic.name == "Support"

    async def test_close_and_reopen(self, forum_env, forum, support):
        await forum_env.bot.close_forum_topic(
            chat_id=forum.id,
            message_thread_id=support.message_thread_id,
        )
        assert forum.topic(support.message_thread_id).is_closed
        assert forum.messages[-1].forum_topic_closed is not None

        await forum_env.bot.reopen_forum_topic(
            chat_id=forum.id,
            message_thread_id=support.message_thread_id,
        )
        assert forum.topic(support.message_thread_id).is_closed is False
        assert forum.messages[-1].forum_topic_reopened is not None

    async def test_delete_removes_the_topic_and_its_messages(self, forum_env, forum, support):
        await forum_env.bot.send_message(
            chat_id=forum.id,
            text="inside",
            message_thread_id=support.message_thread_id,
        )

        assert await forum_env.bot.delete_forum_topic(
            chat_id=forum.id,
            message_thread_id=support.message_thread_id,
        )

        assert support.message_thread_id not in forum.topics
        assert all(item.message_thread_id != support.message_thread_id for item in forum.messages)

    async def test_posting_into_a_deleted_topic_fails(self, forum_env, forum, support):
        await forum_env.bot.delete_forum_topic(
            chat_id=forum.id,
            message_thread_id=support.message_thread_id,
        )

        with pytest.raises(TelegramBadRequest, match="does not exist"):
            await forum_env.bot.send_message(
                chat_id=forum.id,
                text="x",
                message_thread_id=support.message_thread_id,
            )

    async def test_posting_into_an_unknown_topic_fails(self, forum_env, forum):
        with pytest.raises(TelegramBadRequest, match="does not exist"):
            await forum_env.bot.send_message(chat_id=forum.id, text="x", message_thread_id=999)

    async def test_acting_on_an_unknown_topic_fails(self, forum_env, forum):
        with pytest.raises(TelegramBadRequest, match="does not exist"):
            await forum_env.bot.close_forum_topic(chat_id=forum.id, message_thread_id=999)

    async def test_unpin_all_topic_messages(self, forum_env, forum, support):
        message = await forum_env.bot.send_message(
            chat_id=forum.id,
            text="inside",
            message_thread_id=support.message_thread_id,
        )
        other = await forum_env.bot.send_message(chat_id=forum.id, text="general")
        await forum_env.bot.pin_chat_message(chat_id=forum.id, message_id=message.message_id)
        await forum_env.bot.pin_chat_message(chat_id=forum.id, message_id=other.message_id)

        await forum_env.bot.unpin_all_forum_topic_messages(
            chat_id=forum.id,
            message_thread_id=support.message_thread_id,
        )

        assert forum.pinned_message_ids == [other.message_id]

    async def test_icon_stickers_still_answer_from_synthesis(self, forum_env):
        result = await forum_env.bot.get_forum_topic_icon_stickers()

        assert isinstance(result, list)
        assert forum_env.calls.count(GetForumTopicIconStickers) == 1


class TestGeneralForumMethods:
    async def test_rename(self, forum_env, forum):
        assert await forum_env.bot.edit_general_forum_topic(chat_id=forum.id, name="Lobby")

        assert forum.general_topic.name == "Lobby"

    async def test_close_and_reopen(self, forum_env, forum):
        await forum_env.bot.close_general_forum_topic(chat_id=forum.id)
        assert forum.general_topic.is_closed

        await forum_env.bot.reopen_general_forum_topic(chat_id=forum.id)
        assert forum.general_topic.is_closed is False

    async def test_hide_and_unhide(self, forum_env, forum):
        await forum_env.bot.hide_general_forum_topic(chat_id=forum.id)
        assert forum.general_topic.is_hidden
        assert forum.messages[-1].general_forum_topic_hidden is not None

        await forum_env.bot.unhide_general_forum_topic(chat_id=forum.id)
        assert forum.general_topic.is_hidden is False
        assert forum.messages[-1].general_forum_topic_unhidden is not None

    async def test_unpin_all_general_messages(self, forum_env, forum, support):
        general = await forum_env.bot.send_message(chat_id=forum.id, text="general")
        inside = await forum_env.bot.send_message(
            chat_id=forum.id,
            text="inside",
            message_thread_id=support.message_thread_id,
        )
        await forum_env.bot.pin_chat_message(chat_id=forum.id, message_id=general.message_id)
        await forum_env.bot.pin_chat_message(chat_id=forum.id, message_id=inside.message_id)

        await forum_env.bot.unpin_all_general_forum_topic_messages(chat_id=forum.id)

        assert forum.pinned_message_ids == [inside.message_id]


class TestTopicAddressing:
    async def test_triggers_are_tagged(self, forum_env, dp, forum_blueprint, support):
        seen = {}

        @dp.message()
        async def handler(message):
            seen["thread"] = message.message_thread_id
            seen["is_topic"] = message.is_topic_message
            await message.answer("reply")

        actor = forum_env.user(forum_blueprint.users[0]).in_(
            forum_blueprint.chats[0],
            topic=support,
        )
        await actor.send("hi")

        assert seen == {"thread": support.message_thread_id, "is_topic": True}

    async def test_replies_stay_in_the_topic(self, forum_env, dp, forum_blueprint, forum, support):
        @dp.message()
        async def handler(message):
            await message.answer("reply")

        actor = forum_env.user(forum_blueprint.users[0]).in_(
            forum_blueprint.chats[0],
            topic=support,
        )
        await actor.send("hi")

        topic_texts = [item.text for item in forum.topic(support.message_thread_id).messages]
        assert topic_texts[-2:] == ["hi", "reply"]

    async def test_two_topics_stay_separate(self, forum_env, dp, forum_blueprint, forum):
        @dp.message()
        async def handler(message):
            await message.answer(f"echo {message.text}")

        first, second = forum_blueprint.topics
        user = forum_env.user(forum_blueprint.users[0])
        await user.in_(forum_blueprint.chats[0], topic=first).send("one")
        await user.in_(forum_blueprint.chats[0], topic=second).send("two")

        assert [item.text for item in forum.topic(first.message_thread_id).messages][-2:] == [
            "one",
            "echo one",
        ]
        assert [item.text for item in forum.topic(second.message_thread_id).messages][-2:] == [
            "two",
            "echo two",
        ]

    def test_binding_does_not_mutate_the_source_actor(self, forum_env, forum_blueprint, support):
        actor = forum_env.user(forum_blueprint.users[0])

        bound = actor.in_(forum_blueprint.chats[0], topic=support)

        assert bound.topic.message_thread_id == support.message_thread_id
        assert actor.topic is None

    def test_topic_accepts_spec_state_and_id(self, forum_env, forum_blueprint, forum, support):
        actor = forum_env.user(forum_blueprint.users[0])
        chat = forum_blueprint.chats[0]
        state = forum.topic(support.message_thread_id)

        assert actor.in_(chat, topic=support).topic is state
        assert actor.in_(chat, topic=state).topic is state
        assert actor.in_(chat, topic=support.message_thread_id).topic is state
