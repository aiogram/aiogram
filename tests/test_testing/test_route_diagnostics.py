"""
`env.last_route` — where the update actually went.

The reported pain: an update that dies in a middleware or lands in a catch-all handler
comes back from ``send()`` as somebody else's return value, and the test fails minutes
later as a ``wait_for`` timeout with nothing to say about why. These tests pin down what
the record knows and, just as importantly, that it survives a bot which swallows its own
exceptions.
"""

import asyncio

import pytest

from aiogram import F, BaseMiddleware, Router
from aiogram.filters import Command
from aiogram.test import BotTestEnvironment
from aiogram.types import CallbackQuery, Update


class TestLastRoute:
    async def test_a_handled_update_names_its_handler_and_router(self, env, dp, alice):
        greetings = Router(name="greetings")

        @greetings.message(Command("start"))
        async def on_start(message):
            return "ok"

        dp.include_router(greetings)

        await alice.send("/start")

        route = env.last_route
        assert route.handled is True
        assert (
            route.handler
            == "TestLastRoute.test_a_handled_update_names_its_handler_and_router.<locals>.on_start"
        )
        assert route.handler_module == __name__
        assert route.router == "greetings"
        assert route.event_type == "message"

    async def test_an_unhandled_update_says_so(self, env, dp, alice):
        @dp.message(Command("other"))
        async def never(message):  # pragma: no cover - the filter never passes
            return "ok"

        await alice.send("/start")

        route = env.last_route
        assert route.handled is False
        assert route.handler is None
        assert route.handler_path is None
        assert "NOT handled" in route.describe()

    async def test_a_catch_all_handler_is_named(self, env, dp, alice):
        """
        The exact confusion this exists for: the update *was* handled, just not by the
        handler the test is about, and the return value alone cannot tell them apart.
        """
        specific = Router(name="specific")
        fallback = Router(name="fallback")

        @specific.message(Command("start"))
        async def on_start(message):  # pragma: no cover - the wrong command is sent
            return "specific"

        @fallback.message()
        async def log_everything(message):
            return "logged"

        dp.include_router(specific)
        dp.include_router(fallback)

        assert await alice.send("/stat") == "logged"

        assert "log_everything" in env.last_route.handler
        assert env.last_route.router == "fallback"

    async def test_a_middleware_that_swallows_the_update_leaves_no_handler(self, env, dp, alice):
        """
        The reported case: the update dies in a middleware and ``send`` returns something
        anyway. ``handled`` follows aiogram's own definition — anything other than
        ``UNHANDLED`` came back, which a middleware returning ``None`` satisfies — so
        ``handler`` is the field that answers "did anything actually run".
        """

        class Gate(BaseMiddleware):
            async def __call__(self, handler, event, data):
                return None

        dp.message.outer_middleware(Gate())

        @dp.message()
        async def never(message):  # pragma: no cover - the middleware never calls it
            return "ok"

        await alice.send("hi")

        assert env.last_route.handler is None
        assert env.last_route.handled is True

    async def test_the_route_is_reset_between_updates(self, env, dp, alice):
        @dp.message(Command("start"))
        async def on_start(message):
            return "ok"

        await alice.send("/start")
        assert env.last_route.handled is True

        await alice.send("plain text")

        assert env.last_route.handled is False
        assert env.last_route.handler is None

    async def test_an_update_of_an_unknown_type_is_recorded_without_a_type(self, env):
        """
        A bare ``Update`` carries no event, so ``event_type`` raises rather than answering.
        Diagnostics must not be the thing that fails on it.
        """
        with pytest.warns(RuntimeWarning, match="unknown update type"):
            await env.feed(Update(update_id=777))

        assert env.last_route.update_id == 777
        assert env.last_route.event_type is None
        assert "unknown type" in env.last_route.describe()

    def test_no_update_yet_means_no_route(self, env):
        assert env.last_route is None


