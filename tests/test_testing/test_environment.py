import asyncio

import pytest

from aiogram import Dispatcher, F
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.methods import SendMessage
from aiogram.test import (
    BASE_DATE,
    Blueprint,
    BotTestEnvironment,
    WaitTimeoutError,
    build_environment,
)
from aiogram.test.world import WorldLookupError
from aiogram.types import (
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
    User,
)


class Form(StatesGroup):
    name = State()


class TestAccessors:
    def test_chat_and_user_accept_specs_and_ids(self, env, blueprint):
        chat_spec = blueprint.chats[0]
        user_spec = blueprint.users[0]

        assert env.chat(chat_spec).id == chat_spec.id
        assert env.chat(chat_spec.id).id == chat_spec.id
        assert env.user(user_spec).user.id == user_spec.id
        assert env.user(user_spec.id).user.id == user_spec.id

    def test_defaults_are_used_when_nothing_is_supplied(self):
        environment = build_environment()
        try:
            assert environment.blueprint.users
            assert environment.dispatcher is not None
        finally:
            environment.dispose_sync()

    def test_actor_binding_is_not_shared(self, env, blueprint, team):
        actor = env.user(blueprint.users[0])

        bound = actor.in_(team)

        assert bound.chat.id == team.id
        assert actor.chat.id == blueprint.chats[0].id

    def test_actor_accepts_state_spec_and_id(self, env, blueprint, team):
        actor = env.user(blueprint.users[0])

        assert actor.in_(team).chat.id == team.id
        assert actor.in_(blueprint.chats[1]).chat.id == team.id
        assert actor.in_(team.id).chat.id == team.id

    def test_actor_without_a_private_chat_gets_one_opened(self):
        """
        An unbound actor names no chat, but `.chat` opens its own private chat rather
        than refusing — the same auto-creation a followed deep link relies on, see
        `World.ensure_private_chat`.
        """
        blueprint = Blueprint()
        lonely = blueprint.add_user("Lonely")
        environment = BotTestEnvironment(blueprint=blueprint)
        try:
            chat = environment.user(lonely).chat

            assert chat.id == lonely.id
            assert chat.type == ChatType.PRIVATE
            assert environment.world.chats[lonely.id] is chat
        finally:
            environment.dispose_sync()

    def test_env_chat_opens_a_declared_users_private_chat_too(self):
        """
        Regression: ``env.chat(user_id)`` raised while ``env.user(user_id).chat`` opened
        the very same chat, so a chat was reachable through one accessor and not the
        other. The asymmetry was the bug.
        """
        blueprint = Blueprint()
        lonely = blueprint.add_user("Lonely")
        environment = BotTestEnvironment(blueprint=blueprint)
        try:
            chat = environment.chat(lonely.id)

            assert chat.type == ChatType.PRIVATE
            assert chat is environment.user(lonely).chat
            assert environment.world.chats[lonely.id] is chat
        finally:
            environment.dispose_sync()

    def test_env_chat_resolves_the_same_chat_twice(self):
        blueprint = Blueprint()
        lonely = blueprint.add_user("Lonely")
        environment = BotTestEnvironment(blueprint=blueprint)
        try:
            assert environment.chat(lonely.id) is environment.chat(lonely.id)
        finally:
            environment.dispose_sync()

    def test_env_chat_still_refuses_an_id_that_is_nobody(self, env):
        """A group the blueprint never declared is a typo, not a chat the bot can open."""
        with pytest.raises(WorldLookupError, match="Chat -999 is not declared"):
            env.chat(-999)

    def test_env_chat_does_not_open_a_private_chat_with_the_bot_itself(self, env):
        with pytest.raises(WorldLookupError, match="not declared"):
            env.chat(env.world.bot_user.id)


