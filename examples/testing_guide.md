# Testing aiogram 3.x Bots — Practical Guide

> This guide provides practical examples for writing tests for your aiogram 3.x bots.
> Based on patterns from aiogram's own test suite.

## Quick Start

### Using MockedBot from aiogram test suite

```python
# tests/test_mybot.py
import pytest
from aiogram import Bot, Dispatcher, types
from tests.mocked_bot import MockedBot  # Clone aiogram and link to use

@pytest.fixture
def bot():
    return MockedBot()

@pytest.fixture
def dp():
    return Dispatcher()
```

## Testing Message Handlers

### Simple Echo Handler

```python
async def test_echo_handler(dp, bot):
    @dp.message()
    async def echo(message: types.Message):
        await message.answer(message.text)

    bot.add_result_for(
        method=types.Update,
        ok=True,
        result=types.Update(
            update_id=1,
            message=types.Message(
                message_id=1,
                date=0,
                chat=types.Chat(id=1, type="private"),
                from_user=types.User(id=1, is_bot=False, first_name="Test"),
                text="Hello!",
            ),
        ),
    )

    # Feed update and check response
    response = await dp.feed_update(bot, types.Update(update_id=1, message=...))
    assert response is not None
```

## Testing FSM (Finite State Machine)

### State Transitions with MemoryStorage

```python
from aiogram import Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_email = State()

@pytest.fixture
def storage():
    return MemoryStorage()

async def test_registration_flow(dp, bot, storage):
    dp FSMStorage(storage)

    @dp.message(commands=["register"])
    async def cmd_register(message: types.Message, state: FSMContext):
        await state.set_state(RegistrationStates.waiting_for_name)
        await message.answer("Enter your name:")

    @dp.message(state=RegistrationStates.waiting_for_name)
    async def process_name(message: types.Message, state: FSMContext):
        await state.update_data(name=message.text)
        await state.set_state(RegistrationStates.waiting_for_email)
        await message.answer("Enter your email:")

    # Test: send /register command
    message = types.Message(
        message_id=1,
        date=0,
        chat=types.Chat(id=1, type="private"),
        from_user=types.User(id=1, is_bot=False, first_name="Test"),
        text="/register",
    )

    await dp.feed_update(bot, message)

    # Verify state
    state_data = await storage.get_data(bot=bot, user_id=1)
    assert state_data.get("state") == RegistrationStates.waiting_for_name
```

## Testing Middleware

```python
class ThrottlingMiddleware:
    def __init__(self, rate_limit: int = 2):
        self.rate_limit = rate_limit
        self.users = {}

    async def __call__(self, message: types.Message, next_handler):
        user_id = message.from_user.id
        if user_id not in self.users:
            self.users[user_id] = 0

        if self.users[user_id] >= self.rate_limit:
            await message.answer("Slow down!")
            return

        self.users[user_id] += 1
        await next_handler()

async def test_throttling_middleware(dp, bot):
    dp.message.middleware(ThrottlingMiddleware(rate_limit=2))

    @dp.message()
    async def handler(message: types.Message):
        await message.answer("OK")

    # Third message should be blocked
    for i in range(3):
        msg = types.Message(
            message_id=i,
            date=0,
            chat=types.Chat(id=1, type="private"),
            from_user=types.User(id=1, is_bot=False, first_name="Test"),
            text="test",
        )
        result = await dp.feed_update(bot, msg)
```

## Mocking Bot API Responses

```python
from aiogram.methods import SendMessage

async def test_send_welcome_message(dp, bot):
    bot.add_result_for(
        method=SendMessage,
        ok=True,
        result=types.Message(
            message_id=123,
            date=0,
            chat=types.Chat(id=1, type="private"),
            from_user=types.User(id=111, is_bot=True, first_name="Bot"),
            text="Welcome!",
        ),
    )

    @dp.message(commands=["start"])
    async def cmd_start(message: types.Message):
        await message.answer("Welcome!")

    message = types.Message(
        message_id=1,
        date=0,
        chat=types.Chat(id=1, type="private"),
        from_user=types.User(id=1, is_bot=False, first_name="Test"),
        text="/start",
    )

    await dp.feed_update(bot, message)
    
    # Check request was made
    request = bot.get_request()
    assert isinstance(request, SendMessage)
    assert request.text == "Welcome!"
```

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=aiogram --cov-report=html

# Run only dispatcher tests
pytest tests/test_dispatcher/ -v

# Run with Redis/Mongo tests (if available)
pytest tests/ --redis=redis://localhost --mongo=mongodb://localhost
```

## Key Patterns from aiogram Test Suite

1. **Use `MockedBot`** from `tests/mocked_bot.py` — provides `add_result_for()` method
2. **Use fixtures** from `tests/conftest.py` — pre-configured storage, bot, dispatcher
3. **Test with real FSM** — `MemoryStorage` is fast and doesn't need external services
4. **Mock API responses** — queue expected responses in MockedBot.session
5. **Check requests** — use `bot.get_request()` to verify what bot sent to API

## Related Resources

- [aiogram test suite](https://github.com/aiogram/aiogram/tree/dev-3.x/tests)
- [pytest-asyncio docs](https://pytest-asyncio.readthedocs.io/)
- [aiogram documentation](https://docs.aiogram.dev/)
