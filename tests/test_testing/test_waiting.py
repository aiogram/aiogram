import asyncio

import pytest

from aiogram.test import (
    Blueprint,
    BotTestEnvironment,
    ChatState,
    TopicState,
    WaitTimeoutError,
    WorldLookupError,
)
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

    async def test_the_newest_is_by_id_and_not_by_position(self, env, private):
        """
        Regression: "the newest one" was implemented as "the last one in the list".

        The docstring promises the newest match, and a test asking for the bot's latest
        reply is relying on that word. Reading the last element instead made the promise
        depend on the list happening to be sorted — and got an id-50 message out of a chat
        whose newest was 101 the one time it was not.
        """
        await env.bot.send_message(chat_id=private.id, text="tick 1")
        await env.bot.send_message(chat_id=private.id, text="tick 2")
        private.messages.reverse()

        message = await private.wait_for_message(lambda item: item.text.startswith("tick"))

        assert message.text == "tick 2"
        assert await private.wait_for_message() is message

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


class TestDescriptionIsPositional:
    """
    ``description`` is what the failure message can say about a lambda, so it comes second.

    Keyword-only, it was the parameter everybody needed and nobody passed. Positional it
    stays backward compatible — ``description=`` still works — while costing nothing to
    write.
    """

    async def test_wait_for_takes_it_positionally(self, env):
        with pytest.raises(WaitTimeoutError) as exc_info:
            await env.wait_for(lambda: False, "the night phase", timeout=0.05)

        assert "waiting for the night phase" in str(exc_info.value)

    async def test_wait_for_still_takes_it_as_a_keyword(self, env):
        with pytest.raises(WaitTimeoutError) as exc_info:
            await env.wait_for(lambda: False, timeout=0.05, description="the night phase")

        assert "waiting for the night phase" in str(exc_info.value)

    async def test_wait_for_message_takes_it_positionally(self, env, private):
        with pytest.raises(WaitTimeoutError) as exc_info:
            await private.wait_for_message(
                lambda item: False,
                "the dawn announcement",
                timeout=0.05,
            )

        assert "waiting for the dawn announcement" in str(exc_info.value)

    async def test_a_topic_wait_describes_itself_too(self, env, team):
        topic = await env.bot.create_forum_topic(chat_id=team.id, name="Support")
        support = env.chat(team.id).topic(topic.message_thread_id)

        with pytest.raises(WaitTimeoutError) as exc_info:
            await support.wait_for_message(lambda item: False, "the ticket reply", timeout=0.05)

        assert "waiting for the ticket reply" in str(exc_info.value)


class TestDefaultWaitTimeout:
    """
    One setting for every wait in an environment, overridable per call.

    A bot with slow background work would otherwise repeat ``timeout=`` on every wait in
    its suite, and a suite that wants fast failures would repeat a small one — while the
    chat-scoped waits, which are the ones tests actually use, had no way to be told at all.
    """

    @pytest.fixture
    def quick(self, blueprint, dp):
        environment = BotTestEnvironment(
            blueprint=blueprint,
            dispatcher=dp,
            default_wait_timeout=0.05,
        )
        try:
            yield environment
        finally:
            environment.dispose_sync()

    async def test_wait_for_uses_it(self, quick):
        with pytest.raises(WaitTimeoutError) as exc_info:
            await quick.wait_for(lambda: False)

        assert "after 0.05s" in str(exc_info.value)

    async def test_a_chat_wait_reaches_it_through_the_world(self, quick, blueprint):
        chat = quick.chat(blueprint.chats[0].id)

        with pytest.raises(WaitTimeoutError) as exc_info:
            await chat.wait_for_message()

        assert "after 0.05s" in str(exc_info.value)
        assert chat.default_wait_timeout == 0.05

    async def test_a_topic_wait_reaches_it_through_the_chat(self, quick, blueprint):
        chat = quick.chat(blueprint.chats[1].id)

        with pytest.raises(WaitTimeoutError) as exc_info:
            await chat.general_topic.wait_for_message()

        assert "after 0.05s" in str(exc_info.value)

    async def test_an_explicit_timeout_still_wins(self, quick, blueprint):
        chat = quick.chat(blueprint.chats[0].id)

        with pytest.raises(WaitTimeoutError) as exc_info:
            await chat.wait_for_message(timeout=0.01)

        assert "after 0.01s" in str(exc_info.value)

    async def test_the_default_default_is_five_seconds(self, env, private):
        assert env.world.default_wait_timeout == 5.0
        assert private.default_wait_timeout == 5.0
        assert private.general_topic.default_wait_timeout == 5.0

    def test_a_chat_outside_any_world_falls_back(self):
        loose = ChatState(id=1)

        assert loose.default_wait_timeout == 5.0
        assert TopicState(message_thread_id=7).default_wait_timeout == 5.0


