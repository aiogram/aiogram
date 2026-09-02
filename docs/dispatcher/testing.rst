=======
Testing
=======

Handlers are regular async callables, so the simplest tests call them directly with a
mocked event object and mocked dependencies.  Use this style for business logic that
is already inside the handler.

.. code-block:: python

    from unittest.mock import AsyncMock

    import pytest


    async def echo_handler(message):
        await message.answer(message.text)


    @pytest.mark.asyncio
    async def test_echo_handler():
        message = AsyncMock(text="Hello")

        await echo_handler(message)

        message.answer.assert_awaited_once_with("Hello")

For filters, routers, middlewares, and dependency injection, feed an update to a
:class:`aiogram.Dispatcher`.  This exercises aiogram's routing pipeline without
starting long polling or making requests to Telegram.

.. code-block:: python

    import time

    import pytest

    from aiogram import Bot, Dispatcher, F


    @pytest.mark.asyncio
    async def test_dispatcher_routes_message():
        bot = Bot("42:TEST")
        dp = Dispatcher()

        @dp.message(F.text == "ping")
        async def ping_handler():
            return "pong"

        result = await dp.feed_raw_update(
            bot=bot,
            update={
                "update_id": 1,
                "message": {
                    "message_id": 1,
                    "date": int(time.time()),
                    "text": "ping",
                    "chat": {"id": 42, "type": "private"},
                    "from": {"id": 42, "is_bot": False, "first_name": "Test"},
                },
            },
        )

        assert result == "pong"

You can pass handler dependencies in the same call. They are available to filters,
middlewares, and handlers through aiogram's normal dependency injection mechanism.

.. code-block:: python

    import time

    import pytest

    from aiogram import Bot, Dispatcher


    class Repository:
        async def get_name(self, user_id: int) -> str:
            return "Alice"


    @pytest.mark.asyncio
    async def test_handler_with_dependency():
        bot = Bot("42:TEST")
        dp = Dispatcher()

        @dp.message()
        async def profile_handler(repository: Repository):
            return await repository.get_name(user_id=42)

        result = await dp.feed_raw_update(
            bot=bot,
            update={
                "update_id": 1,
                "message": {
                    "message_id": 1,
                    "date": int(time.time()),
                    "text": "/profile",
                    "chat": {"id": 42, "type": "private"},
                    "from": {"id": 42, "is_bot": False, "first_name": "Test"},
                },
            },
            repository=Repository(),
        )

        assert result == "Alice"

If a handler calls Telegram API methods, keep the test focused by mocking the event
object or by using the project's own test helpers.  Avoid real bot tokens and real
network requests in unit tests.
