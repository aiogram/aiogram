import asyncio

import pytest

from aiogram.test import Blueprint, BotTestEnvironment, TopicState, WaitTimeoutError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


async def flip_later(flag: dict, delay: float = 0.02) -> None:
    await asyncio.sleep(delay)
    flag["ready"] = True


class TestWaitFor:
    async def test_already_true_returns_without_waiting(self, env):
        loop = asyncio.get_running_loop()
        started = loop.time()

        assert await env.wait_for(lambda: "value", timeout=5.0) == "value"

        assert loop.time() - started < 1.0

    async def test_picks_up_a_change_from_a_background_task(self, env):
        flag = {"ready": False}
        task = asyncio.create_task(flip_later(flag))

        try:
            assert await env.wait_for(lambda: flag["ready"])
        finally:
            await task

    async def test_returns_the_truthy_value(self, env):
        found = {}
        task = asyncio.create_task(self.fill_later(found))

        try:
            assert await env.wait_for(lambda: found.get("victim")) == "Alice"
        finally:
            await task

    @staticmethod
    async def fill_later(found: dict) -> None:
        await asyncio.sleep(0.02)
        found["victim"] = "Alice"

    async def test_async_predicate_is_awaited(self, env):
        flag = {"ready": False}
        task = asyncio.create_task(flip_later(flag))

        async def ready():
            return flag["ready"]

        try:
            assert await env.wait_for(ready)
        finally:
            await task

    async def test_timeout_raises_a_timeout_error(self, env):
        with pytest.raises(WaitTimeoutError) as exc_info:
            await env.wait_for(lambda: False, timeout=0.05, description="the night phase")

        assert isinstance(exc_info.value, TimeoutError)
        assert "the night phase" in str(exc_info.value)
        assert "0.05" in str(exc_info.value)

    async def test_timeout_without_a_description_identifies_the_predicate(self, env):
        def game_is_over():
            return False

        with pytest.raises(WaitTimeoutError, match="game_is_over"):
            await env.wait_for(game_is_over, timeout=0.05)

        with pytest.raises(WaitTimeoutError, match="description="):
            await env.wait_for(lambda: False, timeout=0.05)

    async def test_the_timeout_is_honoured_with_a_coarser_interval(self, env):
        """
        The last sleep is clamped to what is left, so ``timeout`` means what it says.

        Sleeping a full interval regardless made a wait with a coarse interval overshoot
        by up to that interval — a 0.05s timeout returning after a full second.
        """
        loop = asyncio.get_running_loop()
        started = loop.time()

        with pytest.raises(WaitTimeoutError):
            await env.wait_for(lambda: False, timeout=0.05, interval=1.0, description="x")

        assert loop.time() - started < 0.5

    async def test_a_predicate_without_a_name_falls_back_to_its_repr(self, env):
        class NeverReady:
            def __call__(self):
                return False

        predicate = NeverReady()

        with pytest.raises(WaitTimeoutError, match="NeverReady object at"):
            await env.wait_for(predicate, timeout=0.05)