class TestWatchedChatsInATimeout:
    """
    ``wait_for(..., watch=...)`` — the answer is usually in what the bot said instead.

    A general ``wait_for`` polls a lambda over the bot's own state, so the failure it can
    write on its own is the description it was handed and nothing else. In practice the
    explanation is in the group's last few messages, which the test then has to go and
    print by hand.
    """

    @pytest.fixture
    def quick(self, blueprint, dp):
        environment = BotTestEnvironment(
            blueprint=blueprint,
            dispatcher=dp,
            default_wait_timeout=0.02,
        )
        try:
            yield environment
        finally:
            environment.dispose_sync()

    async def test_a_watched_chat_is_dumped(self, quick, blueprint):
        chat = quick.chat(blueprint.chats[0].id)
        await quick.bot.send_message(chat_id=chat.id, text="the real reason")

        with pytest.raises(WaitTimeoutError) as exc_info:
            await quick.wait_for(lambda: False, "night to fall", watch=chat)

        message = str(exc_info.value)
        assert "waiting for night to fall" in message
        assert f"In chat {chat.id}:" in message
        assert "the real reason" in message

    async def test_several_chats_are_dumped(self, quick, blueprint):
        first = quick.chat(blueprint.chats[0].id)
        second = quick.chat(blueprint.chats[1].id)
        await quick.bot.send_message(chat_id=first.id, text="in private")
        await quick.bot.send_message(chat_id=second.id, text="in the group")

        with pytest.raises(WaitTimeoutError) as exc_info:
            await quick.wait_for(lambda: False, "the phase", watch=[first, second])

        message = str(exc_info.value)
        assert "in private" in message
        assert "in the group" in message

    async def test_a_topic_can_be_watched(self, quick, blueprint):
        chat = quick.chat(blueprint.chats[1].id)
        await quick.bot.send_message(chat_id=chat.id, text="in the general topic")

        with pytest.raises(WaitTimeoutError) as exc_info:
            await quick.wait_for(lambda: False, "the phase", watch=chat.general_topic)

        message = str(exc_info.value)
        assert "In the General topic" in message
        assert "in the general topic" in message

    async def test_an_empty_watched_chat_says_so(self, quick, blueprint):
        chat = quick.chat(blueprint.chats[0].id)

        with pytest.raises(WaitTimeoutError, match="holds no messages"):
            await quick.wait_for(lambda: False, "anything", watch=chat)

    async def test_watching_costs_nothing_on_the_happy_path(self, quick, blueprint):
        chat = quick.chat(blueprint.chats[0].id)

        assert await quick.wait_for(lambda: "done", watch=chat) == "done"

    async def test_a_watch_free_wait_is_unchanged(self, quick):
        with pytest.raises(WaitTimeoutError) as exc_info:
            await quick.wait_for(lambda: False, "nothing in particular")

        assert str(exc_info.value).splitlines() == [
            "Timed out after 0.02s waiting for nothing in particular.",
        ]

    async def test_the_lambda_advice_survives_a_watch(self, quick, blueprint):
        """Without a description the message still has to explain what it cannot show."""
        chat = quick.chat(blueprint.chats[0].id)

        with pytest.raises(WaitTimeoutError) as exc_info:
            await quick.wait_for(lambda: False, watch=chat)

        assert "Pass `description='...'`" in str(exc_info.value)


