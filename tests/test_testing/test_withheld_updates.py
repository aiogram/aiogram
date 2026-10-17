"""A trigger that changes the world and withholds its update."""

import pytest

from aiogram import F
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.test import (
    Blueprint,
    BotTestEnvironment,
    Withheld,
    administrator_rights,
    rejections,
)
from aiogram.test.rejections import rejection_of
from aiogram.types import Message

WITHHELD = "withheld by the test with deliver=False"


@pytest.fixture
def forum(dp):
    blueprint = Blueprint()
    host = blueprint.add_user("Host")
    player = blueprint.add_user("Player")
    newcomer = blueprint.add_user("Newcomer")
    chat = blueprint.add_supergroup(
        "Game",
        members={host: ChatMemberStatus.CREATOR, player: ChatMemberStatus.MEMBER},
        is_forum=True,
    )
    blueprint.set_member(chat, host, rights=administrator_rights(is_anonymous=True))
    topic = blueprint.add_topic(chat, "Round 1")
    blueprint.add_private_chat(player)
    environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
    state = environment.chat(chat)
    try:
        yield {
            "env": environment,
            "chat": state,
            "topic": state.topic(topic.message_thread_id),
            "host": environment.user(host).in_(chat),
            "player": environment.user(player).in_(chat, topic=topic),
            "newcomer": environment.user(newcomer).in_(chat),
            "private": environment.user(player),
        }
    finally:
        environment.dispose_sync()


@pytest.fixture
def seen(dp):
    updates = []

    @dp.update.outer_middleware()
    async def collect(handler, update, data):
        updates.append(update)
        return await handler(update, data)

    return updates


class TestWithholding:
    async def test_closing_a_topic_changes_the_world_and_feeds_nothing(self, forum, seen):
        env, chat, topic = forum["env"], forum["chat"], forum["topic"]

        result = await forum["host"].close_topic(topic, deliver=False)

        assert topic.is_closed
        closed = chat.messages[-1]
        assert closed.forum_topic_closed is not None
        assert isinstance(result, Withheld)
        assert result.update.message is closed
        assert result.reason == WITHHELD
        assert seen == []
        assert env.routes == []
        env.assert_updates_handled()

    async def test_a_message_is_stored_and_not_fed(self, forum, seen):
        result = await forum["player"].send("hello", deliver=False)

        assert forum["chat"].messages[-1].text == "hello"
        assert result.update.message.text == "hello"
        assert seen == []

    async def test_a_membership_change_withholds_both_updates(self, forum, seen):
        chat = forum["chat"]

        result = await forum["newcomer"].join(deliver=False)

        assert chat.member(forum["newcomer"].user.id).status == ChatMemberStatus.MEMBER
        assert chat.messages[-1].new_chat_members[0].id == forum["newcomer"].user.id
        assert result.update.chat_member is not None
        assert seen == []

    async def test_a_promotion_takes_it_beside_the_rights(self, forum, seen):
        chat, player = forum["chat"], forum["player"]

        result = await forum["host"].promote(player.user, can_pin_messages=True, deliver=False)

        assert chat.member(player.user.id).status == ChatMemberStatus.ADMINISTRATOR
        assert isinstance(result, Withheld)
        assert seen == []

    async def test_a_created_topic_is_still_returned(self, forum, seen):
        topic = await forum["host"].create_topic("Round 2", deliver=False)

        assert topic.root_message.forum_topic_created.name == "Round 2"
        assert seen == []

    async def test_an_anonymous_administrator_takes_it_too(self, forum, seen):
        host = forum["host"].in_(forum["chat"], anonymous=True)

        result = await host.close_topic(forum["topic"], deliver=False)

        assert forum["chat"].messages[-1].sender_chat.id == forum["chat"].id
        assert result.reason == WITHHELD
        assert seen == []

    async def test_a_reply_takes_it_too(self, forum, seen):
        await forum["player"].send("first", deliver=False)

        result = await forum["player"].reply(forum["chat"].messages[-1], "second", deliver=False)

        assert result.update.message.text == "second"
        assert seen == []

    async def test_it_leaves_an_empty_route_scope(self, forum, seen):
        env = forum["env"]
        await forum["player"].send("handled")
        assert env.last_route is not None

        await forum["player"].send("lost", deliver=False)

        assert env.routes == []
        assert env.last_route is None
        assert len(env.all_routes) == 1

    async def test_delivering_is_the_default(self, forum, seen):
        await forum["host"].close_topic(forum["topic"], deliver=True)

        assert len(seen) == 1

    @pytest.mark.parametrize(
        ("trigger", "args", "kwargs"),
        [
            ("inline_query", ("q",), {}),
            ("boost", (), {}),
            ("remove_boost", (), {}),
            ("chosen_inline_result", ("r1",), {}),
            ("shipping_query", (), {}),
            ("pre_checkout_query", (), {}),
            ("pay", (), {}),
            ("purchase_paid_media", (), {}),
            ("update_subscription", (), {}),
            ("manage_bot", (), {}),
            ("stop_message_generation", (), {}),
        ],
    )
    async def test_every_trigger_takes_it(self, forum, seen, trigger, args, kwargs):
        result = await getattr(forum["private"], trigger)(*args, deliver=False, **kwargs)

        assert isinstance(result, Withheld)
        assert seen == []


class TestTheLostClosure:
    """The recipe the guide shows: the bot learns from its next send."""

    async def test_the_bot_learns_from_topic_closed(self, forum, dp):
        learned = []

        @dp.message(F.text == "/vote")
        async def vote(message: Message) -> None:
            try:
                await message.answer("Vote counted")
            except TelegramBadRequest as error:
                learned.append(error)

        await forum["host"].close_topic(forum["topic"], deliver=False)
        await forum["player"].send("/vote")

        assert [rejection_of(error) for error in learned] == [rejections.TOPIC_CLOSED]
        assert forum["topic"].messages[-1].text == "/vote"
