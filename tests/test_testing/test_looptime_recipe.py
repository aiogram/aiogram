"""
Verification for the ``looptime`` fake-clock recipe documented in
``docs/dispatcher/testing.rst`` ("Bots with background tasks").

``looptime`` is not a dependency of aiogram or of this suite -- adopting it is a
per-project decision, made only where a bot's background tasks make real-time waits
too slow. This module exists so that recipe does not silently rot: it skips cleanly
wherever ``looptime`` is absent (CI included) and exercises the documented example for
real wherever it is installed.
"""

import asyncio
import time

import pytest

from aiogram import Bot, Router
from aiogram.test import WaitTimeoutError, detach_router

pytest.importorskip("looptime")

router = Router()


@router.message()
async def start_night(message, bot: Bot) -> None:
    asyncio.create_task(run_night_phase(bot, message.chat.id))


async def run_night_phase(bot: Bot, chat_id: int) -> None:
    await asyncio.sleep(15)  # stands in for a game engine's own hardcoded sleep
    await bot.send_message(chat_id=chat_id, text="Night falls.")


@pytest.mark.looptime
class TestLooptimeRecipe:
    async def test_background_sleep_resolves_in_virtual_time(self, env, dp, alice, private):
        dp.include_router(detach_router(router))
        wall_started = time.monotonic()

        await alice.send("/start")
        message = await private.wait_for_message(
            lambda m: m.text == "Night falls.", timeout=20.0, interval=0.5
        )

        wall_elapsed = time.monotonic() - wall_started
        assert message.text == "Night falls."
        # The documented expectation: milliseconds of real time for a 15s virtual sleep.
        assert wall_elapsed < 1.0

    async def test_a_wait_that_should_time_out_still_does(self, env):
        """poll_until's deadline is loop.time()-based, so it must compose with the
        virtual clock: a predicate that never turns true still raises on time, in
        real milliseconds, however large ``timeout`` is in virtual seconds."""
        wall_started = time.monotonic()

        with pytest.raises(WaitTimeoutError):
            await env.wait_for(lambda: False, timeout=10.0, interval=0.5, description="never")

        wall_elapsed = time.monotonic() - wall_started
        assert wall_elapsed < 1.0

    async def test_the_interval_sleep_advances_virtual_time(self, env, dp, alice, private):
        """The poller's own interval sleep must burn *virtual* loop time rather than
        being short-circuited to zero -- otherwise a wait could return before the
        thing it is waiting for has actually happened, virtual-time-wise."""
        dp.include_router(detach_router(router))
        loop = asyncio.get_running_loop()
        started = loop.time()

        await alice.send("/start")
        await private.wait_for_message(
            lambda m: m.text == "Night falls.", timeout=20.0, interval=0.1
        )

        assert loop.time() - started >= 14.9