class TestWaitForMessageInManyChats:
    """
    ``wait_for_message_in`` — one wait over N chats instead of N serial waits.

    Awaiting each chat in turn is both slower (the timeouts add up) and much worse at
    failing: the first chat that never got its message ends the wait, so a broadcast that
    reached nobody reads as one unlucky chat.
    """

    @pytest.fixture
    def party(self):
        blueprint = Blueprint()
        players = [blueprint.add_user(name) for name in ("Alice", "Bob", "Carol")]
        for player in players:
            blueprint.add_private_chat(player)
        return blueprint

    @pytest.fixture
    def table(self, party):
        environment = BotTestEnvironment(blueprint=party, default_wait_timeout=0.05)
        try:
            yield environment
        finally:
            environment.dispose_sync()

    async def deal(self, environment, chat_ids, delay=0.01, text="Night falls"):
        for chat_id in chat_ids:
            await asyncio.sleep(delay)
            await environment.bot.send_message(chat_id=chat_id, text=text)

    async def test_it_returns_a_message_per_chat_once_all_have_one(self, table, party):
        chat_ids = [user.id for user in party.users]
        task = asyncio.create_task(self.deal(table, chat_ids))

        try:
            found = await table.wait_for_message_in(chat_ids, lambda m: m.text == "Night falls")
        finally:
            await task

        assert sorted(found) == sorted(chat_ids)
        assert all(message.text == "Night falls" for message in found.values())

    async def test_it_accepts_states_specs_and_ids_mixed(self, table, party):
        alice, _, carol = party.users
        for user in party.users:
            await table.bot.send_message(chat_id=user.id, text="dealt")

        found = await table.wait_for_message_in([table.chat(alice.id), party.chats[1], carol.id])

        assert sorted(found) == sorted(user.id for user in party.users)

    async def test_the_newest_match_per_chat_wins(self, table, party):
        alice = party.users[0]
        await table.bot.send_message(chat_id=alice.id, text="first")
        await table.bot.send_message(chat_id=alice.id, text="second")

        found = await table.wait_for_message_in([alice.id])

        assert found[alice.id].text == "second"

    async def test_the_failure_names_only_the_chats_still_missing_one(self, table, party):
        alice, bob, carol = party.users
        await table.bot.send_message(chat_id=alice.id, text="Night falls")
        await table.bot.send_message(chat_id=bob.id, text="something else")

        with pytest.raises(WaitTimeoutError) as exc_info:
            await table.wait_for_message_in(
                [alice.id, bob.id, carol.id],
                lambda m: m.text == "Night falls",
                "the night keyboard",
            )

        message = str(exc_info.value)
        assert "waiting for the night keyboard in all 3 watched chat(s)" in message
        assert f"Still missing in chat {bob.id}, chat {carol.id}" in message
        assert "something else" in message
        # The chat that *did* get it is not dumped; that is the whole point.
        assert f"In chat {alice.id}" not in message

    async def test_without_a_description_it_names_the_predicate(self, table, party):
        with pytest.raises(WaitTimeoutError, match="a message matching"):
            await table.wait_for_message_in([party.users[0].id], _is_a_keyboard)

    async def test_without_a_predicate_it_waits_for_any_message(self, table, party):
        with pytest.raises(WaitTimeoutError, match="waiting for any message"):
            await table.wait_for_message_in([party.users[0].id])

    async def test_a_predicate_that_raises_counts_as_no_match(self, table, party):
        """A chat holds messages of every shape; the single-chat wait has the same rule."""
        alice = party.users[0]
        await table.bot.send_message(chat_id=alice.id, text="plain")

        with pytest.raises(WaitTimeoutError):
            await table.wait_for_message_in([alice.id], lambda m: m.caption.startswith("x"))

    async def test_an_explicit_timeout_wins_over_the_environments(self, table, party):
        with pytest.raises(WaitTimeoutError, match="after 0.01s"):
            await table.wait_for_message_in([party.users[0].id], timeout=0.01)


def _is_a_keyboard(message):
    return message.reply_markup is not None


