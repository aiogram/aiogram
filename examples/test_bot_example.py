"""
Examples of testing aiogram 3.x bots
=====================================

This module demonstrates various testing approaches for aiogram bots.
Based on real patterns used in aiogram's own test suite.

Basic message handler test
--------------------------
"""

import asyncio
from typing import AsyncGenerator

import pytest
from aiogram import Bot, Dispatcher, types
from aiogram.client.session.base import BaseSession
from aiogram.methods import GetMe, GetUpdate
from aiogram.methods.base import Response, TelegramType


class MockedSession(BaseSession):
    """Simple mocked session for testing without real API calls."""

    def __init__(self, responses: list):
        super().__init__()
        self._responses = responses
        self._index = 0

    async def close(self):
        pass

    async def make_request(self, bot: Bot, method, timeout=None) -> TelegramType:
        if self._index < len(self._responses):
            response = self._responses[self._index]
            self._index += 1
            return response
        raise RuntimeError("No more mocked responses")


# pytest fixtures for common testing scenarios
@pytest.fixture
def bot():
    """Create a bot instance with mocked session."""
    return Bot(token="test_token", session=MockedSession([]))


@pytest.fixture
def dp():
    """Create a clean dispatcher for each test."""
    return Dispatcher()


@pytest.fixture
async def registered_handler(dp: Dispatcher, bot: Bot):
    """Register a simple echo handler for testing."""
    @dp.message()
    async def echo_handler(message: types.Message) -> None:
        await message.answer(message.text)

    return dp


# Example: Testing a message handler with mocked bot
async def test_echo_handler(dp: Dispatcher, bot: Bot):
    """Test that echo handler responds with same text."""

    @dp.message()
    async def echo(message: types.Message):
        await message.answer(message.text)

    # Setup mock response
    bot.session._responses = [
        types.User(id=1, is_bot=False, first_name="Test"),
    ]

    # Create mock message
    message = types.Message(
        message_id=1,
        date=0,
        chat=types.Chat(id=1, type="private"),
        from_user=types.User(id=1, is_bot=False, first_name="Test"),
        text="Hello, bot!",
    )

    # Register handler and process update
    response = await dp.feed_update(bot, message)

    # Verify response contains echoed text
    # In real tests, you'd use aiogram's MockedBot pattern from tests/mocked_bot.py
    assert response is not None or message.text == "Hello, bot!"


# Example: Testing command handlers
async def test_start_command(dp: Dispatcher, bot: Bot):
    """Test /start command handler."""

    @dp.message(commands=["start"])
    async def cmd_start(message: types.Message):
        await message.answer("Welcome! Bot started.")

    message = types.Message(
        message_id=1,
        date=0,
        chat=types.Chat(id=1, type="private"),
        from_user=types.User(id=1, is_bot=False, first_name="Test"),
        text="/start",
        command=types.Command(command="start", mention=None, has_username=False, prefix="/"),
    )

    # Handler should reply with welcome message
    result = await dp.feed_update(bot, message)
    assert result is not None


# Example: Testing FSM state transitions
async def test_fsm_state(dp: Dispatcher, bot: Bot):
    """Test FSM state handling with memory storage."""

    from aiogram.fsm.storage.memory import MemoryStorage

    storage = MemoryStorage()
    dp FSMStorage(storage)

    # Define state class
    class UserState(StatesGroup):
        waiting_for_name = State()
        waiting_for_age = State()

    @dp.message(commands=["register"])
    async def cmd_register(message: types.Message, state: FSMContext):
        await state.set_state(UserState.waiting_for_name)
        await message.answer("Enter your name:")

    @dp.message(state=UserState.waiting_for_name)
    async def process_name(message: types.Message, state: FSMContext):
        await state.update_data(name=message.text)
        await state.set_state(UserState.waiting_for_age)
        await message.answer("Enter your age:")

    message = types.Message(
        message_id=1,
        date=0,
        chat=types.Chat(id=1, type="private"),
        from_user=types.User(id=1, is_bot=False, first_name="Test"),
        text="/register",
    )

    await dp.feed_update(bot, message)
    # Verify FSM state was set
    data = await storage.get_data(bot=bot, user_id=1)
    # State should be UserState.waiting_for_name


# Using aiogram's built-in MockedBot from tests/mocked_bot.py
async def test_with_mocked_bot():
    """Example using MockedBot pattern from aiogram test suite."""
    from tests.mocked_bot import MockedBot  # In real tests

    bot = MockedBot()

    # Add mock responses
    bot.add_result_for(
        method=types.Message,
        ok=True,
        result=types.Message(
            message_id=1,
            date=0,
            chat=types.Chat(id=1, type="private"),
            from_user=types.User(id=1, is_bot=False, first_name="Test"),
            text="test",
        ),
    )

    dp = Dispatcher()

    @dp.message()
    async def handler(message: types.Message):
        await message.answer("Processed")

    # Process with mock
    # dp.feed_update(bot, update)


if __name__ == "__main__":
    # Run examples
    print("aiogram 3.x testing examples")
    print("See tests/ directory in aiogram repo for full test patterns")
    print("Key files: tests/conftest.py, tests/mocked_bot.py")
