import asyncio

import pytest

from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.methods import CopyMessages, SendMediaGroup, SendMessage, SetChatTitle
from aiogram.test import Blueprint, BotTestEnvironment, RateLimit, RateLimits
from aiogram.test.flood import RATE_LIMITED_METHODS, FloodControl
from aiogram.test.modeling import SENDING_METHODS
from aiogram.types import ChatPermissions, InputMediaPhoto, ReplyParameters


@pytest.fixture
def make_env(dp):
    environments = []

    def make(rate_limits=None):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        blueprint.add_private_chat(alice)
        team = blueprint.add_supergroup("Team", bot_status=ChatMemberStatus.ADMINISTRATOR)
        first = blueprint.add_topic(team, "Day")
        second = blueprint.add_topic(team, "Night")
        blueprint.add_supergroup("Other", bot_status=ChatMemberStatus.ADMINISTRATOR)
        environment = BotTestEnvironment(
            blueprint=blueprint,
            dispatcher=dp,
            rate_limits=rate_limits,
        )
        environments.append(environment)
        return environment, blueprint, (first.message_thread_id, second.message_thread_id)

    yield make
    for environment in environments:
        environment.dispose_sync()


PRIVATE, TEAM, OTHER = 0, 1, 2


def chat_id(blueprint, index):
    return blueprint.chats[index].id


class TestOffByDefault:
    async def test_a_burst_goes_through(self, make_env):
        env, blueprint, _threads = make_env()

        for number in range(30):
            await env.bot.send_message(chat_id=chat_id(blueprint, TEAM), text=str(number))

        assert env.rate_limits is None
        assert len(env.chat(chat_id(blueprint, TEAM)).messages) == 30 + 2


class TestPerChat:
    async def test_a_second_message_in_the_same_second_is_refused(self, make_env):
        env, blueprint, _threads = make_env(RateLimits())
        target = chat_id(blueprint, PRIVATE)
        await env.bot.send_message(chat_id=target, text="one")

        with pytest.raises(TelegramRetryAfter) as raised:
            await env.bot.send_message(chat_id=target, text="two")

        assert raised.value.retry_after == 1
        assert "Too Many Requests: retry after 1" in str(raised.value)
        assert [message.text for message in env.chat(target).messages] == ["one"]
        assert env.calls.count(SendMessage) == 2

    async def test_waiting_out_the_retry_lets_it_through(self, make_env):
        env, blueprint, _threads = make_env(RateLimits())
        target = chat_id(blueprint, PRIVATE)
        await env.bot.send_message(chat_id=target, text="one")
        with pytest.raises(TelegramRetryAfter) as raised:
            await env.bot.send_message(chat_id=target, text="two")

        await env.advance_time(raised.value.retry_after)
        await env.bot.send_message(chat_id=target, text="two")

        assert env.chat(target).messages[-1].text == "two"

    async def test_chats_are_limited_apart(self, make_env):
        env, blueprint, _threads = make_env(RateLimits())

        for index in (PRIVATE, TEAM, OTHER):
            await env.bot.send_message(chat_id=chat_id(blueprint, index), text="hi")

        assert env.chat(chat_id(blueprint, OTHER)).messages[-1].text == "hi"

    @pytest.mark.parametrize(
        "send",
        [
            lambda bot, target: bot.send_photo(chat_id=target, photo="file"),
            lambda bot, target: bot.send_poll(chat_id=target, question="?", options=["a", "b"]),
            lambda bot, target: bot.send_media_group(
                chat_id=target,
                media=[InputMediaPhoto(media="a"), InputMediaPhoto(media="b")],
            ),
            lambda bot, target: bot.copy_message(
                chat_id=target,
                from_chat_id=target,
                message_id=1,
            ),
        ],
        ids=["photo", "poll", "media_group", "copy"],
    )
    async def test_every_message_producing_call_counts(self, make_env, send):
        env, blueprint, _threads = make_env(RateLimits())
        target = chat_id(blueprint, PRIVATE)
        await env.bot.send_message(chat_id=target, text="one")

        with pytest.raises(TelegramRetryAfter):
            await send(env.bot, target)

    async def test_an_album_counts_once(self, make_env):
        env, blueprint, _threads = make_env(RateLimits())
        target = chat_id(blueprint, PRIVATE)

        sent = await env.bot.send_media_group(
            chat_id=target,
            media=[InputMediaPhoto(media="a"), InputMediaPhoto(media="b")],
        )

        assert len(sent) == 2

    async def test_a_refused_send_is_not_counted(self, make_env):
        env, blueprint, _threads = make_env(RateLimits())
        target = chat_id(blueprint, TEAM)
        with pytest.raises(TelegramBadRequest, match="message thread not found"):
            await env.bot.send_message(chat_id=target, text="lost", message_thread_id=999)

        await env.bot.send_message(chat_id=target, text="sent")

        assert env.chat(target).messages[-1].text == "sent"

    async def test_an_override_answers_before_the_limits(self, make_env):
        env, blueprint, _threads = make_env(RateLimits())
        target = chat_id(blueprint, PRIVATE)
        await env.bot.send_message(chat_id=target, text="one")
        env.on(SendMessage).raises(TelegramBadRequest, "Bad Request: declared", times=1)

        with pytest.raises(TelegramBadRequest, match="declared"):
            await env.bot.send_message(chat_id=target, text="two")

    async def test_the_event_loop_clock_moves_the_window(self, make_env, monkeypatch):
        env, blueprint, _threads = make_env(RateLimits())
        target = chat_id(blueprint, PRIVATE)
        loop = asyncio.get_running_loop()
        start = loop.time()
        monkeypatch.setattr(loop, "time", lambda: start)
        await env.bot.send_message(chat_id=target, text="one")

        monkeypatch.setattr(loop, "time", lambda: start + 1.0)
        await env.bot.send_message(chat_id=target, text="two")

        assert env.chat(target).messages[-1].text == "two"