class TestCapturedExceptions:
    async def test_an_exception_raised_in_a_handler_is_captured(self, env, dp, alice):
        @dp.message()
        async def boom(message):
            msg = "handler exploded"
            raise ValueError(msg)

        with pytest.raises(ValueError, match="handler exploded"):
            await alice.send("hi")

        assert isinstance(env.last_route.exception, ValueError)
        assert "ValueError: handler exploded" in env.last_route.describe()

    async def test_an_exception_a_bots_error_handler_swallows_is_still_captured(
        self,
        env,
        dp,
        alice,
    ):
        """
        The case that made this worth building. aiogram's own `ErrorsMiddleware` sits
        outside anything the environment can install, so a bot with an error handler
        reports the update as *handled* and the test fails on the missing reply instead of
        on the traceback that explains it.
        """

        @dp.message()
        async def boom(message):
            msg = "swallowed"
            raise RuntimeError(msg)

        @dp.error()
        async def on_error(event):
            return "handled the error"

        assert await alice.send("hi") == "handled the error"

        # The value the test sees came from the error handler; the record says why.
        assert env.last_route.handled is False
        assert "boom" in env.last_route.handler
        assert isinstance(env.last_route.exception, RuntimeError)
        assert str(env.last_route.exception) == "swallowed"

    async def test_an_exception_raised_in_an_outer_middleware_is_captured(self, env, dp, alice):
        class Boom(BaseMiddleware):
            async def __call__(self, handler, event, data):
                msg = "middleware exploded"
                raise ValueError(msg)

        dp.message.outer_middleware(Boom())

        with pytest.raises(ValueError, match="middleware exploded"):
            await alice.send("hi")

        assert isinstance(env.last_route.exception, ValueError)


class TestAssertHandledBy:
    async def test_it_passes_on_a_substring_of_the_qualified_name(self, env, dp, alice):
        @dp.message(Command("start"))
        async def on_start(message):
            return "ok"

        await alice.send("/start")

        record = env.assert_handled_by("on_start")
        assert record is env.last_route
        env.assert_handled_by(f"{__name__}.TestAssertHandledBy")

    async def test_it_reports_where_the_update_actually_went(self, env, dp, alice):
        @dp.message()
        async def log_everything(message):
            return "logged"

        await alice.send("/start")

        with pytest.raises(AssertionError, match="log_everything") as failure:
            env.assert_handled_by("on_start")
        assert "Expected the last trigger to be handled by 'on_start'" in str(failure.value)

    async def test_it_reports_an_unhandled_update(self, env, dp, alice):
        await alice.send("hi")

        with pytest.raises(AssertionError, match="NOT handled"):
            env.assert_handled_by("on_start")

    def test_it_explains_that_nothing_was_recorded(self, env):
        with pytest.raises(AssertionError, match="no update has been routed"):
            env.assert_handled_by("on_start")


class TestInstrumentationIsUndone:
    def test_the_middlewares_are_removed_on_dispose(self, blueprint, dp):
        """
        A dispatcher may be shared across tests, so the recorder follows the same rule the
        FSM storage does: mutate, remember, undo.
        """
        before = (len(dp.update.outer_middleware), len(dp.message.middleware))

        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        assert len(dp.update.outer_middleware) == before[0] + 1
        assert len(dp.message.middleware) == before[1] + 1
        environment.dispose_sync()

        assert (len(dp.update.outer_middleware), len(dp.message.middleware)) == before

    async def test_two_environments_over_one_dispatcher_do_not_stack(self, blueprint, dp):
        first = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        await first.dispose()
        second = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:

            @dp.message()
            async def handler(message):
                return "ok"

            await second.user(blueprint.users[0]).in_(blueprint.chats[0]).send("hi")

            assert second.assert_handled_by("handler")
            assert first.last_route is None
        finally:
            await second.dispose()


