"""
`env.last_route` — where the update actually went.

The reported pain: an update that dies in a middleware or lands in a catch-all handler
comes back from ``send()`` as somebody else's return value, and the test fails minutes
later as a ``wait_for`` timeout with nothing to say about why. These tests pin down what
the record knows and, just as importantly, that it survives a bot which swallows its own
exceptions.
"""

import pytest

from aiogram import BaseMiddleware, Router
from aiogram.filters import Command
from aiogram.test import BotTestEnvironment
from aiogram.types import Update


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
        assert "Expected the last update to be handled by 'on_start'" in str(failure.value)

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