class TestPerGroup:
    LIMITS = RateLimits(per_chat=None)

    async def test_twenty_a_minute_are_shared_across_topics(self, make_env):
        env, blueprint, threads = make_env(self.LIMITS)
        target = chat_id(blueprint, TEAM)
        for number in range(20):
            await env.bot.send_message(
                chat_id=target,
                text=str(number),
                message_thread_id=threads[number % 2],
            )

        with pytest.raises(TelegramRetryAfter) as raised:
            await env.bot.send_message(chat_id=target, text="21st")

        assert raised.value.retry_after == 60

    async def test_the_retry_after_is_the_truth(self, make_env):
        env, blueprint, _threads = make_env(RateLimits(per_chat=None, per_group=RateLimit(2, 10)))
        target = chat_id(blueprint, TEAM)
        await env.bot.send_message(chat_id=target, text="1")
        await env.advance_time(4)
        await env.bot.send_message(chat_id=target, text="2")

        with pytest.raises(TelegramRetryAfter) as first:
            await env.bot.send_message(chat_id=target, text="3")
        await env.advance_time(first.value.retry_after - 1)
        with pytest.raises(TelegramRetryAfter) as second:
            await env.bot.send_message(chat_id=target, text="3")
        await env.advance_time(second.value.retry_after)
        await env.bot.send_message(chat_id=target, text="3")

        assert (first.value.retry_after, second.value.retry_after) == (6, 1)
        assert env.chat(target).messages[-1].text == "3"

    async def test_a_private_chat_is_not_a_group(self, make_env):
        env, blueprint, _threads = make_env(self.LIMITS)
        target = chat_id(blueprint, PRIVATE)

        for number in range(25):
            await env.bot.send_message(chat_id=target, text=str(number))

        assert len(env.chat(target).messages) == 25


class TestFloodControl:
    def test_no_limit_forgets_everything(self):
        control = FloodControl(RateLimits(per_chat=None, per_group=None))

        control.record(1, "private", 0.0)

        assert control.retry_after(1, "private", 0.0) is None
        assert list(control.sent[1]) == []

    def test_old_sends_are_forgotten(self):
        control = FloodControl(RateLimits())

        control.record(1, "private", 0.0)
        control.record(1, "private", 5.0)

        assert list(control.sent[1]) == [5.0]


class TestRecipe:
    async def test_a_declared_flood_refusal(self, make_env):
        """The override recipe in the docs, kept from rotting."""
        env, blueprint, _threads = make_env()
        target = chat_id(blueprint, TEAM)
        flood = TelegramRetryAfter(
            method=SendMessage(chat_id=target, text=""),
            message="Too Many Requests: retry after 5",
            retry_after=5,
        )
        env.on(SendMessage, chat_id=target).raises(flood, times=1)

        with pytest.raises(TelegramRetryAfter) as raised:
            await env.bot.send_message(chat_id=target, text="x")
        await env.bot.send_message(chat_id=target, text="x")

        assert raised.value.retry_after == 5
        assert env.chat(target).messages[-1].text == "x"


class TestLocalChecksComeFirst:
    """A call Telegram refuses locally is refused so when flooded."""

    @pytest.fixture
    async def flooded(self, make_env):
        env, blueprint, threads = make_env(RateLimits())
        target = chat_id(blueprint, TEAM)
        await env.bot.send_message(chat_id=target, text="one")
        with pytest.raises(TelegramRetryAfter):
            await env.bot.send_message(chat_id=target, text="two")
        return env, env.chat(target), threads

    async def test_an_unknown_thread_answers_400(self, flooded):
        env, chat, _threads = flooded

        with pytest.raises(TelegramBadRequest, match="message thread not found"):
            await env.bot.send_message(chat_id=chat.id, text="x", message_thread_id=999)

    async def test_a_missing_reply_answers_400(self, flooded):
        env, chat, _threads = flooded

        with pytest.raises(TelegramBadRequest, match="message to be replied not found"):
            await env.bot.send_message(
                chat_id=chat.id,
                text="x",
                reply_parameters=ReplyParameters(message_id=999),
            )

    async def test_missing_rights_answer_400(self, flooded):
        env, chat, _threads = flooded
        chat.member(env.world.bot_user.id).set_status(ChatMemberStatus.MEMBER)
        chat.permissions = ChatPermissions(can_send_messages=False)

        with pytest.raises(TelegramBadRequest, match="send text messages"):
            await env.bot.send_message(chat_id=chat.id, text="x")

    async def test_a_valid_send_is_still_flooded(self, flooded):
        env, chat, _threads = flooded
        before = list(chat.messages)

        with pytest.raises(TelegramRetryAfter):
            await env.bot.send_message(chat_id=chat.id, text="x")

        assert chat.messages == before

    async def test_a_flooded_copy_of_a_poll_registers_no_poll(self, make_env):
        env, blueprint, _threads = make_env(RateLimits())
        target = chat_id(blueprint, PRIVATE)
        poll = await env.bot.send_poll(chat_id=target, question="?", options=["a", "b"])
        polls = dict(env.world.polls)

        with pytest.raises(TelegramRetryAfter):
            await env.bot.copy_message(
                chat_id=target,
                from_chat_id=target,
                message_id=poll.message_id,
            )

        assert env.world.polls == polls


def test_the_counted_methods_are_the_modeled_sends():
    assert frozenset(SENDING_METHODS) == RATE_LIMITED_METHODS
    assert {SendMessage, SendMediaGroup, CopyMessages} <= RATE_LIMITED_METHODS
    assert SetChatTitle not in RATE_LIMITED_METHODS
