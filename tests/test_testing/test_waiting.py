import asyncio

import pytest

from aiogram.test import WaitTimeoutError
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