class TestTriggers:
    async def test_send_reaches_the_handler(self, env, dp, alice):
        @dp.message(Command("start"))
        async def handler(message):
            return "handled"

        assert await alice.send("/start") == "handled"

    async def test_message_is_stored_in_the_chat(self, env, dp, alice, private):
        @dp.message()
        async def handler(message):
            return None

        await alice.send("hello")

        assert private.messages[-1].text == "hello"
        assert private.messages[-1].from_user.id == alice.user.id

    async def test_a_fed_update_arrives_mounted_and_uncopied(self, env, dp, private):
        """
        ``feed`` mounts the update before the dispatcher sees it, and that is why a
        handler works on the world's own objects: an update carrying a different bot is
        re-mounted by round-tripping it through JSON, which replaces everything in it with
        a copy.
        """
        seen = {}

        @dp.message()
        async def handler(message):
            seen["message"] = message

        stored = await env.bot.send_message(chat_id=private.id, text="hi")
        await env.feed(Update(update_id=99, message=stored))

        assert seen["message"] is stored
        assert seen["message"].bot is env.bot

    async def test_an_update_from_another_environment_is_copied_first(self, blueprint):
        """
        Two environments, one module-level update: the second must not answer into the
        first one's world.

        ``mount`` stops at anything already bound, so the update kept its first
        environment's bot — and since two bots built from one blueprint compare equal,
        every reply the second one's handlers sent landed in the first one's world and its
        call log, with nothing to show that it had. The fix is a copy, and the tell that it
        happened is that the update the second environment fed is not the one it was given.
        """
        seen = []

        def environment():
            dispatcher = Dispatcher()

            @dispatcher.message()
            async def handler(message):
                seen.append(message.bot)
                await message.answer("pong")

            return BotTestEnvironment(blueprint=blueprint, dispatcher=dispatcher)

        chat_id = blueprint.chats[0].id
        shared = Update(
            update_id=7,
            message=Message(
                message_id=1,
                date=BASE_DATE,
                chat=Chat(id=chat_id, type=ChatType.PRIVATE),
                from_user=User(id=blueprint.users[0].id, is_bot=False, first_name="Alice"),
                text="ping",
            ),
        )

        first, second = environment(), environment()
        try:
            await first.feed(shared)
            await second.feed(shared)

            assert seen == [first.bot, second.bot]
            assert first.calls.count(SendMessage) == 1
            assert second.calls.count(SendMessage) == 1
            assert [item.text for item in first.chat(chat_id).messages] == ["ping", "pong"]
            assert [item.text for item in second.chat(chat_id).messages] == ["ping", "pong"]
        finally:
            first.dispose_sync()
            second.dispose_sync()

    async def test_a_carried_message_does_not_collide_with_the_reply(self, blueprint, dp):
        """
        Regression: the copied message was never registered, so its id was handed out twice.

        The chat's allocator knew nothing about the message the update carried, so the
        bot's first reply was minted with the *same* ``message_id`` — and the next edit,
        which finds a message by id, landed on whichever of the two came first.
        """

        @dp.message()
        async def handler(message):
            reply = await message.answer("pong")
            await reply.edit_text("edited")

        chat_id = blueprint.chats[0].id
        foreign = BotTestEnvironment(blueprint=blueprint, dispatcher=Dispatcher())
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            await foreign.user(blueprint.users[0].id).in_(chat_id).send("ping")
            carried = foreign.chat(chat_id).messages[-1]

            await env.feed(Update(update_id=1, message=carried))

            texts = [item.text for item in env.chat(chat_id).messages]
            assert texts == ["ping", "edited"]
            ids = [item.message_id for item in env.chat(chat_id).messages]
            assert len(set(ids)) == len(ids)
            assert ids[1] > carried.message_id
        finally:
            env.dispose_sync()
            foreign.dispose_sync()

    async def test_a_carried_message_lands_in_message_id_order(self, blueprint, dp):
        """
        Regression: a carried message was appended, so an older id landed last.

        The two environments allocate ids independently, so the one that arrives from
        outside can be *older* than everything this chat already holds. Appending it left
        ``chat.messages`` unsorted, and ``chat.messages[-1]`` — which every test writes to
        mean "the newest message" — pointed at the oldest one instead.
        """
        chat_id = blueprint.chats[0].id
        foreign = BotTestEnvironment(blueprint=blueprint, dispatcher=Dispatcher())
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            speaker = foreign.user(blueprint.users[0].id).in_(chat_id)
            for index in range(4):
                await speaker.send(f"far away {index}")
            older, newer = foreign.chat(chat_id).messages[1], foreign.chat(chat_id).messages[-1]
            assert older.message_id < newer.message_id

            # Out of order, which is all it takes: the second one is older than the chat's
            # newest, and its id was never allocated here.
            await env.feed(Update(update_id=1, message=newer))
            await env.feed(Update(update_id=2, message=older))

            chat = env.chat(chat_id)
            ids = [item.message_id for item in chat.messages]
            assert ids == sorted(ids)
            assert chat.messages[-1].message_id == newer.message_id
            assert chat.messages[0].message_id == older.message_id
        finally:
            env.dispose_sync()
            foreign.dispose_sync()

    async def test_a_carried_channel_post_is_registered_too(self, blueprint, dp):
        """The rule is about the message, not about which field carried it."""
        channel = blueprint.add_channel("News")
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            post = Message(
                message_id=17,
                date=BASE_DATE,
                chat=Chat(id=channel.id, type=ChatType.CHANNEL),
                text="headline",
            )

            await env.feed(Update(update_id=1, channel_post=post))

            assert env.chat(channel.id).messages == [post]
            assert env.chat(channel.id).last_message_id == 17
        finally:
            env.dispose_sync()

    async def test_a_carried_message_id_collision_is_loud(self, blueprint, dp):
        """
        Design decision: an id already taken by a *different* message must not be silently
        dropped — the handler would go on to work on a message the world never stores, and a
        `wait_for_message` waiting for it would hang forever with no clue why.
        """
        first_foreign = BotTestEnvironment(blueprint=blueprint, dispatcher=Dispatcher())
        second_foreign = BotTestEnvironment(blueprint=blueprint, dispatcher=Dispatcher())
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            chat_id = blueprint.chats[0].id
            await first_foreign.user(blueprint.users[0].id).in_(chat_id).send("hello")
            await second_foreign.user(blueprint.users[0].id).in_(chat_id).send("world")
            one = first_foreign.chat(chat_id).messages[-1]
            two = second_foreign.chat(chat_id).messages[-1]
            # Both environments allocate ids independently, starting from the same blank
            # chat, so the first message either one sends collides by construction.
            assert one.message_id == two.message_id

            await env.feed(Update(update_id=1, message=one))

            with pytest.raises(WorldLookupError, match="already holds a different message"):
                await env.feed(Update(update_id=2, message=two))
        finally:
            env.dispose_sync()
            first_foreign.dispose_sync()
            second_foreign.dispose_sync()

    async def test_a_carried_message_re_fed_with_equal_content_is_a_no_op(self, blueprint, dp):
        """The collision guard must not fire on the same message arriving a second time."""
        foreign = BotTestEnvironment(blueprint=blueprint, dispatcher=Dispatcher())
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            chat_id = blueprint.chats[0].id
            await foreign.user(blueprint.users[0].id).in_(chat_id).send("ping")
            carried = foreign.chat(chat_id).messages[-1]

            await env.feed(Update(update_id=1, message=carried))
            # Fed again, wrapped in a fresh `Update` — each `feed` mints its own detached
            # copy of `carried` since it still belongs to `foreign`'s bot, so this is two
            # structurally equal but distinct objects sharing one id, not the exact same one.
            await env.feed(Update(update_id=2, message=carried))

            assert len(env.chat(chat_id).messages) == 1
        finally:
            env.dispose_sync()
            foreign.dispose_sync()

    async def test_a_message_for_an_undeclared_chat_is_left_alone(self, env, dp):
        """There is no chat here to keep it in, and inventing one would hide the mistake."""
        stray = Message(
            message_id=3,
            date=BASE_DATE,
            chat=Chat(id=-999999, type=ChatType.SUPERGROUP),
            text="elsewhere",
        )

        await env.feed(Update(update_id=1, message=stray))

        assert -999999 not in env.world.chats

    async def test_an_actor_built_update_is_fed_without_a_copy(self, env, dp, alice, private):
        """
        The other side of the same rule: an update this environment already owns keeps its
        identity, however many times it is fed, so a handler still works on the world's own
        objects.
        """
        seen = []

        @dp.message()
        async def handler(message):
            seen.append(message)

        stored = await env.bot.send_message(chat_id=private.id, text="hi")
        update = Update(update_id=99, message=stored)
        await env.feed(update)
        await env.feed(update)

        assert seen == [stored, stored]
        assert all(item is stored for item in seen)

    async def test_filters_are_not_bypassed(self, env, dp, alice):
        @dp.message(F.text == "expected")
        async def handler(message):
            return "handled"

        assert await alice.send("something else") is UNHANDLED

    async def test_middleware_runs(self, env, dp, alice):
        seen = []

        @dp.message.outer_middleware()
        async def middleware(handler, event, data):
            seen.append(event.text)
            data["injected"] = "from middleware"
            return await handler(event, data)

        @dp.message()
        async def handler(message, injected: str):
            return injected

        assert await alice.send("hi") == "from middleware"
        assert seen == ["hi"]

    async def test_dependencies_are_injected(self, env, dp, alice):
        @dp.message()
        async def handler(message, repository):
            return repository.upper()

        assert await alice.send("hi", repository="value") == "VALUE"

    async def test_event_context_is_resolved(self, env, dp, alice, private):
        @dp.message()
        async def handler(message, event_from_user, event_chat):
            return event_from_user.id, event_chat.id

        assert await alice.send("hi") == (alice.user.id, private.id)

    async def test_edit_triggers_edited_message(self, env, dp, alice, private):
        @dp.edited_message()
        async def handler(message, event_from_user):
            return "edited"

        await alice.send("before", fields={})
        original = private.messages[-1]

        assert await alice.edit(original, "after") == "edited"
        assert private.messages[-1].text == "after"

    async def test_send_with_raw_fields(self, env, dp, alice, private):
        @dp.message()
        async def handler(message):
            return None

        await alice.send("hi", fields={"message_thread_id": 7})

        assert private.messages[-1].message_thread_id == 7

    async def test_inline_query(self, env, dp, alice):
        @dp.inline_query()
        async def handler(query):
            return query.query

        assert await alice.inline_query("search") == "search"

    async def test_join_and_leave(self, env, dp, blueprint, team):
        transitions = []

        @dp.chat_member()
        async def handler(event):
            transitions.append(
                (event.old_chat_member.status, event.new_chat_member.status),
            )
            return "seen"

        bob = env.user(blueprint.users[0]).in_(team)

        assert await bob.leave() == "seen"
        assert team.member(bob.user.id).status == ChatMemberStatus.LEFT

        assert await bob.join() == "seen"
        assert team.member(bob.user.id).status == ChatMemberStatus.MEMBER
        assert transitions[-1] == (ChatMemberStatus.LEFT, ChatMemberStatus.MEMBER)