class TestTheWaitFamilySpeaksOneVocabulary:
    """
    ``watch=`` and ``chats=`` took different things, and neither took a declaration.

    A test holds the ``ChatSpec`` its ``add_supergroup`` returned — that *is* the handle the
    blueprint gives back — and passing it to ``watch=`` survived registration and then blew
    up with an ``AttributeError`` from inside the failure message it was assembling, which
    replaced the real diagnosis with a traceback about ``label``. One resolver now backs
    both, so the family accepts declarations, live states, topics and bare ids alike.
    """

    @pytest.fixture
    def quick(self, blueprint, dp):
        environment = BotTestEnvironment(
            blueprint=blueprint,
            dispatcher=dp,
            default_wait_timeout=0.02,
        )
        try:
            yield environment
        finally:
            environment.dispose_sync()

    async def test_watch_accepts_a_chat_declaration(self, quick, blueprint):
        group = blueprint.chats[1]
        await quick.bot.send_message(chat_id=group.id, text="the real reason")

        with pytest.raises(WaitTimeoutError) as exc_info:
            await quick.wait_for(lambda: False, "the phase", watch=group)

        message = str(exc_info.value)
        assert f"In chat {group.id}:" in message
        assert "the real reason" in message

    async def test_watch_accepts_a_bare_chat_id(self, quick, blueprint):
        group = blueprint.chats[1]
        await quick.bot.send_message(chat_id=group.id, text="the real reason")

        with pytest.raises(WaitTimeoutError, match="the real reason"):
            await quick.wait_for(lambda: False, "the phase", watch=group.id)

    async def test_watch_accepts_a_topic_declaration(self, quick, blueprint, dp):
        chat = quick.chat(blueprint.chats[1].id)
        created = await quick.bot.create_forum_topic(chat_id=chat.id, name="Support")
        topic = quick.topic(chat.id, created.message_thread_id)
        await quick.bot.send_message(
            chat_id=chat.id,
            message_thread_id=topic.message_thread_id,
            text="in the thread",
        )

        with pytest.raises(WaitTimeoutError) as exc_info:
            await quick.wait_for(lambda: False, "the phase", watch=topic)

        assert "in the thread" in str(exc_info.value)

    async def test_watch_accepts_a_topic_declaration_object(self, blueprint, dp):
        """
        A ``TopicSpec`` is what ``add_topic`` hands back, and it carries the chat it belongs
        to — so the resolver needs nothing else to turn it into the live topic.
        """
        topic_spec = blueprint.add_topic(blueprint.chats[1], "Support")
        environment = BotTestEnvironment(
            blueprint=blueprint,
            dispatcher=dp,
            default_wait_timeout=0.02,
        )
        try:
            live = environment.topic(topic_spec.chat_id, topic_spec)
            await environment.bot.send_message(
                chat_id=topic_spec.chat_id,
                message_thread_id=live.message_thread_id,
                text="in the declared thread",
            )

            with pytest.raises(WaitTimeoutError) as exc_info:
                await environment.wait_for(lambda: False, "the phase", watch=topic_spec)

            message = str(exc_info.value)
            assert "'Support'" in message
            assert "in the declared thread" in message
        finally:
            environment.dispose_sync()

    async def test_watch_accepts_a_mixed_iterable(self, quick, blueprint):
        private, group = blueprint.chats[0], blueprint.chats[1]
        await quick.bot.send_message(chat_id=private.id, text="in private")
        await quick.bot.send_message(chat_id=group.id, text="in the group")

        with pytest.raises(WaitTimeoutError) as exc_info:
            await quick.wait_for(
                lambda: False,
                "the phase",
                watch=[private, quick.chat(group.id)],
            )

        message = str(exc_info.value)
        assert "in private" in message
        assert "in the group" in message

    async def test_wait_for_message_in_accepts_a_single_chat_state(self, quick, blueprint):
        chat = quick.chat(blueprint.chats[0].id)
        await quick.bot.send_message(chat_id=chat.id, text="hello")

        found = await quick.wait_for_message_in(chat)

        assert found[chat.id].text == "hello"

    async def test_wait_for_message_in_accepts_a_single_declaration(self, quick, blueprint):
        group = blueprint.chats[1]
        await quick.bot.send_message(chat_id=group.id, text="hello")

        found = await quick.wait_for_message_in(group)

        assert found[group.id].text == "hello"

    async def test_wait_for_message_in_accepts_a_single_bare_id(self, quick, blueprint):
        group = blueprint.chats[1]
        await quick.bot.send_message(chat_id=group.id, text="hello")

        found = await quick.wait_for_message_in(group.id)

        assert found[group.id].text == "hello"

    async def test_wait_for_message_in_accepts_a_topic(self, quick, blueprint):
        chat = quick.chat(blueprint.chats[1].id)
        created = await quick.bot.create_forum_topic(chat_id=chat.id, name="Support")
        topic = quick.topic(chat.id, created.message_thread_id)
        await quick.bot.send_message(
            chat_id=chat.id,
            message_thread_id=topic.message_thread_id,
            text="in the thread",
        )

        found = await quick.wait_for_message_in([topic], lambda m: m.text == "in the thread")

        assert found[chat.id].text == "in the thread"

    async def test_two_views_of_one_chat_are_refused_rather_than_collapsed(
        self,
        quick,
        blueprint,
    ):
        """
        The result is ``chat_id -> message``, so two views of one chat would silently drop
        an entry and a test asserting on the count would fail on an answer never given.
        """
        chat = quick.chat(blueprint.chats[1].id)

        with pytest.raises(WorldLookupError, match="cannot hold them both"):
            await quick.wait_for_message_in([chat, chat.general_topic])

    async def test_as_views_of_nothing_is_empty(self, quick):
        assert quick.as_views(None) == ()