class TestConcurrentFeedsDoNotCrossAttribute:
    """
    Two updates in flight at once used to swap handlers.

    The record in flight lived in a list on the environment and the inner middleware read
    its *top*, so a second feed starting while the first was suspended inside a middleware
    or an async filter put its own record on top — and the first update's handler name was
    then written onto the second update's record. Every diagnostic downstream was a lie,
    and only for the tests that use ``asyncio.gather``, which are exactly the tests of a bot
    that fans work out concurrently.

    A context variable is the fix rather than a lock: a task copies the context when it is
    created, so ``gather`` isolates the two by construction, while a nested feed runs in the
    same task and therefore still shadows and restores correctly.
    """

    async def test_each_record_names_its_own_handler(self, env, dp, blueprint):
        seen: dict[int, str] = {}

        class Yield(BaseMiddleware):
            """Suspends between opening the record and reaching the handler middleware."""

            async def __call__(self, handler, event, data):
                await asyncio.sleep(0)
                return await handler(event, data)

        dp.message.outer_middleware(Yield())

        @dp.message(Command("alpha"))
        async def on_alpha(message, event_update):
            await asyncio.sleep(0)
            seen[event_update.update_id] = "on_alpha"
            return "alpha"

        @dp.message(Command("beta"))
        async def on_beta(message, event_update):
            await asyncio.sleep(0)
            seen[event_update.update_id] = "on_beta"
            return "beta"

        alice = env.user(blueprint.users[0])
        group = env.chat(blueprint.chats[1].id)

        results = await asyncio.gather(
            alice.send("/alpha"),
            alice.in_(group).send("/beta"),
        )

        assert sorted(results) == ["alpha", "beta"]
        records = {record.update_id: record for record in env.routes}
        assert len(records) == 2
        assert set(records) == set(seen)
        for update_id, expected in seen.items():
            assert records[update_id].handler is not None
            assert expected in records[update_id].handler, (
                f"update {update_id} really ran {expected}, but its record says "
                f"{records[update_id].handler}"
            )

    async def test_a_nested_feed_still_shadows_and_restores(self, env, dp, blueprint):
        """
        The property the stack got right and a naive per-task flag would lose: a handler
        that feeds an update of its own must not have the inner update's handler written
        onto the outer record.
        """

        @dp.message(Command("outer"))
        async def on_outer(message):
            await env.feed(
                Update(
                    update_id=9001,
                    callback_query=CallbackQuery(
                        id="q-1",
                        from_user=message.from_user,
                        chat_instance="ci",
                        data="inner",
                    ),
                ),
            )
            return "outer"

        @dp.callback_query()
        async def on_inner(query):
            return "inner"

        await env.user(blueprint.users[0]).send("/outer")

        by_id = {record.update_id: record for record in env.routes}
        assert "on_inner" in by_id[9001].handler
        outer = next(record for record in env.routes if record.update_id != 9001)
        assert "on_outer" in outer.handler
        # Records complete innermost first, and `last_route` prefers the newest *handled*
        # one — which after a nested feed is the outer update, the one `feed` was called
        # with.
        assert env.last_route is outer


class TestTheErrorObserverIsNotRecorded:
    """
    An error handler is not where the update went — it is what ran after it failed to go
    anywhere. Recording it overwrote the very field the record exists to preserve.
    """

    async def test_a_nested_error_handler_does_not_rewrite_the_outer_record(
        self,
        env,
        dp,
        blueprint,
    ):
        """
        The repro. aiogram's `ErrorsMiddleware` sits outside the recorder, so for a plain
        feed the record has already closed by the time the error handler runs and there is
        nothing to corrupt. Nest one feed inside another and there is: the inner update's
        record closes, the outer one is in flight again, and the error handler's name and
        router landed on it — so the outer update reported itself as handled by
        ``on_error`` in a router it never touched.
        """

        @dp.message(Command("outer"))
        async def on_outer(message):
            await env.feed(
                Update(
                    update_id=9002,
                    callback_query=CallbackQuery(
                        id="q-2",
                        from_user=message.from_user,
                        chat_instance="ci",
                        data="boom",
                    ),
                ),
            )
            return "outer"

        @dp.callback_query()
        async def explode(query):
            msg = "inner exploded"
            raise RuntimeError(msg)

        errors = Router(name="errors")

        @errors.error()
        async def on_error(event):
            return "swallowed"

        dp.include_router(errors)

        await env.user(blueprint.users[0]).send("/outer")

        outer = next(record for record in env.routes if record.update_id != 9002)
        assert "on_outer" in outer.handler
        assert "on_error" not in outer.handler
        assert outer.router != "errors"

        inner = next(record for record in env.routes if record.update_id == 9002)
        assert "explode" in inner.handler
        assert isinstance(inner.exception, RuntimeError)

    def test_the_error_observer_gets_no_middleware(self, blueprint, dp):
        before = len(dp.error.middleware)

        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            assert len(dp.error.middleware) == before
        finally:
            environment.dispose_sync()