class TestClicking:
    @staticmethod
    def keyboard(data: str = "go") -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data=data)]],
        )

    async def test_click_resolves_the_real_button(self, env, dp, alice, private):
        @dp.message()
        async def start(message):
            await message.answer("pick", reply_markup=TestClicking.keyboard())

        @dp.callback_query(F.data == "go")
        async def clicked(query):
            return query.message.text

        await alice.send("/start")

        assert await alice.click("go") == "pick"

    async def test_click_accepts_a_button_object(self, env, dp, alice, private):
        button = InlineKeyboardButton(text="Go", callback_data="go")

        @dp.message()
        async def start(message):
            await message.answer(
                "pick",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[button]]),
            )

        @dp.callback_query()
        async def clicked(query):
            return query.data

        await alice.send("/start")

        assert await alice.click(button) == "go"

    async def test_click_with_an_explicit_message(self, env, dp, alice, private):
        @dp.callback_query()
        async def clicked(query):
            return query.message.message_id

        await alice.send("hi")
        message = private.messages[-1]

        assert await alice.click("anything", message=message) == message.message_id

    async def test_click_skips_messages_without_a_keyboard(self, env, dp, alice, private):
        @dp.message()
        async def start(message):
            if message.text == "/start":
                await message.answer("pick", reply_markup=TestClicking.keyboard())

        @dp.callback_query()
        async def clicked(query):
            return query.message.text

        await alice.send("/start")
        await alice.send("chatter")  # newer message, no keyboard

        assert await alice.click("go") == "pick"

    async def test_click_on_a_button_that_was_never_sent(self, env, alice):
        with pytest.raises(WorldLookupError, match="carries a button"):
            await alice.click("missing")

    async def test_click_on_a_button_without_callback_data(self, env, alice):
        button = InlineKeyboardButton(text="Open", url="https://example.com")

        with pytest.raises(WorldLookupError, match="no callback_data"):
            await alice.click(button)