class TestWaitForMessage:
    async def test_a_message_already_there_matches_immediately(self, env, private):
        await env.bot.send_message(chat_id=private.id, text="already here")

        message = await private.wait_for_message(lambda item: item.text == "already here")

        assert message.message_id == private.messages[-1].message_id

    async def test_a_message_sent_by_a_background_task_matches(self, env, private):
        async def announce():
            await asyncio.sleep(0.02)
            await env.bot.send_message(chat_id=private.id, text="Night falls")

        task = asyncio.create_task(announce())

        try:
            message = await private.wait_for_message(lambda item: item.text.startswith("Night"))
        finally:
            await task

        assert message.text == "Night falls"

    async def test_the_newest_matching_message_is_returned(self, env, private):
        await env.bot.send_message(chat_id=private.id, text="tick 1")
        await env.bot.send_message(chat_id=private.id, text="tick 2")

        message = await private.wait_for_message(lambda item: item.text.startswith("tick"))

        assert message.text == "tick 2"

    async def test_without_a_predicate_any_message_matches(self, env, private):
        async def chatter():
            await asyncio.sleep(0.02)
            await env.bot.send_message(chat_id=private.id, text="anything")

        task = asyncio.create_task(chatter())

        try:
            message = await private.wait_for_message()
        finally:
            await task

        assert message.text == "anything"

    async def test_timeout_lists_the_messages_the_chat_holds(self, env, private):
        await env.bot.send_message(chat_id=private.id, text="hello")
        await env.bot.send_message(
            chat_id=private.id,
            text="pick one",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
            ),
        )
        expected_id = private.messages[-1].message_id

        with pytest.raises(WaitTimeoutError) as exc_info:
            await private.wait_for_message(lambda item: item.text == "never", timeout=0.05)

        text = str(exc_info.value)
        assert isinstance(exc_info.value, TimeoutError)
        assert f"chat {private.id}" in text
        assert "0.05" in text
        assert "'hello'" in text
        assert f"#{expected_id} 'pick one' [inline keyboard]" in text

    async def test_timeout_on_an_empty_chat_says_so(self, env, private):
        with pytest.raises(WaitTimeoutError, match="holds no messages"):
            await private.wait_for_message(timeout=0.05)

    async def test_a_message_without_text_is_still_identified(self, env, private):
        await env.bot.send_dice(chat_id=private.id)
        expected_id = private.messages[-1].message_id

        with pytest.raises(WaitTimeoutError) as exc_info:
            await private.wait_for_message(lambda item: False, timeout=0.05)

        assert f"#{expected_id} <no text>" in str(exc_info.value)

    async def test_a_long_text_is_truncated(self, env, private):
        await env.bot.send_message(chat_id=private.id, text="x" * 200)

        with pytest.raises(WaitTimeoutError) as exc_info:
            await private.wait_for_message(lambda item: False, timeout=0.05)

        assert "x" * 60 + "'..." in str(exc_info.value)
        assert "x" * 100 not in str(exc_info.value)

    def test_describe_messages_names_the_chat(self, env, private):
        assert private.describe_messages() == "The chat holds no messages."

    async def test_the_message_it_returns_is_usable(self, env, alice, private):
        """A user's message is stored, not returned by any call — and still mounted."""
        await alice.send("ping")

        message = await private.wait_for_message(lambda item: item.text == "ping")
        await message.answer("pong")

        assert [item.text for item in private.messages] == ["ping", "pong"]


class TestAPredicateThatRaises:
    """
    A chat holds messages of every shape, so a natural predicate blows up on some of them.

    ``lambda m: m.text.startswith(...)`` meets a service message whose ``text`` is
    ``None`` — a renamed chat, a new topic — and used to fail the wait with an
    ``AttributeError`` from inside the toolkit instead of ever reaching the timeout. Such
    a message now simply does not match; but if the wait does time out, the failure names
    what the predicate raised, so a predicate that is merely broken still says so.
    """

    async def test_a_service_message_does_not_break_the_wait(self, env, team):
        await env.bot.set_chat_title(chat_id=team.id, title="Renamed")

        async def announce():
            await asyncio.sleep(0.02)
            await env.bot.send_message(chat_id=team.id, text="Night falls")

        task = asyncio.create_task(announce())
        try:
            message = await team.wait_for_message(lambda item: item.text.startswith("Night"))
        finally:
            await task

        assert message.text == "Night falls"

    async def test_the_timeout_reports_what_the_predicate_raised(self, env, team):
        await env.bot.set_chat_title(chat_id=team.id, title="Renamed")
        service_id = team.messages[-1].message_id

        with pytest.raises(WaitTimeoutError) as exc_info:
            await team.wait_for_message(lambda item: item.text.startswith("Night"), timeout=0.05)

        text = str(exc_info.value)
        assert "The predicate raised on 1 of them" in text
        assert "AttributeError(" in text
        assert f"on message #{service_id}" in text

    async def test_a_predicate_that_always_raises_still_fails_with_its_cause(self, env, private):
        await env.bot.send_message(chat_id=private.id, text="hi")

        def broken(message):
            raise ValueError("the predicate itself is wrong")

        with pytest.raises(WaitTimeoutError) as exc_info:
            await private.wait_for_message(broken, timeout=0.05)

        assert "ValueError('the predicate itself is wrong')" in str(exc_info.value)


