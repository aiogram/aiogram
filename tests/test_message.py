from asyncio import BaseEventLoop

import pytest

from aiogram import Bot, types
from . import FakeTelegram, TOKEN

pytestmark = pytest.mark.asyncio


@pytest.yield_fixture()
async def bot(event_loop):
    """ Bot fixture """
    _bot = Bot(TOKEN, loop=event_loop, parse_mode=types.ParseMode.HTML)
    yield _bot
    await _bot.close()


@pytest.yield_fixture()
async def message(bot, event_loop):
    """
    Message fixture
    :param bot: Telegram bot fixture
    :type bot: Bot
    :param event_loop: asyncio event loop
    :type event_loop: BaseEventLoop
    """
    from .types.dataset import MESSAGE
    msg = types.Message(**MESSAGE)

    async with FakeTelegram(message_data=MESSAGE, loop=event_loop):
        _message = await bot.send_message(chat_id=msg.chat.id, text=msg.text)

    yield _message


class TestMiscCases:
    async def test_calling_bot_not_from_context(self, message):
        """
        Calling any helper method without bot instance in context.

        :param message: message fixture
        :type message: types.Message
        :return: RuntimeError with reason and help
        """
        with pytest.raises(RuntimeError):
            await message.edit_text('test_calling_bot_not_from_context')
