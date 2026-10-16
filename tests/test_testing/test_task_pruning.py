import asyncio
import contextlib
import gc
import weakref

import pytest

from aiogram import Dispatcher
from aiogram.test import BackgroundTaskError, BotTestEnvironment, DrainedTaskError


@pytest.fixture
async def started(env, alice):
    """An environment that has run, so it tracks new tasks."""
    await alice.send("hello")
    return env


def held(env):
    """
    Everything the environment keeps hold of, besides the test's own task.

    A failure the bot retrieved is let go at the next sweep, which any task ending, a drain
    or a wait makes, so the sweep is made here for a test that asks in between.
    """
    env._release_retrieved_failures()
    return (env._spawned_tasks | env._failed_tasks) - {asyncio.current_task()}


async def ticks(count=3):
    for _ in range(count):
        await asyncio.sleep(0)


async def fail(message="boom"):
    raise KeyError(message)


class TestFinishedTasksAreLetGo:
    async def test_a_finished_task_is_not_held(self, started):
        async def work():
            return 1

        for _ in range(200):
            asyncio.create_task(work())
        await ticks()

        assert held(started) == set()

    async def test_nothing_pins_a_finished_task_in_memory(self, started):
        async def work():
            return 1

        task = asyncio.create_task(work())
        reference = weakref.ref(task)
        await task
        await ticks()
        del task
        gc.collect()

        assert reference() is None

    async def test_a_cancelled_task_is_not_held(self, started):
        task = asyncio.create_task(asyncio.sleep(3600))
        await ticks()
        assert task in held(started)

        task.cancel()
        await ticks()

        assert held(started) == set()

    async def test_a_running_task_is_held_and_drained(self, started):
        tasks = [asyncio.create_task(asyncio.sleep(3600)) for _ in range(5)]
        await ticks()

        assert set(tasks) <= held(started)
        assert await started.drain() == 5
        await ticks()
        assert held(started) == set()

    async def test_waiting_still_counts_what_it_waited_for(self, started):
        async def work():
            await asyncio.sleep(0.01)

        tasks = [asyncio.create_task(work()) for _ in range(4)]
        quick = asyncio.create_task(asyncio.sleep(0))
        await quick

        assert await started.wait_for_tasks() == 4
        assert all(task.done() for task in tasks)
        assert held(started) == set()


class TestAFailureIsStillReported:
    async def test_wait_for_tasks_reports_a_failure_among_many_finished_tasks(self, started):
        async def work():
            return 1

        for _ in range(50):
            asyncio.create_task(work())
        failing = asyncio.create_task(fail("night timer"))
        for _ in range(50):
            asyncio.create_task(work())
        await ticks()

        assert held(started) == {failing}
        with pytest.raises(BackgroundTaskError, match="night timer") as failure:
            await started.wait_for_tasks()

        assert isinstance(failure.value.__cause__, KeyError)
        await ticks()
        assert held(started) == set()

    async def test_drain_reports_it_too(self, started):
        failing = asyncio.create_task(fail("night timer"))
        await ticks()
        assert failing.done()

        with pytest.raises(DrainedTaskError, match="night timer"):
            await started.drain()

        await ticks()
        assert held(started) == set()

    async def test_a_failure_the_bot_retrieved_is_not_one(self, started):
        failing = asyncio.create_task(fail())
        with pytest.raises(KeyError):
            await failing
        await ticks()

        assert held(started) == set()
        assert await started.wait_for_tasks() == 0
        assert await started.drain() == 0

    async def test_a_failure_retrieved_late_is_not_reported(self, started):
        failing = asyncio.create_task(fail())
        await ticks()
        assert held(started) == {failing}

        with pytest.raises(KeyError):
            await failing

        assert await started.wait_for_tasks() == 0
        assert await started.drain() == 0
        assert held(started) == set()

    async def test_a_failure_retrieved_then_forgotten_is_not_reported(self, started):
        async def handle():
            with contextlib.suppress(KeyError):
                await asyncio.create_task(fail())

        await asyncio.create_task(handle())
        await ticks()
        gc.collect()

        assert await started.wait_for_tasks() == 0
        assert held(started) == set()

    async def test_a_failure_during_a_wait_is_kept_for_the_report(self, started):
        async def late():
            await asyncio.sleep(0.01)
            raise KeyError("late")

        asyncio.create_task(late())

        with pytest.raises(BackgroundTaskError, match="late"):
            await started.wait_for_tasks()


class TestADisposedEnvironmentHoldsNothing:
    async def test_tasks_created_after_disposal_are_not_held(self, blueprint):
        outer = BotTestEnvironment(blueprint=blueprint, dispatcher=Dispatcher())
        await outer.user(blueprint.users[0]).send("hi")
        inner = BotTestEnvironment(blueprint=blueprint, dispatcher=Dispatcher())
        await inner.user(blueprint.users[0]).send("hi")
        outer.dispose_sync()

        # The inner environment has the loop's factory, and the
        # outer's is under it.
        failing = asyncio.create_task(fail())
        sleeping = asyncio.create_task(asyncio.sleep(3600))
        await ticks()

        try:
            assert held(outer) == set()
            assert {failing, sleeping} <= held(inner)
        finally:
            sleeping.cancel()
            with pytest.raises(KeyError):
                await failing
            inner.dispose_sync()