class TestTriggerScope:
    """
    One thing the test did is the unit, and one thing the test did is often several updates.

    ``member.join()`` delivers a ``chat_member`` transition *and* the group's own
    ``new_chat_members`` service message. ``last_route`` described the second one, so a bot
    that handled the first and ignored the second failed
    ``assert_handled_by("on_user_joined")`` — the assertion was right and the toolkit was
    wrong.
    """

    async def test_join_reports_the_handler_that_claimed_the_membership_update(
        self,
        env,
        dp,
        blueprint,
    ):
        @dp.chat_member()
        async def on_user_joined(event):
            return "welcomed"

        member = env.user(blueprint.users[0]).in_(blueprint.chats[1])

        await member.join()

        env.assert_handled_by("on_user_joined")
        assert env.last_route.handled is True
        assert env.last_route.event_type == "chat_member"
        # Both updates are in the scope, so the diagnosis is complete rather than merely
        # convenient.
        assert len(env.routes) == 2
        assert {record.event_type for record in env.routes} == {"chat_member", "message"}

    async def test_the_service_message_handler_is_found_too(self, env, dp, blueprint):
        """Either update claiming the handler is the bot doing the right thing."""

        @dp.message(F.new_chat_members)
        async def on_user_joined(message):
            return "welcomed"

        member = env.user(blueprint.users[0]).in_(blueprint.chats[1])

        await member.join()

        env.assert_handled_by("on_user_joined")
        assert env.last_route.event_type == "message"

    async def test_a_trigger_nothing_handled_still_says_so(self, env, blueprint):
        """The false negative must not be traded for a false positive."""
        member = env.user(blueprint.users[0]).in_(blueprint.chats[1])

        await member.join()

        assert env.last_route.handled is False
        assert all(not record.handled for record in env.routes)
        with pytest.raises(AssertionError, match="NOT handled"):
            env.assert_handled_by("on_user_joined")

    async def test_the_failure_dumps_every_update_of_the_trigger(self, env, dp, blueprint):
        @dp.chat_member()
        async def on_membership(event):
            return "seen"

        member = env.user(blueprint.users[0]).in_(blueprint.chats[1])

        await member.join()

        with pytest.raises(AssertionError) as failure:
            env.assert_handled_by("on_user_joined")
        message = str(failure.value)
        assert "its 2 update(s) went here" in message
        assert "chat_member" in message
        assert "on_membership" in message

    async def test_the_next_trigger_replaces_the_scope(self, env, dp, blueprint):
        @dp.chat_member()
        async def on_membership(event):
            return "seen"

        member = env.user(blueprint.users[0]).in_(blueprint.chats[1])
        await member.join()
        assert len(env.routes) == 2

        await env.user(blueprint.users[0]).send("plain")

        assert len(env.routes) == 1
        assert env.last_route.handled is False

    async def test_an_explicit_block_groups_hand_written_helpers(self, env, dp, blueprint):
        """The scope is public, because a test's own helper feeds several updates too."""

        @dp.message(Command("deal"))
        async def on_deal(message):
            return "dealt"

        alice = env.user(blueprint.users[0])

        with env.trigger():
            await alice.send("/deal")
            await alice.send("small talk")

        assert len(env.routes) == 2
        env.assert_handled_by("on_deal")
        assert env.last_route.handled is True

    async def test_nesting_a_block_does_not_close_the_outer_one(self, env, dp, blueprint):
        @dp.message(Command("deal"))
        async def on_deal(message):
            return "dealt"

        alice = env.user(blueprint.users[0])

        with env.trigger():
            await alice.send("/deal")
            with env.trigger():
                await alice.send("small talk")
            await alice.send("more small talk")

        assert len(env.routes) == 3
        env.assert_handled_by("on_deal")
