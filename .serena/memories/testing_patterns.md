# Testing Patterns

## Framework
- pytest with async support
- No `pytest-asyncio` explicit marks needed (configured globally in pyproject.toml)
- `MockedBot` (tests/mocked_bot.py) — use for all bot method tests, no real HTTP

## MockedBot pattern
```python
from tests.mocked_bot import MockedBot
from aiogram.methods import SendMessage
from aiogram.types import Message, Chat
import datetime

class TestSendMessage:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendMessage,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                text="test",
                chat=Chat(id=42, type="private"),
            ),
        )
        response: Message = await bot.send_message(chat_id=42, text="test")
        bot.get_request()
        assert response == prepare_result.result
```

## Test structure
- Class per type/method: `class TestSendMessage:`
- One test per scenario: `async def test_<scenario>(self, ...)`
- `bot` fixture comes from `tests/conftest.py`

## Integration tests
- Redis: `uv run pytest --redis redis://localhost:6379/0 tests`
- MongoDB: `uv run pytest --mongo mongodb://mongo:mongo@localhost:27017 tests`
- Only run these when Redis/Mongo storage code is affected

## What NOT to do
- Do not mock the database/storage in FSM tests — use real backends or memory storage
- Do not introduce new test dependencies for small tests
- Keep test style consistent with existing suite