class TestBroadcastTimeoutReportsARaisingPredicate:
    """
    Parity with the single-chat wait, which its own docstring already promised.

    ``wait_for_message_in`` dropped the exceptions its predicate raised on the floor, so a
    predicate that was simply buggy — ``m.text.startswith(...)`` meeting the
    ``forum_topic_created`` service message — read as "the bot never sent it". That is the
    wrong bug, and much harder to find across ten chats than across one.
    """

    @pytest.fixture
    def quick(self, blueprint, dp):
        environment = BotTestEnvironment(
            blueprint=blueprint,
            dispatcher=dp,
            default_wait_timeout=0.02,
        )
        try:
            yield environment
        finally:
            environment.dispose_sync()

    async def test_what_the_predicate_raised_is_reported(self, quick, blueprint):
        private, group = blueprint.chats[0], blueprint.chats[1]
        await quick.bot.send_message(chat_id=private.id, text="text")
        await quick.bot.send_photo(chat_id=group.id, photo="file-id")

        with pytest.raises(WaitTimeoutError) as exc_info:
            await quick.wait_for_message_in(
                [private, group],
                lambda m: m.text.startswith("Night"),
                "the night keyboard",
            )

        message = str(exc_info.value)
        assert "The predicate raised on 1 message(s)" in message
        assert "AttributeError" in message
        assert f"chat {group.id}" in message

    async def test_a_predicate_that_raises_everywhere_still_counts_as_no_match(
        self,
        quick,
        blueprint,
    ):
        """The rule the single-chat wait states: raising is "no match", not a failed wait."""
        group = blueprint.chats[1]
        await quick.bot.send_photo(chat_id=group.id, photo="file-id")

        with pytest.raises(WaitTimeoutError) as exc_info:
            await quick.wait_for_message_in([group], lambda m: m.text.startswith("Night"))

        assert "Still missing in" in str(exc_info.value)

    async def test_nothing_is_reported_when_the_predicate_never_raises(self, quick, blueprint):
        group = blueprint.chats[1]

        with pytest.raises(WaitTimeoutError) as exc_info:
            await quick.wait_for_message_in([group], lambda m: m.text == "Night")

        assert "The predicate raised" not in str(exc_info.value)


class TestThePlayersListIsTheVocabularyToo:
    """
    A user stands for their private chat with the bot, everywhere a chat may be named.

    The broadcast this whole family exists for is "every player got the night keyboard",
    and what a test holds for a player is the ``UserSpec`` its ``add_user`` returned — the
    example in ``wait_for_message_in``'s own docstring is literally
    ``wait_for_message_in(players, ...)``. Passing that list raised ``WorldLookupError``
    from inside the resolver, so the documented example did not run.
    """

    @pytest.fixture
    def party(self):
        blueprint = Blueprint()
        for name in ("Alice", "Bob", "Carol"):
            blueprint.add_user(name)
        return blueprint

    @pytest.fixture
    def table(self, party):
        environment = BotTestEnvironment(blueprint=party, default_wait_timeout=0.05)
        try:
            yield environment
        finally:
            environment.dispose_sync()

    async def deal(self, environment, chat_ids):
        for chat_id in chat_ids:
            await asyncio.sleep(0.005)
            await environment.bot.send_message(chat_id=chat_id, text="Night falls")

    async def test_the_documented_players_example_runs(self, table, party):
        """
        And note the blueprint declares no private chats: a user's private chat is opened
        on demand, the same rule ``env.user(alice).chat`` follows.
        """
        players = party.users
        task = asyncio.create_task(self.deal(table, [player.id for player in players]))

        try:
            keyboards = await table.wait_for_message_in(
                players,
                lambda m: m.text == "Night falls",
                "the night keyboard",
            )
        finally:
            await task

        assert set(keyboards) == {player.id for player in players}

    async def test_watch_accepts_a_user_declaration(self, table, party):
        alice = party.users[0]
        await table.user(alice).send("hello?")  # a bot may only answer, never write first
        await table.bot.send_message(chat_id=alice.id, text="the real reason")

        with pytest.raises(WaitTimeoutError) as failure:
            await table.wait_for(lambda: False, "the phase", watch=alice, timeout=0.01)

        assert f"In chat {alice.id}" in str(failure.value)
        assert "the real reason" in str(failure.value)

    async def test_watch_accepts_a_live_user_state(self, table, party):
        alice = table.world.user(party.users[0].id)
        await table.user(party.users[0]).send("hello?")
        await table.bot.send_message(chat_id=alice.id, text="the real reason")

        with pytest.raises(WaitTimeoutError) as failure:
            await table.wait_for(lambda: False, "the phase", watch=[alice], timeout=0.01)

        assert f"In chat {alice.id}" in str(failure.value)

    async def test_a_user_mixes_freely_with_the_rest_of_the_vocabulary(self, table, party):
        alice, bob = party.users[0], table.world.user(party.users[1].id)
        views = table.as_views([alice, bob, party.users[2].id])

        assert [view.id for view in views] == [alice.id, bob.id, party.users[2].id]