class TestFsmAccess:
    async def test_state_can_be_read_after_a_flow(self, env, dp, alice, blueprint):
        @dp.message()
        async def handler(message, state):
            await state.set_state(Form.name)
            await state.update_data(step=1)

        await alice.send("hi")

        context = env.state(blueprint.users[0], blueprint.chats[0])
        assert await context.get_state() == Form.name.state
        assert await context.get_data() == {"step": 1}

    async def test_state_can_be_arranged_up_front(self, env, dp, alice, blueprint):
        @dp.message(Form.name)
        async def handler(message, state):
            data = await state.get_data()
            return data["prefilled"]

        context = env.state(blueprint.users[0])
        await context.set_state(Form.name)
        await context.update_data(prefilled="yes")

        assert await alice.send("hi") == "yes"

    async def test_state_defaults_to_the_private_chat(self, env, blueprint):
        context = env.state(blueprint.users[0])

        assert context.key.chat_id == blueprint.users[0].id


class TestDrain:
    """
    ``await env.drain()`` — the opt-in cleanup for a bot that spawns its own tasks.

    An engine that does ``asyncio.create_task(self._night_timer())`` leaves the task
    sleeping when the test ends, and the loop is torn down under it: every one of them
    prints ``Task was destroyed but it is pending!`` to stderr, after the test that caused
    it has already passed and long after anyone could trace it back.
    """

    async def test_a_leaked_sleeping_task_is_cancelled_and_awaited(self, env):
        started = asyncio.Event()

        async def forever():
            started.set()
            await asyncio.sleep(3600)

        task = asyncio.create_task(forever())
        await started.wait()

        assert await env.drain() == 1

        assert task.cancelled()

    async def test_it_reports_how_many_it_drained(self, env):
        tasks = [asyncio.create_task(asyncio.sleep(3600)) for _ in range(3)]
        await asyncio.sleep(0)

        assert await env.drain() == 3
        assert all(task.done() for task in tasks)

    async def test_nothing_to_drain_is_free(self, env):
        assert await env.drain() == 0

    async def test_a_task_that_finished_on_its_own_is_not_counted(self, env):
        task = asyncio.create_task(asyncio.sleep(0))
        await task

        assert await env.drain() == 0

    async def test_a_task_that_fails_while_being_cancelled_is_collected_quietly(self, env):
        """
        Its exception is retrieved rather than left for the garbage collector to complain
        about at some later, unrelated moment — which would be the very stderr noise this
        exists to remove.
        """
        started = asyncio.Event()

        async def explode_on_cancel():
            started.set()
            try:
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                msg = "cleanup failed"
                raise ValueError(msg) from None

        task = asyncio.create_task(explode_on_cancel())
        await started.wait()

        assert await env.drain() == 1

        assert not task.cancelled()
        assert isinstance(task.exception(), ValueError)

    async def test_a_task_that_already_finished_is_not_drained(self, env):
        task = asyncio.create_task(asyncio.sleep(0))
        await task

        assert await env.drain() == 0

    async def test_the_caller_is_never_cancelled(self, env):
        await env.drain()

        assert not asyncio.current_task().cancelled()

    async def test_a_task_that_outlives_its_cancellation_is_reported(self, env):
        """
        Exactly the "a `finally` that awaits" the failure message points at: the task
        accepts the cancellation but takes longer to unwind than the drain waits, so the
        drain must say so rather than leave it running and claim success.
        """
        started = asyncio.Event()

        async def slow_to_die():
            started.set()
            try:
                await asyncio.sleep(3600)
            finally:
                await asyncio.sleep(0.2)

        task = asyncio.create_task(slow_to_die())
        await started.wait()

        try:
            with pytest.raises(WaitTimeoutError, match="still running"):
                await env.drain(timeout=0.01)
        finally:
            await asyncio.wait([task], timeout=2.0)

    async def test_tasks_that_predate_the_environment_are_left_alone(self, blueprint, dp):
        """A session-scoped fixture's worker is not this test's litter."""
        started = asyncio.Event()

        async def worker():
            started.set()
            await asyncio.sleep(3600)

        outsider = asyncio.create_task(worker())
        await started.wait()

        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            mine = asyncio.create_task(asyncio.sleep(3600))
            await asyncio.sleep(0)

            assert await environment.drain() == 1

            assert mine.cancelled()
            assert not outsider.done()
        finally:
            await environment.dispose()
            outsider.cancel()

    async def test_dispose_does_not_drain(self, blueprint, dp):
        """
        Deliberately not automatic: ``dispose_sync`` cannot await anything at all, so an
        auto-drain would work in one teardown path and silently not in the other.
        """
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        task = asyncio.create_task(asyncio.sleep(3600))
        await asyncio.sleep(0)

        await environment.dispose()

        try:
            assert not task.done()
        finally:
            task.cancel()