class TestWaitForMessageInATopic:
    """The same wait, scoped to one topic's view of the chat's messages."""

    @pytest.fixture
    def forum(self, dp):
        blueprint = Blueprint()
        chat = blueprint.add_supergroup("Team")
        blueprint.add_topic(chat, "Support")
        blueprint.add_topic(chat, "Random")
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            yield environment, environment.chat(chat), blueprint.topics
        finally:
            environment.dispose_sync()

    async def test_a_message_posted_into_the_topic_matches(self, forum):
        env, chat, topics = forum
        support = chat.topic(topics[0].message_thread_id)

        async def announce():
            await asyncio.sleep(0.02)
            await env.bot.send_message(
                chat_id=chat.id,
                text="Night falls",
                message_thread_id=support.message_thread_id,
            )

        task = asyncio.create_task(announce())
        try:
            message = await support.wait_for_message(lambda item: item.text == "Night falls")
        finally:
            await task

        assert message.message_thread_id == support.message_thread_id

    async def test_a_message_in_a_sibling_topic_does_not_satisfy_the_wait(self, forum):
        env, chat, topics = forum
        support = chat.topic(topics[0].message_thread_id)
        random = chat.topic(topics[1].message_thread_id)
        await env.bot.send_message(
            chat_id=chat.id,
            text="elsewhere",
            message_thread_id=random.message_thread_id,
        )

        with pytest.raises(WaitTimeoutError) as exc_info:
            await support.wait_for_message(lambda item: item.text == "elsewhere", timeout=0.05)

        text = str(exc_info.value)
        assert f"topic #{support.message_thread_id} 'Support' of chat {chat.id}" in text
        # Only this topic's own messages are enumerated — the sibling's is not one of them.
        assert "The topic holds 1 message(s)" in text
        assert "elsewhere" not in text

    async def test_the_general_topic_names_itself(self, forum):
        env, chat, _topics = forum

        with pytest.raises(WaitTimeoutError) as exc_info:
            await chat.general_topic.wait_for_message(timeout=0.05)

        text = str(exc_info.value)
        assert f"the General topic of chat {chat.id}" in text
        assert "The topic holds no messages" in text

    async def test_a_hand_built_topic_still_names_itself(self):
        assert TopicState(message_thread_id=7, name="Loose").label == "topic #7 'Loose'"

    async def test_the_message_it_returns_is_usable(self, forum):
        env, chat, topics = forum
        support = chat.topic(topics[0].message_thread_id)
        await env.bot.send_message(
            chat_id=chat.id,
            text="ping",
            message_thread_id=support.message_thread_id,
        )

        message = await support.wait_for_message(lambda item: item.text == "ping")
        await message.answer("pong")

        assert [item.text for item in support.messages][-1] == "pong"

    async def test_a_raising_predicate_is_reported_for_a_topic_too(self, forum):
        env, chat, topics = forum
        support = chat.topic(topics[0].message_thread_id)

        with pytest.raises(WaitTimeoutError) as exc_info:
            await support.wait_for_message(lambda item: item.text.startswith("x"), timeout=0.05)

        assert "The predicate raised on 1 of them" in str(exc_info.value)

    def test_describe_messages_names_the_topic(self, forum):
        _env, chat, topics = forum
        support = chat.topic(topics[0].message_thread_id)

        assert support.describe_messages().startswith("The topic holds 1 message(s)")
