Testing your bot (pytest)
=========================

This guide shows how to test your handlers **without using the real Telegram API**.
We will use `pytest` and `pytest-asyncio`.

Installation::

   pip install -U pytest pytest-asyncio

Simple echo handler
-------------------

**Handler:**

.. code-block:: python

   # app/bot.py
   from aiogram.types import Message

   async def echo_handler(message: Message):
       await message.answer(message.text)

**Test:**

.. code-block:: python

   # tests/test_echo.py
   import pytest
   from app.bot import echo_handler

   @pytest.mark.asyncio
   async def test_echo_handler():
       sent = []

       class DummyMessage:
           def __init__(self, text):
               self.text = text
           async def answer(self, text):
               sent.append(text)

       msg = DummyMessage("hello")
       await echo_handler(msg)

       assert sent == ["hello"]

Callback query example
----------------------

**Handler:**

.. code-block:: python

   # app/callbacks.py
   from aiogram.types import CallbackQuery

   async def ping_pong(cb: CallbackQuery):
       if cb.data == "ping":
           await cb.message.edit_text("pong")
           await cb.answer()

**Test:**

.. code-block:: python

   # tests/test_callbacks.py
   import pytest
   from app.callbacks import ping_pong

   @pytest.mark.asyncio
   async def test_ping_pong():
       calls = {"edited": None, "answered": False}

       class DummyMsg:
           async def edit_text(self, text):
               calls["edited"] = text

       class DummyCb:
           data = "ping"
           message = DummyMsg()
           async def answer(self):
               calls["answered"] = True

       cb = DummyCb()
       await ping_pong(cb)

       assert calls["edited"] == "pong"
       assert calls["answered"] is True
