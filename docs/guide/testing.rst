Testing your bot (pytest)
=========================

This guide shows how to test your handlers **without using the real Telegram API**.
We will use `pytest` and `pytest-asyncio`.

Configure pytest once (no need to mark every test):

.. code-block:: toml

   # pyproject.toml
   [tool.pytest.ini_options]
   asyncio_mode = "auto"


Example: testing a simple handler:

.. code-block:: python

   from unittest.mock import AsyncMock
   from aiogram import Router, F
   from aiogram.types import Message

   router = Router()

   @router.message(F.text == "/start")
   async def start(message: Message):
       await message.answer("Hello!")

   async def test_start_handler():
       # Bot and message stubs
       bot = AsyncMock()
       msg = Message(
           message_id=1,
           date=None,
           chat={"id": 1, "type": "private"},
           text="/start",
       )

       # Emulate answer() call
       message = AsyncMock(spec=Message)
       message.answer = AsyncMock()

       # Run handler
       await start(message)

       # Assert: answer called with expected payload
       message.answer.assert_awaited_once_with("Hello!")


Mocking Bot API
===============

To assert Bot API calls, patch the method and verify arguments:

.. code-block:: python

   from unittest.mock import AsyncMock, patch
   from aiogram import Bot

   async def test_bot_send_message():
       bot = Bot("42:TEST", parse_mode=None)

       with patch.object(Bot, "send_message", new_callable=AsyncMock) as send_msg:
           await bot.send_message(123, "ping")
           send_msg.assert_awaited_once_with(123, "ping")

See also
--------

- :ref:`aiogram.utils.magic_filter`
- :ref:`pytest documentation <https://docs.pytest.org/en/latest/>`
