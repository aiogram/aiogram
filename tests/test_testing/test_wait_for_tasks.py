"""
``await env.wait_for_tasks()``: wait for the bot's background work
to finish, where ``drain()`` would cancel it.
"""

import asyncio

import pytest

from aiogram import F
from aiogram.test import (
    BackgroundTaskError,
    BotTestEnvironment,
    DrainedTaskError,
    WaitTimeoutError,
)


class TestWaitForTasks:
    async def test_a_broadcast_runs_to_its_end(self, env, dp, alice, private):
        @dp.message(F.text == "/results")
        async def results(message, bot):
            async def broadcast():
                for line in ("Town wins", "Mafia: Bob"):
                    await asyncio.sleep(0.01)
                    await bot.send_message(message.chat.id, line)

            asyncio.create_task(broadcast())

        await alice.send("/results")

        assert await env.wait_for_tasks() == 1
        assert [m.text for m in private.messages[-2:]] == ["Town wins", "Mafia: Bob"]

    async def test_nothing_is_cancelled(self, env, alice):
        await alice.send("hi")
        task = asyncio.create_task(asyncio.sleep(0.01))

        assert await env.wait_for_tasks() == 1
        assert task.done()
        assert not task.cancelled()

    async def test_tasks_spawned_while_waiting_are_waited_for(self, env, alice):
        await alice.send("hi")
        finished = []

        async def child():
            await asyncio.sleep(0.01)
            finished.append("child")

        async def parent():
            await asyncio.sleep(0.01)
            asyncio.create_task(child())
            finished.append("parent")

        asyncio.create_task(parent())

        assert await env.wait_for_tasks() == 2
        assert finished == ["parent", "child"]

    async def test_no_tasks_is_free(self, env, alice):
        await alice.send("hi")

        assert await env.wait_for_tasks() == 0

    async def test_an_environment_that_never_ran_waits_for_nothing(self, env):
        outsider = asyncio.create_task(asyncio.sleep(3600))
        await asyncio.sleep(0)

        try:
            assert await env.wait_for_tasks(timeout=0.01) == 0
            assert not outsider.done()
        finally:
            outsider.cancel()

    async def test_tasks_alive_at_the_first_feed_are_not_the_bots(self, env, alice):
        outsider = asyncio.create_task(asyncio.sleep(3600))
        await asyncio.sleep(0)
        await alice.send("hi")

        try:
            assert await env.wait_for_tasks(timeout=0.01) == 0
        finally:
            outsider.cancel()

    async def test_a_wait_from_a_child_task_does_not_wait_for_the_test(self, env, alice):
        """The test's own task awaits the child, so waiting for it would hang."""
        await alice.send("hi")
        task = asyncio.create_task(asyncio.sleep(0.01))

        [waited] = await asyncio.gather(env.wait_for_tasks(timeout=1.0))

        assert waited == 1
        assert task.done()

    async def test_a_failed_task_is_raised(self, env, alice):
        await alice.send("hi")

        async def explode():
            await asyncio.sleep(0.01)
            msg = "no such player"
            raise KeyError(msg)

        task = asyncio.create_task(explode())

        with pytest.raises(BackgroundTaskError, match="ended with an exception") as failure:
            await env.wait_for_tasks()

        assert not isinstance(failure.value, DrainedTaskError)
        assert task.get_name() in str(failure.value)
        assert "KeyError" in str(failure.value)
        assert isinstance(failure.value.__cause__, KeyError)
        # Retrieved, so a later drain does not report it again.
        assert await env.drain() == 0

    async def test_a_task_that_failed_before_the_wait_is_raised(self, env, alice):
        await alice.send("hi")

        async def explode():
            msg = "boom"
            raise ValueError(msg)

        asyncio.create_task(explode())
        await asyncio.sleep(0)

        with pytest.raises(BackgroundTaskError, match="ValueError: boom"):
            await env.wait_for_tasks()

    async def test_a_retrieved_failure_is_the_bots_own(self, env, alice):
        await alice.send("hi")

        async def explode():
            msg = "handled"
            raise ValueError(msg)

        task = asyncio.create_task(explode())
        with pytest.raises(ValueError, match="handled"):
            await task

        assert await env.wait_for_tasks() == 0

    async def test_a_timeout_names_what_still_runs_and_cancels_nothing(self, env, alice):
        await alice.send("hi")

        async def night_timer():
            await asyncio.sleep(3600)

        task = asyncio.create_task(night_timer(), name="night")

        try:
            with pytest.raises(WaitTimeoutError) as failure:
                await env.wait_for_tasks(timeout=0.02)
            message = str(failure.value)
            assert "1 still running" in message
            assert "night (TestWaitForTasks." in message
            assert "night_timer)" in message
            assert "Nothing was cancelled" in message
            assert failure.value.__cause__ is None
            assert not task.done()
        finally:
            task.cancel()

    async def test_a_timeout_also_reports_a_failure(self, env, alice):
        await alice.send("hi")

        async def explode():
            msg = "broadcast failed"
            raise RuntimeError(msg)

        stuck = asyncio.create_task(asyncio.sleep(3600))
        asyncio.create_task(explode())
        await asyncio.sleep(0)

        try:
            with pytest.raises(WaitTimeoutError, match="still running") as failure:
                await env.wait_for_tasks(timeout=0.02)
            assert "RuntimeError: broadcast failed" in str(failure.value)
            assert isinstance(failure.value.__cause__, RuntimeError)
        finally:
            stuck.cancel()

    async def test_the_timeout_defaults_to_the_environments(self, blueprint, dp):
        environment = BotTestEnvironment(
            blueprint=blueprint,
            dispatcher=dp,
            default_wait_timeout=0.02,
        )
        try:
            await environment.user(blueprint.users[0]).send("hi")
            stuck = asyncio.create_task(asyncio.sleep(3600))
            try:
                with pytest.raises(WaitTimeoutError, match="after 0.02s"):
                    await environment.wait_for_tasks()
            finally:
                stuck.cancel()
        finally:
            await environment.dispose()

    async def test_drain_from_a_child_task_spares_the_test(self, env, alice):
        """The task that first ran the environment is never the bot's."""
        await alice.send("hi")
        leaked = asyncio.create_task(asyncio.sleep(3600))
        await asyncio.sleep(0)

        [drained] = await asyncio.gather(env.drain())

        assert drained == 1
        assert leaked.cancelled()
